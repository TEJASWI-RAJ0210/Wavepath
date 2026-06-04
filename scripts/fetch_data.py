import os, time
import pandas as pd
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv

# Load the credentials we saved in .env
load_dotenv()

# Authenticate with Spotify using Client Credentials flow.
# This flow is for server-to-server access — no user login needed.
# It gives us read-only access to the public catalog.
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=os.getenv('SPOTIFY_CLIENT_ID'),
    client_secret=os.getenv('SPOTIFY_CLIENT_SECRET')
))

# ─────────────────────────────────────────────────────────────
# SEED PLAYLISTS
# We need tracks spread across all four quadrants of the mood
# space (valence x energy). Picking playlists with different
# emotional tones guarantees good coverage.
# ─────────────────────────────────────────────────────────────
SEED_PLAYLISTS = [
    # Bollywood — High energy, high valence
    "37i9dQZF1DX0XUfTFmNBRM",  # Bollywood Butter
    "37i9dQZF1DXdgz8ZB7c2CP",  # Bollywood Workout
    "37i9dQZF1DX3PIPIT6lEg5",  # Hot Hits Hindi

    # Bollywood — Sad / emotional
    "37i9dQZF1DX3YSRoSdA634",  # Sad Songs Hindi
    "37i9dQZF1DWVqfgj8NZEp1",  # Bollywood Heartbreak
    "37i9dQZF1DX6mvEU1S6INL",  # Dil Se

    # Bollywood — Romantic / calm
    "37i9dQZF1DWUa8ZRTfalHk",  # Romance Hindi
    "37i9dQZF1DX0vHZ8ElGm5Y",  # Bollywood Love Songs
    "37i9dQZF1DXdSjVZSHcFNd",  # Filhaal

    # Party / Dance
    "37i9dQZF1DX1IkKyqeQGJ8",  # Bollywood Party
    "37i9dQZF1DXaB5YNbFEtaW",  # Punjabi Party
    "37i9dQZF1DX0pH2SQMRXnC",  # Bhangra Hits

    # Indie / Lo-fi Hindi
    "37i9dQZF1DX4UkKv329LNI",  # Hindi Indie
    "37i9dQZF1DWXRqgorJj26U",  # Chill Hindi

    # South Indian (Tamil, Telugu) — good for coverage
    "37i9dQZF1DX6XE7HRLM75P",  # Tamil Hits
    "37i9dQZF1DX4h89JZTS4Vi",  # Telugu Chartbusters
]


def fetch_playlist_tracks(playlist_id: str) -> list:
    """
    Fetch all track metadata from a Spotify playlist.
    Spotify paginates results (max 100 per page), so we loop
    through pages until there are no more.
    """
    results = sp.playlist_tracks(playlist_id)
    tracks = []
    while results:
        for item in results['items']:
            track = item.get('track')
            # Skip local files, podcasts, deleted tracks
            if not track or not track.get('id'):
                continue
            tracks.append({
                'id':          track['id'],
                'name':        track['name'],
                'artist':      track['artists'][0]['name'],
                'preview_url': track.get('preview_url'),
                'album_image': (
                    track['album']['images'][0]['url']
                    if track['album']['images'] else None
                ),
                'popularity':  track.get('popularity', 0),
            })
        # Follow Spotify's pagination cursor
        results = sp.next(results) if results['next'] else None
    return tracks


def fetch_audio_features(track_ids: list) -> list:
    """
    Fetch Spotify audio features for a batch of track IDs.
    The API allows max 100 IDs per call, so we chunk the list.
    We add a small sleep to stay under the rate limit (100 req/min).
    """
    features = []
    for i in range(0, len(track_ids), 100):
        batch = track_ids[i:i+100]
        result = sp.audio_features(batch)
        # Some tracks return None (unavailable in region)
        features.extend([f for f in result if f])
        time.sleep(0.5)  # be polite to the API
        print(f'  Fetched features {i+len(batch)}/{len(track_ids)}')
    return features


def build_dataset() -> pd.DataFrame:
    """
    Main pipeline: fetch tracks from all playlists, get audio
    features, merge, deduplicate, and return a clean DataFrame.
    """
    print('Step 1: Fetching tracks from seed playlists...')
    all_tracks = []
    for i, pid in enumerate(SEED_PLAYLISTS):
        try:
            tracks = fetch_playlist_tracks(pid)
            all_tracks.extend(tracks)
            print(f'  Playlist {i+1}/{len(SEED_PLAYLISTS)}: {len(tracks)} tracks')
            time.sleep(0.3)
        except Exception as e:
            print(f'  Skipped playlist {pid}: {e}')

    track_df = pd.DataFrame(all_tracks).drop_duplicates(subset='id')
    print(f'Total unique tracks: {len(track_df)}')

    print('Step 2: Fetching audio features...')
    features = fetch_audio_features(track_df['id'].tolist())
    features_df = pd.DataFrame(features)[
        ['id', 'valence', 'energy', 'danceability',
         'tempo', 'acousticness', 'instrumentalness', 'loudness']
    ]

    # Inner join — only keep tracks that have both metadata AND features
    df = track_df.merge(features_df, on='id', how='inner')
    print(f'Final dataset: {len(df)} tracks')
    return df


if __name__ == '__main__':
    os.makedirs('data', exist_ok=True)
    df = build_dataset()
    df.to_parquet('data/tracks.parquet', index=False)
    print('Saved to data/tracks.parquet')
    print(df[['name', 'artist', 'valence', 'energy']].head(10).to_string())