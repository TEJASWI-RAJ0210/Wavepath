import { LineChart, Line, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from "recharts";

export default function MoodArcChart({ moodArc, targetValence, targetEnergy }) {
  return (
    <div className="w-full h-56">
      <ResponsiveContainer>
        <LineChart data={moodArc} margin={{ top: 8, right: 20, left: 0, bottom: 8 }}>
          <XAxis dataKey="step" label={{ value: "Song #", position: "insideBottom", offset: -4 }} />
          <YAxis domain={[0, 1]} />
          <Tooltip formatter={(v) => v.toFixed(2)} />
          <Legend />
          <ReferenceLine y={targetValence} stroke="#a855f7" strokeDasharray="4 4" label="Target valence" />
          <ReferenceLine y={targetEnergy}  stroke="#f97316" strokeDasharray="4 4" label="Target energy" />
          <Line type="monotone" dataKey="valence" stroke="#a855f7" strokeWidth={2} dot={{ r: 4 }} name="Valence" />
          <Line type="monotone" dataKey="energy"  stroke="#f97316" strokeWidth={2} dot={{ r: 4 }} name="Energy" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}