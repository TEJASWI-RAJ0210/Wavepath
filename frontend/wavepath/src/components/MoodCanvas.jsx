import { useState, useRef } from "react";

const MOODS = [
  { label: "Happy",      valence: 0.85, energy: 0.75, emoji: "😄", x: "75%", y: "20%" },
  { label: "Excited",    valence: 0.80, energy: 0.95, emoji: "🤩", x: "75%", y: "5%"  },
  { label: "Calm",       valence: 0.70, energy: 0.25, emoji: "😌", x: "75%", y: "75%" },
  { label: "Sad",        valence: 0.15, energy: 0.20, emoji: "😔", x: "15%", y: "75%" },
  { label: "Angry",      valence: 0.10, energy: 0.90, emoji: "😤", x: "10%", y: "5%"  },
  { label: "Melancholic",valence: 0.25, energy: 0.35, emoji: "😞", x: "20%", y: "60%" },
];

export default function MoodCanvas({ value, onChange, label, color }) {
  const canvasRef = useRef(null);

  const handleClick = (e) => {
    const rect = canvasRef.current.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width;
    const y = 1 - (e.clientY - rect.top) / rect.height; // invert Y: top = high energy
    onChange({ valence: Math.max(0, Math.min(1, x)), energy: Math.max(0, Math.min(1, y)) });
  };

  return (
    <div className="flex flex-col gap-2">
      <p className="text-sm font-medium text-gray-500">{label}</p>
      <div
        ref={canvasRef}
        onClick={handleClick}
        className="relative w-full h-64 border border-gray-200 rounded-xl bg-gray-50 cursor-crosshair"
      >
        {/* Axis labels */}
        <span className="absolute top-2 left-1/2 -translate-x-1/2 text-xs text-gray-400">High energy</span>
        <span className="absolute bottom-2 left-1/2 -translate-x-1/2 text-xs text-gray-400">Low energy</span>
        <span className="absolute left-2 top-1/2 -translate-y-1/2 text-xs text-gray-400 -rotate-90">Sad</span>
        <span className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-gray-400 -rotate-90">Happy</span>

        {/* Mood region labels */}
        {MOODS.map(m => (
          <span key={m.label} className="absolute text-lg" style={{ left: m.x, top: m.y }}
            title={m.label}>{m.emoji}</span>
        ))}

        {/* Current position dot */}
        {value && (
          <div
            className="absolute w-5 h-5 rounded-full border-2 border-white -translate-x-1/2 -translate-y-1/2 transition-all"
            style={{
              left: `${value.valence * 100}%`,
              top: `${(1 - value.energy) * 100}%`,
              background: color
            }}
          />
        )}
      </div>
    </div>
  );
}