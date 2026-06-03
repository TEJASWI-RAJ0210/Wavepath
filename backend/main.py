# main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pickle
import uuid

app = FastAPI(title="Mood Journey API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load models at startup
with open("models/mood_graph.pkl", "rb") as f:
    MOOD_GRAPH = pickle.load(f)

# ── Request / Response Models ──────────────────────────────

class JourneyRequest(BaseModel):
    start_valence: float   # 0.0 – 1.0
    start_energy: float    # 0.0 – 1.0
    target_valence: float  # 0.0 – 1.0
    target_energy: float   # 0.0 – 1.0
    n_songs: int = 8       # playlist length

class FeedbackRequest(BaseModel):
    session_id: str
    track_id: str
    action: str            # skip | like | replay | complete
    position: int

class TrackOut(BaseModel):
    id: str
    name: str
    artist: str
    valence: float
    energy: float
    preview_url: str | None
    album_image: str | None
    position: int
    explanation: str

class JourneyResponse(BaseModel):
    session_id: str
    playlist: list[TrackOut]
    mood_arc: list[dict]   # [{step, valence, energy}] for chart

# ── Endpoints ──────────────────────────────────────────────

@app.post("/journey", response_model=JourneyResponse)
def create_journey(req: JourneyRequest):
    from models.path_finder import find_journey
    from models.rl_agent import get_rl_ordered_playlist
    from models.feedback import rerank_with_feedback

    # 1. Graph path-finding
    candidates = find_journey(
        MOOD_GRAPH,
        req.start_valence, req.start_energy,
        req.target_valence, req.target_energy,
        n_songs=req.n_songs
    )
    if not candidates:
        raise HTTPException(status_code=404, detail="No path found in mood graph")

    # 2. RL ordering
    ordered = get_rl_ordered_playlist(
        candidates,
        target_mood=(req.target_valence, req.target_energy)
    )

    # 3. Re-rank with feedback
    ordered = rerank_with_feedback(ordered)

    # 4. Build explanations
    playlist = []
    for i, song in enumerate(ordered):
        if i == 0:
            explanation = f"Starting point — closest to your current mood"
        elif i == len(ordered) - 1:
            explanation = f"Your destination — valence {song['valence']:.2f}, energy {song['energy']:.2f}"
        else:
            delta_v = song["valence"] - ordered[i-1]["valence"]
            delta_e = song["energy"]  - ordered[i-1]["energy"]
            direction = "lifts" if delta_v > 0 else "softens"
            explanation = f"This song {direction} your mood (valence {delta_v:+.2f}, energy {delta_e:+.2f})"

        playlist.append(TrackOut(
            **{k: song[k] for k in ["id","name","artist","valence","energy","preview_url","album_image"]},
            position=i,
            explanation=explanation
        ))

    mood_arc = [{"step": i, "valence": s.valence, "energy": s.energy}
                for i, s in enumerate(playlist)]

    session_id = str(uuid.uuid4())
    return JourneyResponse(session_id=session_id, playlist=playlist, mood_arc=mood_arc)


@app.post("/feedback")
def submit_feedback(req: FeedbackRequest):
    from models.feedback import update_song_score
    new_score = update_song_score(req.track_id, req.action)
    return {"status": "ok", "new_score": round(new_score, 3)}


@app.get("/track/{track_id}/similar")
def get_similar(track_id: str, n: int = 5):
    """Return n tracks most mood-similar to the given track."""
    if track_id not in MOOD_GRAPH:
        raise HTTPException(status_code=404, detail="Track not found")
    neighbours = sorted(
        MOOD_GRAPH.neighbors(track_id),
        key=lambda n: MOOD_GRAPH[track_id][n]["weight"]
    )[:n]
    return [{"id": n, **MOOD_GRAPH.nodes[n]} for n in neighbours]


@app.get("/health")
def health():
    return {"status": "ok", "tracks": MOOD_GRAPH.number_of_nodes()}