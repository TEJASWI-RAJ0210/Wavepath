import os
import pandas as pd
import numpy as np

# ─────────────────────────────────────────────────────────────
# This dataset (maharshipandya Spotify Tracks) has these columns:
# track_id, artists, album_name, track_name, popularity,
# duration_ms, explicit, danceability, energy, key, loudness,
# mode, speechiness, acousticness, instrumentalness, liveness,
# valence, tempo, time_signature, track_genre
# ─────────────────────────────────────────────────────────────

# Indian music genres present in this dataset.
# We filter to only these so the mood space is built
# entirely from Indian music — not pop or rock.
INDIAN_GENRES = [
    'indian', 'hindi', 'bollywood', 'desi',
    'tamil', 'telugu', 'punjabi', 'south-indian',
    'malayalam', 'kannada', 'bhojpuri', 'gujarati',
    'marathi', 'rajasthani', 'haryanvi'
]


def load_and_filter(csv_path: str) -> pd.DataFrame:
    """
    Load the Kaggle Spotify Tracks CSV and filter to Indian genres only.
    """
    print(f'Loading {csv_path}...')
    df = pd.read_csv(csv_path)
    print(f'Total rows in CSV: {len(df)}')
    print(f'Columns: {list(df.columns)}')
    print()

    # ── Rename columns to match our app's schema ──────────────
    # The CSV uses different names than what our app expects
    df = df.rename(columns={
        'track_id':   'id',
        'track_name': 'name',
        'artists':    'artist',
    })

    # ── Filter to Indian genres ───────────────────────────────
    # track_genre column has values like 'indian', 'tamil', etc.
    # We keep a row if its genre matches any Indian genre keyword.
    mask = df['track_genre'].str.lower().str.contains(
        '|'.join(INDIAN_GENRES), na=False
    )
    indian_df = df[mask].copy()
    print(f'Indian genre tracks found: {len(indian_df)}')

    # ── If no Indian tracks found, warn and use full dataset ──
    # Some versions of this CSV may have slightly different genre names.
    # In that case we print all unique genres so you can check manually.
    if len(indian_df) < 100:
        print()
        print('WARNING: Very few Indian tracks found.')
        print('All genres in the dataset:')
        print(sorted(df['track_genre'].unique()))
        print()
        print('Using full dataset as fallback...')
        indian_df = df.copy()

    return indian_df


def clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and validate the dataset.
    After this function, the DataFrame is guaranteed to have:
    - id, name, artist, valence, energy columns
    - All values in 0-1 range
    - No duplicates
    - No missing valence or energy
    """

    # ── Add columns our app needs but dataset doesn't have ────
    # This dataset was scraped before Spotify removed preview URLs.
    # We set these to None — the frontend handles missing previews.
    if 'preview_url' not in df.columns:
        df['preview_url'] = None
    if 'album_image' not in df.columns:
        df['album_image'] = None

    # ── Drop rows with missing required values ─────────────────
    required = ['id', 'name', 'artist', 'valence', 'energy']
    before   = len(df)
    df = df.dropna(subset=required)
    print(f'Dropped {before - len(df)} rows with missing required values')

    # ── Normalise to 0-1 if any column is on 0-100 scale ──────
    # This dataset uses 0-1 scale already, but we check anyway
    # in case you switch to a different dataset later
    for col in ['valence', 'energy', 'danceability', 'acousticness']:
        if col in df.columns and df[col].max() > 1.0:
            df[col] = df[col] / 100.0
            print(f'Normalised {col} from 0-100 to 0-1 scale')

    # ── Clip to valid range just in case ──────────────────────
    for col in ['valence', 'energy', 'danceability', 'acousticness']:
        if col in df.columns:
            df[col] = df[col].clip(0.0, 1.0)

    # ── Deduplicate ───────────────────────────────────────────
    before = len(df)
    df = df.drop_duplicates(subset='id')
    print(f'Removed {before - len(df)} duplicate tracks')

    # ── Keep only the columns our app uses ────────────────────
    keep = ['id', 'name', 'artist', 'valence', 'energy',
            'danceability', 'tempo', 'acousticness',
            'instrumentalness', 'preview_url', 'album_image']
    df = df[[c for c in keep if c in df.columns]]

    print(f'Final clean dataset: {len(df)} tracks')
    return df


def build_dataset(csv_path: str) -> pd.DataFrame:
    """Main pipeline: load → filter → clean → return."""
    print('=== Step 1: Load and filter to Indian music ===')
    df = load_and_filter(csv_path)

    print()
    print('=== Step 2: Clean and validate ===')
    df = clean_dataset(df)

    print()
    print('=== Step 3: Final summary ===')
    print(f'Tracks: {len(df)}')
    print(f'Valence range: {df.valence.min():.3f} to {df.valence.max():.3f}')
    print(f'Energy range:  {df.energy.min():.3f} to {df.energy.max():.3f}')
    print()
    print('Sample tracks:')
    print(df[['name', 'artist', 'valence', 'energy']].head(10).to_string())

    return df


if __name__ == '__main__':
    os.makedirs('data', exist_ok=True)

    df = build_dataset('data/tracks.csv')
    df.to_parquet('data/tracks.parquet', index=False)
    print()
    print('Saved to data/tracks.parquet')