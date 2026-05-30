# 🎵 Wavepath

> *A mood-aware music journey planner that builds playlists to carry you from how you feel right now to how you want to feel.*

![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green?style=flat-square&logo=fastapi)
![React](https://img.shields.io/badge/React-18-61dafb?style=flat-square&logo=react)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)
![Status](https://img.shields.io/badge/Status-In%20Development-orange?style=flat-square)

---

## What is Wavepath?

Most music apps ask *"what do you like?"* — Wavepath asks *"where are you emotionally, and where do you want to go?"*

You drag two points on a 2D mood canvas (valence × energy). Wavepath builds a playlist where every song moves you incrementally closer to your target mood — no jarring jumps, no random detours. Recommendation as an emotional arc, not a static list.

```
Sad + Low Energy  ──►  ──►  ──►  ──►  Happy + Energetic
    😔           song 1  song 2  song 3      😊
  (0.2, 0.3)   smoothly shifting valence & energy   (0.8, 0.75)
```

---

## Demo

| Mood Canvas | Live Arc Chart | Playlist with Explanations |
|---|---|---|
| Drag to set start & target mood | Valence + energy plotted per song | Each track explains why it was chosen |

> 🎬 **[Watch the demo video](#)** · 🌐 **[Try the live app](#)**

---

## How It Works

Wavepath combines three ML components into a pipeline:

### 1. Mood Graph (k-NN Graph)
20,000+ Spotify tracks are embedded in a 2D valence × energy space. A k-nearest-neighbour graph connects each track to its 10 closest mood neighbours. Edge weight = Euclidean distance in mood space.

### 2. Path Finder (A* Search)
Given a start mood and target mood, A* search finds the smoothest path through the mood graph — minimising total valence/energy deviation at each step.

### 3. RL Ordering Agent (PPO)
A Proximal Policy Optimisation agent learns the best *ordering* of candidate songs to maximise trajectory smoothness. Trained with:
- **Reward**: negative deviation from the ideal linear mood arc
- **Bonus**: +2.0 for reaching target mood within threshold
- **Online updates**: skips (−0.3) and likes (+0.2) from real users via Redis

```
Spotify API
    │
    ▼
Track Dataset (valence, energy, danceability, tempo...)
    │
    ▼
Mood Graph ──► A* Path Finder ──► Candidate Songs
                                        │
                                        ▼
                                   PPO RL Agent
                                        │
                                        ▼
                              Ordered Playlist + Explanations
                                        │
                                  User Feedback (skip/like)
                                        │
                                        ▼
                                  Redis Online Learner
```

---

## Features

- **2D Mood Canvas** — drag-to-set current and target mood on a valence × energy grid
- **Smooth mood arc** — A* graph search guarantees no abrupt emotional jumps
- **RL-optimised ordering** — PPO agent trained to follow the ideal trajectory
- **Live trajectory chart** — real-time valence/energy line chart as playlist plays
- **30-second audio previews** — powered by Spotify's preview URLs via Howler.js
- **Explainability panel** — every song tells you *why* it was chosen
- **Online learning** — skips and likes update song weights in real-time via Redis
- **A/B evaluation dashboard** — RL agent vs greedy vs random baseline comparison

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Data** | Spotify Web API · spotipy · pandas · PostgreSQL |
| **ML — Graph** | NetworkX · scikit-learn (k-NN) |
| **ML — RL** | Stable-Baselines3 (PPO) · Gymnasium |
| **ML — Feedback** | Redis (online score updates) |
| **Backend** | FastAPI · SQLAlchemy · Pydantic · Uvicorn |
| **Frontend** | React 18 · Vite · Tailwind CSS · Recharts · Howler.js |
| **Infrastructure** | Docker · PostgreSQL · Redis |

---

## Project Structure

```
wavepath/
│
├── data/
│   ├── tracks.parquet          # Track dataset with audio features
│   └── seed_playlists.txt      # Spotify playlist IDs used for seeding
│
├── models/
│   ├── mood_graph.pkl          # Serialised k-NN mood graph
│   ├── ppo_mood_agent.zip      # Trained PPO model weights
│   ├── path_finder.py          # A* search implementation
│   ├── rl_agent.py             # Gymnasium env + PPO wrapper
│   └── feedback.py             # Redis online learning
│
├── backend/
│   ├── main.py                 # FastAPI app + all endpoints
│   ├── database.py             # SQLAlchemy models
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   └── components/
│   │       ├── MoodCanvas.jsx      # 2D drag-to-set mood input
│   │       ├── MoodArcChart.jsx    # Live trajectory chart
│   │       └── PlaylistCard.jsx    # Track card + audio + feedback
│   └── package.json
│
├── notebooks/
│   ├── 01_data_pipeline.ipynb  # Data fetching + EDA
│   ├── 02_graph_building.ipynb # Mood graph construction
│   ├── 03_rl_training.ipynb    # PPO training + reward curves
│   └── 04_evaluation.ipynb     # A/B comparison metrics
│
├── scripts/
│   ├── fetch_data.py           # One-time Spotify data pipeline
│   └── train_rl.py             # RL training script
│
├── docker-compose.yml
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker (for PostgreSQL + Redis)
- Spotify Developer account → [Create an app here](https://developer.spotify.com/dashboard)

### 1. Clone the repo

```bash
git clone https://github.com/yourusername/wavepath.git
cd wavepath
```

### 2. Set up environment variables

```bash
cp .env.example .env
```

Edit `.env`:

```env
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
DATABASE_URL=postgresql://user:pass@localhost:5432/wavepath
REDIS_URL=redis://localhost:6379
```

### 3. Start infrastructure

```bash
docker-compose up -d
# Starts PostgreSQL on :5432 and Redis on :6379
```

### 4. Install Python dependencies & build data pipeline

```bash
cd backend
pip install -r requirements.txt

# Fetch tracks from Spotify and build the mood graph
python ../scripts/fetch_data.py    # ~10 min, builds 20k track dataset
python ../scripts/train_rl.py      # ~20 min, trains PPO agent
```

### 5. Start the backend

```bash
uvicorn main:app --reload --port 8000
# API docs available at http://localhost:8000/docs
```

### 6. Start the frontend

```bash
cd ../frontend
npm install
npm run dev
# App available at http://localhost:3000
```

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/journey` | Generate a mood journey playlist |
| `POST` | `/feedback` | Submit skip / like / replay signal |
| `GET` | `/track/{id}/similar` | Get mood-similar tracks |
| `GET` | `/health` | Service health check |

### Example — create a journey

```bash
curl -X POST http://localhost:8000/journey \
  -H "Content-Type: application/json" \
  -d '{
    "start_valence": 0.2,
    "start_energy": 0.3,
    "target_valence": 0.8,
    "target_energy": 0.75,
    "n_songs": 8
  }'
```

```json
{
  "session_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "playlist": [
    {
      "id": "4uLU6hMCjMI75M1A2tKUQC",
      "name": "Don't Stop Me Now",
      "artist": "Queen",
      "valence": 0.97,
      "energy": 0.84,
      "explanation": "This song lifts your mood (valence +0.18, energy +0.12)",
      "preview_url": "https://p.scdn.co/mp3-preview/...",
      "album_image": "https://i.scdn.co/image/..."
    }
  ],
  "mood_arc": [
    { "step": 0, "valence": 0.22, "energy": 0.31 },
    { "step": 1, "valence": 0.41, "energy": 0.48 }
  ]
}
```

---

## Evaluation

Wavepath uses both offline and online metrics to measure recommendation quality.

### Offline — algorithm comparison

| Algorithm | Mean Arc Deviation ↓ | Max Step Jump ↓ | Completion Rate ↑ |
|---|---|---|---|
| **RL Agent (PPO)** | **0.08** | **0.14** | **81%** |
| Greedy (graph order) | 0.13 | 0.22 | 67% |
| Random baseline | 0.31 | 0.48 | 41% |

### Online metrics (target)

| Metric | Target |
|---|---|
| Journey completion rate | > 70% |
| Skip rate | < 20% |
| Mean mood deviation at end | < 0.15 |
| Session length | > 15 min |

Full evaluation methodology is in [`notebooks/04_evaluation.ipynb`](notebooks/04_evaluation.ipynb).

---

## Roadmap

- [x] Spotify data pipeline
- [x] k-NN mood graph construction
- [x] A* path finder
- [x] PPO RL ordering agent
- [x] FastAPI backend
- [x] React frontend with mood canvas
- [x] Online feedback learning (Redis)
- [ ] User accounts + persistent history
- [ ] 4D mood space (+ danceability, acousticness)
- [ ] BERT4Rec sequence model for long-range preferences
- [ ] Social features ("340 people took this journey today")
- [ ] Mobile app (React Native)

---

## Notebooks

| Notebook | Description |
|---|---|
| [`01_data_pipeline`](notebooks/01_data_pipeline.ipynb) | Spotify API fetching, EDA, valence×energy scatter plots |
| [`02_graph_building`](notebooks/02_graph_building.ipynb) | k-NN graph construction, edge distribution analysis |
| [`03_rl_training`](notebooks/03_rl_training.ipynb) | PPO training, reward curves, policy visualisation |
| [`04_evaluation`](notebooks/04_evaluation.ipynb) | A/B test: RL vs greedy vs random, all metrics |

---

## Contributing

Contributions are welcome. Please open an issue first to discuss what you'd like to change.

```bash
# Fork the repo, then:
git checkout -b feature/your-feature-name
git commit -m "feat: add your feature"
git push origin feature/your-feature-name
# Open a Pull Request
```

---

## License

MIT — see [LICENSE](LICENSE) for details.

---

## Acknowledgements

- [Spotify Web API](https://developer.spotify.com/documentation/web-api) for audio features
- [Stable-Baselines3](https://stable-baselines3.readthedocs.io) for the PPO implementation
- [spotipy](https://spotipy.readthedocs.io) for the Python Spotify client
- Inspired by research on mood-based music recommendation and affective computing

---

<p align="center">Built with ♥ as a portfolio project · <a href="#">Live Demo</a> · <a href="#">Video Walkthrough</a></p>