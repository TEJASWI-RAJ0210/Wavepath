import os
import uuid
import pickle
import sys
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Add project root to path so we can import from models/
# This is needed because main.py is inside backend/ folder
# but models/ is in the root folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.path_finder import find_journey
from models.rl_agent    import get_rl_ordered_playlist
from models.feedback    import update_song_score, rerank_with_feedback

load_dotenv()

# ─────────────────────────────────────────────────────────────
# App setup
# ─────────────────────────────────────────────────────────────

app = FastAPI(
    title       = 'Wavepath API',
    description = 'Mood-based music journey planner for Indian/Bollywood songs',
    version     = '1.0.0'
)

# CORS allows the React frontend (localhost:3000 or localhost:5173)
# to call this API from the browser.
# Without this the browser blocks all requests with a CORS error.
app.add_middleware(
    CORSMiddleware,
    allow_origins  = ['*'],
    allow_methods  = ['*'],
    allow_headers  = ['*'],
)

# ─────────────────────────────────────────────────────────────
# Load mood graph once at startup — not on every request
# The graph is large (~50MB in memory for 8000+ tracks).
# Loading it per-request would add 2-3 seconds of latency
# to every single /journey call. Module-level loading means
# it is loaded once when the server starts and stays in RAM.
# ─────────────────────────────────────────────────────────────

GRAPH_PATH = os.path.join(
    os.path.dirname(__file__), '..', 'models', 'mood_graph.pkl'
)

print('Loading mood graph...')
with open(GRAPH_PATH, 'rb') as f:
    MOOD_GRAPH = pickle.load(f)
print(f'Mood graph loaded: {MOOD_GRAPH.number_of_nodes()} tracks, '
      f'{MOOD_GRAPH.number_of_edges()} edges')

RL_MODEL_PATH = os.path.join(
    os.path.dirname(__file__), '..', 'models', 'ppo_mood_agent'
)

# ─────────────────────────────────────────────────────────────
# Pydantic models — request and response shapes
# FastAPI uses these to:
#   1. Validate incoming JSON automatically
#   2. Generate the Swagger docs at /docs
#   3. Serialise the response back to JSON
# ─────────────────────────────────────────────────────────────

class JourneyRequest(BaseModel):
    start_valence:  float = Field(..., ge=0.0, le=1.0,
                    description='Current mood valence (0=sad, 1=happy)')
    start_energy:   float = Field(..., ge=0.0, le=1.0,
                    description='Current mood energy (0=calm, 1=intense)')
    target_valence: float = Field(..., ge=0.0, le=1.0,
                    description='Target mood valence')
    target_energy:  float = Field(..., ge=0.0, le=1.0,
                    description='Target mood energy')
    n_songs:        int   = Field(8, ge=4, le=15,
                    description='Number of songs in the journey')


class FeedbackRequest(BaseModel):
    session_id: str
    track_id:   str
    action:     str   # skip | like | replay | complete
    position:   int


class TrackOut(BaseModel):
    id:          str
    name:        str
    artist:      str
    valence:     float
    energy:      float
    position:    int
    explanation: str
    preview_url: Optional[str] = None
    album_image: Optional[str] = None


class MoodPoint(BaseModel):
    step:    int
    valence: float
    energy:  float


class JourneyResponse(BaseModel):
    session_id: str
    playlist:   list[TrackOut]
    mood_arc:   list[MoodPoint]


# ─────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────

