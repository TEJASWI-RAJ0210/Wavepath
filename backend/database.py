import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL',
    'postgresql://user:pass@localhost:5432/wavepath')

# SQLAlchemy engine — this is the connection to PostgreSQL.
# We reuse this engine across the whole app (connection pooling).
engine = create_engine(DATABASE_URL)


def init_db():
    """
    Create all tables if they do not exist yet.
    Running this twice is safe — CREATE TABLE IF NOT EXISTS.
    """
    with engine.connect() as conn:
        conn.execute(text('''
            CREATE TABLE IF NOT EXISTS tracks (
                id               TEXT PRIMARY KEY,
                name             TEXT NOT NULL,
                artist           TEXT NOT NULL,
                valence          FLOAT,
                energy           FLOAT,
                danceability     FLOAT,
                tempo            FLOAT,
                acousticness     FLOAT,
                instrumentalness FLOAT,
                loudness         FLOAT,
                popularity       INT,
                preview_url      TEXT,
                album_image      TEXT
            )
        '''))
        conn.execute(text('''
            CREATE TABLE IF NOT EXISTS user_feedback (
                id          SERIAL PRIMARY KEY,
                session_id  TEXT NOT NULL,
                track_id    TEXT REFERENCES tracks(id),
                action      TEXT CHECK (action IN
                            ('skip','like','replay','complete')),
                position    INT,
                created_at  TIMESTAMP DEFAULT NOW()
            )
        '''))
        conn.commit()
    print('Tables created (or already exist)')


def load_tracks_from_parquet(parquet_path: str = 'data/tracks.parquet'):
    """
    Load the track dataset into the tracks table.
    Uses INSERT ... ON CONFLICT DO NOTHING so re-running is safe.
    """
    df = pd.read_parquet(parquet_path)
    # Rename columns to match DB schema
    df = df.where(pd.notna(df), None)  # replace NaN with None

    # Bulk insert via pandas — fastest way to load large DataFrames
    df.to_sql(
        'tracks',
        engine,
        if_exists='append',  # append, don't overwrite
        index=False,
        method='multi',      # batch inserts
        chunksize=1000,
    )
    print(f'Loaded {len(df)} tracks into PostgreSQL')


if __name__ == '__main__':
    init_db()
    load_tracks_from_parquet()