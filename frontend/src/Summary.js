import { useEffect, useState } from "react";
import Timeline from "./Timeline";

const API = "http://127.0.0.1:5000";

/* ==================== EMOJI RAIN WHEN HAPPY ==================== */
function rainEmoji() {
  let count = 45;
  while (count--) {
    const node = document.createElement("div");
    node.innerText = "😄";
    node.style.position = "fixed";
    node.style.fontSize = "40px";
    node.style.left = Math.random() * 100 + "vw";
    node.style.top = "-30px";
    node.style.transition = "7s linear";
    document.body.appendChild(node);

    setTimeout(() => (node.style.top = "100vh"), 100);
    setTimeout(() => node.remove(), 7000);
  }
}

export default function Summary({ sessionId, goHome }) {
  const [summary, setSummary] = useState(null);

  useEffect(() => {
    async function load() {
      const res = await fetch(`${API}/sessions/${sessionId}/summary`);
      const data = await res.json();
      setSummary(data);

      if (data?.top_emotion === "happy") rainEmoji();
    }
    load();
  }, []);

  if (!summary) return <h2 style={{ color: "white", marginTop: 60 }}>Loading Summary...</h2>;

  const emotions = summary.percentages || {};

  const colors = {
    angry:"#ff1744", sad:"#2979ff", happy:"#00e676", neutral:"#bdbdbd",
    surprised:"#ffea00", disgust:"#b000b5", fear:"#ef6c00", none:"#666"
  };

  return (
    <div style={styles.page}>
      <h1 style={styles.heading}>📊 Session Summary</h1>

      {/* ================== SUMMARY INFO BLOCK ================== */}
      <div style={styles.infoCard}>
        <h2>🧾 Report Details</h2>
        <p><b>📌 Total Samples:</b> {summary.total_samples}</p>
        <p><b>🏆 Top Emotion:</b> <span style={{color:colors[summary.top_emotion]}}>
          {summary.top_emotion.toUpperCase()}
        </span></p>
      </div>

      {/* ================== BAR CHART ================== */}
      <div style={styles.chart}>
        {Object.entries(emotions).map(([emo,val])=>(
          <div key={emo} style={{textAlign:"center"}}>
            <div style={{
              height: val*3+"px",
              width:"58px",
              background:colors[emo],
              borderRadius:8,
              margin:"auto",
              boxShadow:"0px 0px 10px rgba(255,255,255,.3)"
            }} title={`Samples: ${summary.counts?.[emo] || 0}`}></div>

            <p style={{marginTop:6,fontSize:14}}>
              {emo} ({val.toFixed(1)}%)
            </p>
          </div>
        ))}
      </div>

      {/* Timeline Graph */}
      <Timeline data={summary} />

      {/* Buttons */}
      <div style={styles.btnRow}>
        <button style={styles.back} onClick={goHome}>⬅ Back to Live</button>

        <button
          style={styles.pdf}
          onClick={() => window.open(`${API}/sessions/${sessionId}/pdf`, "_blank")}
        >
          📄 Download PDF Report
        </button>
      </div>
    </div>
  );
}

/* ==================== STYLES ==================== */
const styles = {
  page:{ background:"#0d1117", color:"white", minHeight:"100vh", paddingTop:35, textAlign:"center" },
  heading:{ fontSize:"2.4rem", fontWeight:800, marginBottom:20 },

  infoCard:{
    background:"#141b29", padding:"18px 30px", width:"350px", margin:"auto",
    borderRadius:12, border:"1px solid #00e67655", marginBottom:35
  },

  chart:{ display:"flex", gap:30, justifyContent:"center", flexWrap:"wrap", marginTop:20 },

  btnRow:{ marginTop:35, display:"flex", gap:25, justifyContent:"center" },

  back:{ background:"#4da3ff", padding:"10px 22px", borderRadius:10, fontSize:"1.1rem" },
  pdf:{ background:"#00c853", padding:"10px 22px", borderRadius:10, fontSize:"1.1rem" }
};
