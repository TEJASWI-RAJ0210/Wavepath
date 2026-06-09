import os
import redis
from dotenv import load_dotenv

load_dotenv()

r = redis.from_url(
    os.getenv('REDIS_URL', 'redis://localhost:6379'),
    ssl_cert_reqs=None  # required for Upstash TLS
)

DELTA = {
    'like':     +0.2,
    'replay':   +0.3,
    'complete': +0.1,
    'skip':     -0.3,
}


def update_song_score(track_id: str, action: str) -> float:
    key   = f'score:{track_id}'
    delta = DELTA.get(action, 0.0)
    try:
        current = float(r.get(key) or 1.0)
    except Exception:
        current = 1.0
    new_score = max(0.1, min(2.0, current + delta))
    r.set(key, new_score, ex=86400)
    return new_score


def get_song_score(track_id: str) -> float:
    try:
        val = r.get(f'score:{track_id}')
        return float(val) if val else 1.0
    except Exception:
        return 1.0


def rerank_with_feedback(playlist: list) -> list:
    n = len(playlist)
    for i, song in enumerate(playlist):
        pos_score           = 1.0 - (i / max(n, 1))
        fb_score            = get_song_score(song['id'])
        song['final_score'] = 0.7 * pos_score + 0.3 * fb_score
    return sorted(playlist, key=lambda s: s['final_score'], reverse=True)


if __name__ == '__main__':
    print('Testing Upstash connection...')
    r.ping()
    print('Connected to Upstash Redis')
    update_song_score('test_track_001', 'like')
    print(f'Score after like: {get_song_score("test_track_001")}')
    update_song_score('test_track_001', 'skip')
    print(f'Score after skip: {get_song_score("test_track_001")}')