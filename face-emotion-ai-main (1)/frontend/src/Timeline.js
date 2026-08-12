import React from "react";
import { Line } from "react-chartjs-2";
import { Chart as ChartJS, LineElement, CategoryScale, LinearScale, PointElement, Legend } from "chart.js";

ChartJS.register(LineElement, CategoryScale, LinearScale, PointElement, Legend);

export default function Timeline({ data }) {
  if (!data || !data.timeline || data.timeline.length === 0) {
    return <p style={{ color: "#bbb", marginTop: 20 }}>📌 Timeline not available — session too short</p>;
  }

  const timeline = data.timeline; // safe now

  const labels = timeline.map(item => `Min ${item.minute}`);

  // extracting counts safely
  const emotions = ["happy", "sad", "angry", "neutral", "fear", "surprised", "disgust"];
  const datasets = emotions.map(colorEmotion => ({
    label: colorEmotion,
    data: timeline.map(item => item.counts[colorEmotion] || 0),
    borderColor: emotionColors[colorEmotion],
    backgroundColor: emotionColors[colorEmotion],
    tension: 0.3,
    borderWidth: 3,
    pointRadius: 4,
    hidden: datasetsHidden(colorEmotion, timeline) // hide if emotion never appears
  }));

  return (
    <div style={{ width: "80%", margin: "40px auto", background: "#111", padding: 20, borderRadius: 12 }}>
      <h2 style={{ color: "white", marginBottom: 15 }}>📈 Emotion Timeline</h2>
      <Line 
        data={{ labels, datasets }} 
        options={{ responsive:true, plugins:{ legend:{ labels:{ color:"white"}}}, scales:{ x:{ ticks:{ color:"#ddd"}}, y:{ ticks:{color:"#ccc"}} }}}
      />
    </div>
  );
}

/* 🎨 Color palette */
const emotionColors = {
  happy:"#00e676",
  sad:"#2979ff",
  angry:"#ff1744",
  neutral:"#bdbdbd",
  fear:"#ff9100",
  surprised:"#ffea00",
  disgust:"#b000b5"
};

/* Hide lines if emotion count is ZERO everywhere */
function datasetsHidden(emotion, timeline){
  return !timeline.some(t => t.counts[emotion] > 0);
}
