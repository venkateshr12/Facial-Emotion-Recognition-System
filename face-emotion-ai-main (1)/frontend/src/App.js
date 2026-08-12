import { useEffect, useState } from "react";
import Summary from "./Summary";

const API = "http://127.0.0.1:5000";

export default function App() {
  const [emotion, setEmotion] = useState("Detecting...");
  const [confidence, setConfidence] = useState(0);
  const [sessionId, setSessionId] = useState(null);
  const [viewMode, setViewMode] = useState("live"); // live / summary
  const [loading, setLoading] = useState(false);

  //====================== 🔥 Live Emotion Polling ======================//
  useEffect(() => {
    let stop = false;

    async function poll() {
      while (!stop && sessionId) {
        try {
          const res = await fetch(`${API}/emotion`);
          const data = await res.json();

          const label = data?.emotion ?? "unknown";
          const conf = Number(data?.confidence ?? 0) * 100;

          setEmotion(label);
          setConfidence(conf.toFixed(1));
        } catch {
          setEmotion("backend_offline");
          setConfidence(0);
        }
        await new Promise(r => setTimeout(r, 900));
      }
    }

    if (sessionId) poll();
    return () => (stop = true);
  }, [sessionId]);


  //====================== ▶ START ======================//
  async function startSession() {
    setLoading(true);
    try {
      const res = await fetch(`${API}/sessions/start`, { method: "POST" });
      const data = await res.json();
      setSessionId(data.id);
      setViewMode("live");

      // CLICK FEEDBACK
      animateButton("start-btn");
    } catch {
      alert("Server offline ❗");
    }
    setLoading(false);
  }

  //====================== ⏹ STOP ======================//
  async function stopSession() {
    if (!sessionId) return alert("No active session!");

    await fetch(`${API}/sessions/stop`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id: sessionId }),
    });

    animateButton("stop-btn");
  }

  //====================== 🎉 Button Pop Animation ======================//
  function animateButton(id) {
    const btn = document.getElementById(id);
    btn.style.transform = "scale(1.15)";
    setTimeout(() => (btn.style.transform = "scale(1)"), 200);
  }


  return viewMode === "summary" ? (
    <Summary sessionId={sessionId} goHome={() => setViewMode("live")} />

  ) : (

    //====================== UI PAGE ======================//

    <div style={styles.page}>

      <h1 style={styles.heading}>Real-Time Emotion Detection</h1>

      <div style={styles.videoBox}>
        <img src={`${API}/video_feed`} style={styles.video} alt="camera feed"/>
      </div>

      <div style={styles.card}>
        <h2>Emotion: <b style={{color:"#40c4ff"}}>{emotion}</b></h2>
        <p style={{opacity:0.8}}>Confidence: {confidence}%</p>
      </div>

      {/* BUTTONS */}
      <div style={styles.btnRow}>

        <button id="start-btn"
          style={{...styles.btn, ...styles.start}}
          onClick={startSession}
        >🚀 Start</button>

        <button id="stop-btn"
          style={{...styles.btn, ...styles.stop}}
          onClick={stopSession}
        >⏹ Stop</button>

        <button
          style={{...styles.btn, ...styles.summary}}
          onClick={() => setViewMode("summary")}
        >📊 Summary</button>
      </div>

      <p style={{opacity:0.4}}>Session ID: {sessionId || "Not Started"}</p>
    </div>
  );
}



//====================== 🎨 UI STYLING ======================//
const styles = {
  page:{background:"#0d1117",color:"#fff",minHeight:"100vh",paddingTop:30,textAlign:"center"},

  heading:{fontSize:"2.7rem",fontWeight:800,marginBottom:25},

  videoBox:{width:650,height:470,borderRadius:12,overflow:"hidden",margin:"auto",border:"3px solid #ffffff35"},
  video:{width:"100%",height:"100%",objectFit:"cover"},

  card:{background:"#151b2c",width:300,margin:"18px auto",padding:15,borderRadius:12,border:"1px solid #4dd0ff22"},

  btnRow:{display:"flex",gap:15,justifyContent:"center",marginTop:10},

  btn:{
    fontSize:"1.2rem",padding:"10px 26px",borderRadius:10,fontWeight:700,border:"none",cursor:"pointer",
    transition:"0.15s transform ease"
  },
  start:{background:"#00d47c"},
  stop:{background:"#ff4f4f"},
  summary:{background:"#007bff"},
};

