from flask import Flask, jsonify, Response, request, send_file
from flask_cors import CORS
import cv2
from fer.fer import FER
import threading
import atexit
import uuid
import time
import json
import os
import logging
from datetime import datetime

# ===== extra imports for PDF + chart =====
import matplotlib
matplotlib.use("Agg")  # headless backend
import matplotlib.pyplot as plt
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader

# ================= App Init ==================
app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

RECORDINGS_DIR = os.path.join(os.path.dirname(__file__), "recordings")
os.makedirs(RECORDINGS_DIR, exist_ok=True)

# ================= Webcam + Detector ==================
_lock = threading.Lock()
_cap = None
_detector = None

_sessions = {}          # sid -> { meta... }
_sessions_lock = threading.Lock()


def _open_camera():
    """Try to open webcam with DSHOW first, then MSMF."""
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap or not cap.isOpened():
        cap = cv2.VideoCapture(0, cv2.CAP_MSMF)
    return cap


def _ensure_ready():
    """Lazy-init FER detector + camera."""
    global _cap, _detector
    if _detector is None:
        _detector = FER(mtcnn=False)
    if _cap is None or not _cap.isOpened():
        _cap = _open_camera()


def _read_frame():
    """Thread-safe read with one reopen retry."""
    global _cap
    with _lock:
        _ensure_ready()
        ok, frame = _cap.read()
        if not ok or frame is None:
            try:
                if _cap is not None:
                    _cap.release()
            except Exception:
                pass
            _cap = _open_camera()
            ok, frame = _cap.read()
        return ok, frame


