import { useState } from "react";
import Howl from "howler";

export default function PlaylistCard({ track, onFeedback, isActive }) {
  const [playing, setPlaying] = useState(false);
  const [sound, setSound] = useState(null);

  const togglePlay = () => {
    if (!track.preview_url) return;
    if (playing) {
      sound?.pause();
      setPlaying(false);
    } else {
      const s = new Howl({ src: [track.preview_url], html5: true,
        onend: () => { setPlaying(false); onFeedback("complete"); }
      });
      s.play();
      setSound(s);
      setPlaying(true);
      onFeedback("play");
    }
  };

  return (
    <div className={`flex items-center gap-3 p-3 rounded-xl border transition-all
      ${isActive ? "border-purple-300 bg-purple-50" : "border-gray-100 bg-white"}`}>
      <img src={track.album_image} alt="" className="w-12 h-12 rounded-lg object-cover" />
      <div className="flex-1 min-w-0">
        <p className="font-medium text-sm truncate">{track.name}</p>
        <p className="text-xs text-gray-500 truncate">{track.artist}</p>
        <p className="text-xs text-gray-400 mt-1">{track.explanation}</p>
      </div>
      <div className="flex gap-1">
        <button onClick={() => onFeedback("skip")}  className="p-1 text-gray-400 hover:text-red-400 text-lg">⏭</button>
        <button onClick={togglePlay}                 className="p-1 text-gray-400 hover:text-purple-500 text-lg">{playing ? "⏸" : "▶"}</button>
        <button onClick={() => onFeedback("like")}  className="p-1 text-gray-400 hover:text-pink-400 text-lg">♥</button>
      </div>
      <div className="text-right text-xs text-gray-400 w-14">
        <div>val {track.valence.toFixed(2)}</div>
        <div>nrg {track.energy.toFixed(2)}</div>
      </div>
    </div>
  );
}