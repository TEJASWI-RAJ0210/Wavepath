import { useState } from "react";
import MoodCanvas from "./components/MoodCanvas";
import MoodArcChart from "./components/MoodArcChart";
import PlaylistCard from "./components/PlaylistCard";

const API = "http://localhost:8000";

export default function App() {
  const [startMood,  setStartMood]  = useState(null);
  const [targetMood, setTargetMood] = useState(null);
  const [journey,    setJourney]    = useState(null);
  const [loading,    setLoading]    = useState(false);
  const [sessionId,  setSessionId]  = useState(null);

  const buildJourney = async () => {
    if (!startMood || !targetMood) return;
    setLoading(true);
    const res = await fetch(`${API}/journey`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        start_valence:  startMood.valence,
        start_energy:   startMood.energy,
        target_valence: targetMood.valence,
        target_energy:  targetMood.energy,
        n_songs: 8
      })
    });
    const data = await res.json();
    setJourney(data);
    setSessionId(data.session_id);
    setLoading(false);
  };

  const sendFeedback = async (trackId, action, position) => {
    await fetch(`${API}/feedback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, track_id: trackId, action, position })
    });
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-semibold mb-1">Mood Journey Planner</h1>
      <p className="text-gray-500 mb-8">Set your current mood and your target. We'll build the arc.</p>

      <div className="grid grid-cols-2 gap-6 mb-6">
        <MoodCanvas value={startMood}  onChange={setStartMood}  label="Where you are now" color="#a855f7" />
        <MoodCanvas value={targetMood} onChange={setTargetMood} label="Where you want to be" color="#f97316" />
      </div>

      <button onClick={buildJourney} disabled={!startMood || !targetMood || loading}
        className="w-full py-3 rounded-xl bg-purple-600 text-white font-medium disabled:opacity-40 mb-8">
        {loading ? "Building your journey..." : "Build my journey →"}
      </button>

      {journey && (
        <>
          <h2 className="font-medium mb-3">Your mood arc</h2>
          <MoodArcChart
            moodArc={journey.mood_arc}
            targetValence={targetMood.valence}
            targetEnergy={targetMood.energy}
          />
          <h2 className="font-medium mt-6 mb-3">Your playlist ({journey.playlist.length} songs)</h2>
          <div className="flex flex-col gap-2">
            {journey.playlist.map((track, i) => (
              <PlaylistCard
                key={track.id}
                track={track}
                isActive={false}
                onFeedback={(action) => sendFeedback(track.id, action, i)}
              />
            ))}
          </div>
        </>
      )}
    </div>
  );
}