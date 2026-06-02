# CREATE TABLE tracks (
#     id          TEXT PRIMARY KEY,
#     name        TEXT NOT NULL,
#     artist      TEXT NOT NULL,
#     valence     FLOAT,
#     energy      FLOAT,
#     danceability FLOAT,
#     tempo       FLOAT,
#     acousticness FLOAT,
#     instrumentalness FLOAT,
#     loudness    FLOAT,
#     preview_url TEXT,
#     album_image TEXT
# );

# CREATE TABLE user_sessions (
#     session_id  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
#     created_at  TIMESTAMP DEFAULT NOW()
# );

# CREATE TABLE user_feedback (
#     id          SERIAL PRIMARY KEY,
#     session_id  UUID REFERENCES user_sessions(session_id),
#     track_id    TEXT REFERENCES tracks(id),
#     action      TEXT CHECK (action IN ('skip','like','replay','complete')),
#     position_in_journey INT,
#     created_at  TIMESTAMP DEFAULT NOW()
# );

# Load into PostgreSQL
import psycopg2
from sqlalchemy import create_engine

engine = create_engine("postgresql://user:pass@localhost:5432/moodjourney")
df.to_sql("tracks", engine, if_exists="replace", index=False)