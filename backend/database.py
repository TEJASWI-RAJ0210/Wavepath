import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

engine = create_engine(
    DATABASE_URL,
    connect_args={'sslmode': 'require'}
)


def init_db():
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
    print('NeonDB tables ready')


def load_tracks_from_parquet(parquet_path: str = 'data/tracks.parquet'):
    df = pd.read_parquet(parquet_path)
    df = df.where(pd.notna(df), None)

    schema_cols = ['id', 'name', 'artist', 'valence', 'energy',
                   'danceability', 'tempo', 'acousticness',
                   'preview_url', 'album_image']
    df = df[[c for c in schema_cols if c in df.columns]]

    df.to_sql('tracks', engine, if_exists='append',
              index=False, method='multi', chunksize=500)
    print(f'Loaded {len(df)} tracks into NeonDB')


if __name__ == '__main__':
    init_db()
    load_tracks_from_parquet()