# ================= Recorder Worker ==================
def _save_report(sid, meta, data):
    payload = {
        "id": sid,
        "meta": meta,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "data": data,
    }
    path = os.path.join(RECORDINGS_DIR, f"{sid}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return path


def _recorder_worker(sid, duration_s, interval_s):
    """Background worker that samples emotion and records timestamped entries."""
    start_ts = time.time()
    data = []
    meta = {
        "start_ts": start_ts,
        "duration_requested": duration_s,
        "interval_s": interval_s,
    }
    logger.info("session %s started: duration=%s interval=%s", sid, duration_s, interval_s)

    try:
        while True:
            now = time.time()
            elapsed = now - start_ts

            # stop requested?
            with _sessions_lock:
                s = _sessions.get(sid)
                if not s or s.get("stop_requested"):
                    break

            if duration_s and elapsed >= duration_s:
                break

            ok, frame = _read_frame()
            if ok and frame is not None:
                try:
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    res = _detector.top_emotion(rgb)
                    if res:
                        label, score = res
                        conf = float(score) if isinstance(score, (int, float)) else 0.0
                        label = label or "none"
                    else:
                        label, conf = "none", 0.0
                except Exception:
                    label, conf = "none", 0.0

                data.append(
                    {
                        "ts": datetime.utcnow().isoformat() + "Z",
                        "label": label,
                        "confidence": conf,
                    }
                )

            time.sleep(interval_s)
    finally:
        meta["end_ts"] = time.time()
        meta["samples"] = len(data)
        path = _save_report(sid, meta, data)
        logger.info("session %s finished: samples=%s file=%s", sid, meta["samples"], path)

        with _sessions_lock:
            if sid in _sessions:
                _sessions[sid]["status"] = "stopped"
                _sessions[sid]["report_path"] = path


# ================= Basic Routes ==================
@app.route("/health")
def health():
    return jsonify({"ok": True})


# ---- Session APIs ----
@app.route("/sessions/start", methods=["POST"])
def sessions_start():
    body = request.get_json(silent=True) or {}
    duration = float(body.get("duration", 600))
    interval = float(body.get("interval", 1.0))
    sid = uuid.uuid4().hex

    meta = {
        "id": sid,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "status": "running",
        "duration": duration,
        "interval": interval,
    }

    with _sessions_lock:
        _sessions[sid] = {**meta, "stop_requested": False}

    t = threading.Thread(target=_recorder_worker, args=(sid, duration, interval), daemon=True)
    t.start()

    return jsonify({"ok": True, "id": sid, "meta": meta}), 201


@app.route("/sessions/stop", methods=["POST"])
def sessions_stop():
    body = request.get_json(silent=True) or {}
    sid = body.get("id")
    if not sid:
        return jsonify({"ok": False, "error": "missing id"}), 400

    with _sessions_lock:
        s = _sessions.get(sid)
        if not s:
            return jsonify({"ok": False, "error": "unknown id"}), 404
        s["stop_requested"] = True

    return jsonify({"ok": True, "id": sid}), 200


@app.route("/sessions/<sid>/summary", methods=["GET"])
def sessions_summary(sid):
    """Return counts, percentages, top emotion + per-minute timeline."""
    path = os.path.join(RECORDINGS_DIR, f"{sid}.json")
    if not os.path.exists(path):
        return jsonify({"ok": False, "error": "not found"}), 404

    with open(path, "r", encoding="utf-8") as f:
        report = json.load(f)

    data = report.get("data", [])
    total = len(data)
    counts = {}
    times = []

    for r in data:
        label = r.get("label") or "none"
        counts[label] = counts.get(label, 0) + 1
        ts_str = r.get("ts")
        try:
            ts = datetime.fromisoformat(ts_str.replace("Z", ""))
            times.append(ts.timestamp())
        except Exception:
            pass

    percentages = {k: (v / total * 100.0) if total else 0.0 for k, v in counts.items()}
    top = max(counts.items(), key=lambda x: x[1])[0] if counts else "none"

    # per-minute timeline
    timeline = []
    if data and times:
        start = min(times)
        buckets = {}
        for r in data:
            try:
                ts = datetime.fromisoformat(r["ts"].replace("Z", ""))
                minute = int((ts.timestamp() - start) // 60)
            except Exception:
                minute = 0
            label = r.get("label") or "none"
            buckets.setdefault(minute, {})
            buckets[minute][label] = buckets[minute].get(label, 0) + 1

        for minute in sorted(buckets.keys()):
            timeline.append({"minute": minute, "counts": buckets[minute]})

    summary = {
        "ok": True,
        "id": sid,
        "total_samples": total,
        "counts": counts,
        "percentages": percentages,
        "top_emotion": top,
        "timeline": timeline,
    }
    return jsonify(summary)


@app.route("/sessions/<sid>/download", methods=["GET"])
def sessions_download(sid):
    path = os.path.join(RECORDINGS_DIR, f"{sid}.json")
    if os.path.exists(path):
        return send_file(path, as_attachment=True)
    return jsonify({"ok": False, "error": "not found"}), 404


# ============== PDF EXPORT (WITH GRAPH) ==============
@app.route("/sessions/<sid>/pdf", methods=["GET"])
def generate_pdf(sid):
    path = os.path.join(RECORDINGS_DIR, f"{sid}.json")
    if not os.path.exists(path):
        return jsonify({"ok": False, "error": "report not found"}), 404

    with open(path, "r", encoding="utf-8") as f:
        report = json.load(f)

    data = report.get("data", [])
    total = len(data)

    counts = {}
    for item in data:
        emo = item.get("label", "none")
        counts[emo] = counts.get(emo, 0) + 1

    if total > 0:
        percentages = {k: (v / total * 100.0) for k, v in counts.items()}
    else:
        percentages = {}
    top = max(counts, key=counts.get) if counts else "none"

    # ---- bar chart image ----
    if percentages:
        plt.figure(figsize=(4, 3))
        plt.bar(list(percentages.keys()), list(percentages.values()), color="cyan")
        plt.ylabel("%")
        plt.title("Emotion Percentage Distribution")
        img_buffer = io.BytesIO()
        plt.tight_layout()
        plt.savefig(img_buffer, format="png")
        plt.close()
        img_buffer.seek(0)
        img_reader = ImageReader(img_buffer)
    else:
        img_reader = None

    # ---- build PDF ----
    pdf_path = os.path.join(RECORDINGS_DIR, f"{sid}.pdf")
    c = canvas.Canvas(pdf_path, pagesize=A4)
    w, h = A4

    c.setFont("Helvetica-Bold", 18)
    c.drawString(70, h - 60, "Emotion Detection Report")

    c.setFont("Helvetica", 12)
    c.drawString(70, h - 100, f"Session ID: {sid}")
    c.drawString(70, h - 120, f"Total Samples: {total}")
    c.drawString(70, h - 140, f"Top Emotion: {top}")

    y = h - 180
    for emo, p in percentages.items():
        c.drawString(70, y, f"{emo}: {p:.1f}%")
        y -= 18

    if img_reader:
        c.drawImage(img_reader, 70, y - 240, width=380, height=240, preserveAspectRatio=True, mask="auto")

    c.showPage()
    c.save()

    return send_file(pdf_path, as_attachment=True)


# ================= Live Emotion + Video ==================
@app.route("/emotion")
def emotion():
    try:
        ok, frame = _read_frame()
        if not ok or frame is None:
            return jsonify({"ok": True, "emotion": "camera_error", "confidence": 0.0})

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = _detector.top_emotion(rgb)
        if not result:
            return jsonify({"ok": True, "emotion": "no_face", "confidence": 0.0})

        label, score = result
        conf = float(score) if isinstance(score, (int, float)) else 0.0
        label = label or "none"

        return jsonify({"ok": True, "emotion": label, "confidence": conf})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "emotion": "server_error", "confidence": 0.0}), 200


def _generate_frames():
    while True:
        ok, frame = _read_frame()
        if not ok or frame is None:
            continue
        ret, buf = cv2.imencode(".jpg", frame)
        if not ret:
            continue
        jpg = buf.tobytes()
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + jpg + b"\r\n"
        )


@app.route("/video_feed")
def video_feed():
    return Response(_generate_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/release")
def release():
    global _cap
    with _lock:
        try:
            if _cap is not None:
                _cap.release()
        finally:
            _cap = None
    return jsonify({"ok": True, "released": True})


# ================= Cleanup & Main ==================
def _cleanup():
    global _cap
    try:
        if _cap is not None:
            _cap.release()
    except Exception:
        pass


atexit.register(_cleanup)

if __name__ == "__main__":
    app.run(debug=True)
