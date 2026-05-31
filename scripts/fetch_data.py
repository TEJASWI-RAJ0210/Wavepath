import pandas as pd
import time

def fetch_playlist_tracks(playlist_id: str) -> list[dict]:
    results = sp.playlist_tracks(playlist_id)
    tracks = []
    while results:
        for item in results["items"]:
            track = item.get("track")
            if track and track.get("id"):
                tracks.append({
                    "id": track["id"],
                    "name": track["name"],
                    "artist": track["artists"][0]["name"],
                    "preview_url": track.get("preview_url"),
                    "album_image": track["album"]["images"][0]["url"] if track["album"]["images"] else None
                })
        results = sp.next(results) if results["next"] else None
    return tracks

def fetch_audio_features(track_ids: list[str]) -> list[dict]:
    features = []
    # API allows max 100 IDs per call
    for i in range(0, len(track_ids), 100):
        batch = track_ids[i:i+100]
        result = sp.audio_features(batch)
        features.extend([f for f in result if f])
        time.sleep(0.1)  # rate limiting
    return features

# Seed playlists — pick playlists that cover all quadrants of the mood space
SEED_PLAYLISTS = [
    "37i9dQZF1DX3rxVfibe1L0",  # Mood Booster (high valence, high energy)
    "37i9dQZF1DX4sWSpwq3LiO",  # Peaceful Piano (low valence, low energy)
    "37i9dQZF1DWXRqgorJj26U",  # Work From Home (mid valence, mid energy)
    "37i9dQZF1DX889U0CL85jj",  # Late Night (low valence, mid energy)
    "37i9dQZF1DX0XUsuxWHRQd",  # RapCaviar (high energy, variable valence)
    # Add 10-20 more for good coverage
]

all_tracks = []
for pid in SEED_PLAYLISTS:
    all_tracks.extend(fetch_playlist_tracks(pid))

# Deduplicate
track_df = pd.DataFrame(all_tracks).drop_duplicates(subset="id")

# Fetch audio features
features = fetch_audio_features(track_df["id"].tolist())
features_df = pd.DataFrame(features)[["id","valence","energy","danceability",
                                       "tempo","acousticness","instrumentalness","loudness"]]

# Merge
df = track_df.merge(features_df, on="id")
df.to_parquet("data/tracks.parquet", index=False)
print(f"Dataset: {len(df)} tracks")