@app.post('/journey', response_model=JourneyResponse)
def create_journey(req: JourneyRequest):
    """
    Main endpoint. Takes start and target mood coordinates,
    returns an ordered playlist with mood arc data.

    Full pipeline:
      1. A* graph search  → candidate songs
      2. PPO RL agent     → optimal ordering
      3. Feedback rerank  → adjust by skip/like history
      4. Build response   → explanations + mood arc
    """

    # ── Step 1: A* search finds candidate songs ───────────────
    # find_journey() walks the k-NN mood graph from the node
    # closest to start_mood toward target_mood using A* search.
    # Returns a list of song dicts ordered by graph traversal.
    candidates = find_journey(
        MOOD_GRAPH,
        req.start_valence,  req.start_energy,
        req.target_valence, req.target_energy,
        n_songs = req.n_songs
    )

    if not candidates:
        raise HTTPException(
            status_code = 404,
            detail = (
                'No path found in mood graph. '
                'Try slightly different mood coordinates.'
            )
        )

    # ── Step 2: RL agent reorders the candidates ──────────────
    # The A* path gives us the right songs but not necessarily
    # the best order. The PPO agent learned to order them so
    # valence and energy follow a smooth arc toward the target.
    # ordered = get_rl_ordered_playlist(
    #     candidates,
    #     target_mood = (req.target_valence, req.target_energy),
    #     model_path  = RL_MODEL_PATH
    # )
    
    ordered = sorted(
    candidates,
    key=lambda s: s['valence'] + s['energy']
)

    # ── Step 3: Re-rank using Redis feedback scores ───────────
    # Songs the user previously liked score higher.
    # Songs the user previously skipped score lower.
    # 0.7 * position_score + 0.3 * feedback_score
    ordered = rerank_with_feedback(ordered)

    # ── Step 4: Build the response ────────────────────────────
    playlist = []
    for i, song in enumerate(ordered):
        # Generate explanation text shown on each playlist card
        if i == 0:
            explanation = 'Shuru — closest to your current mood'
        elif i == len(ordered) - 1:
            explanation = 'Manzil — your target mood reached'
        else:
            prev = ordered[i - 1]
            dv   = song['valence'] - prev['valence']
            de   = song['energy']  - prev['energy']
            if dv > 0.05:
                direction = 'Khushi ki taraf'
            elif dv < -0.05:
                direction = 'Sukoon ki taraf'
            else:
                direction = 'Stable mood'
            explanation = f'val {dv:+.2f}  nrg {de:+.2f}  — {direction}'

        playlist.append(TrackOut(
            id          = song['id'],
            name        = song['name'],
            artist      = song['artist'],
            valence     = round(song['valence'], 3),
            energy      = round(song['energy'],  3),
            position    = i,
            explanation = explanation,
            preview_url = song.get('preview_url'),
            album_image = song.get('album_image'),
        ))

    # Build mood arc — list of {step, valence, energy} per song
    # This is what the frontend chart plots
    mood_arc = [
        MoodPoint(step=i, valence=t.valence, energy=t.energy)
        for i, t in enumerate(playlist)
    ]

    return JourneyResponse(
        session_id = str(uuid.uuid4()),
        playlist   = playlist,
        mood_arc   = mood_arc
    )


@app.post('/feedback')
def submit_feedback(req: FeedbackRequest):
    """
    Record a user action for a track.
    Updates the score in Upstash Redis instantly.
    The next /journey call will use the updated score
    in the rerank_with_feedback() step.
    """
    valid_actions = {'skip', 'like', 'replay', 'complete'}
    if req.action not in valid_actions:
        raise HTTPException(
            status_code = 400,
            detail = f'Invalid action. Must be one of: {valid_actions}'
        )

    new_score = update_song_score(req.track_id, req.action)
    return {
        'status':    'ok',
        'track_id':  req.track_id,
        'action':    req.action,
        'new_score': round(new_score, 3)
    }


@app.get('/health')
def health():
    """
    Quick check that the server is up and the graph is loaded.
    Use this to verify deployment is working.
    """
    return {
        'status': 'ok',
        'tracks': MOOD_GRAPH.number_of_nodes(),
        'edges':  MOOD_GRAPH.number_of_edges()
    }


@app.get('/similar/{track_id}')
def get_similar(track_id: str, n: int = 5):
    """
    Return n tracks most mood-similar to the given track.
    Useful for debugging — lets you verify the graph
    neighbours make musical sense.
    """
    if track_id not in MOOD_GRAPH:
        raise HTTPException(
            status_code = 404,
            detail = f'Track {track_id} not found in mood graph'
        )

    neighbours = sorted(
        MOOD_GRAPH.neighbors(track_id),
        key = lambda n: MOOD_GRAPH[track_id][n]['weight']
    )[:n]

    return [
        {
            'id':      node,
            'name':    MOOD_GRAPH.nodes[node]['name'],
            'artist':  MOOD_GRAPH.nodes[node]['artist'],
            'valence': round(MOOD_GRAPH.nodes[node]['valence'], 3),
            'energy':  round(MOOD_GRAPH.nodes[node]['energy'],  3),
        }
        for node in neighbours
    ]