# 👁️ CrowdSense AI — Real-Time Crowd Monitoring System

> AI-powered crowd monitoring using YOLOv8 + Streamlit. Works with webcams, CCTV/RTSP streams, video files, and demo mode.

![Python](https://img.shields.io/badge/Python-3.9+-blue) ![YOLOv8](https://img.shields.io/badge/YOLO-v8-green) ![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-red)

---

## 🚀 Features

| Feature | Description |
|---|---|
| 🎯 **YOLOv8 Detection** | State-of-the-art real-time person detection |
| 📡 **Multi-Source Input** | Webcam, RTSP/IP camera, video file, demo mode |
| 🗺️ **Zone Management** | Up to 6 configurable spatial zones |
| 🚨 **3-Tier Alerts** | Info → Warning → Critical threshold system |
| 💡 **AI Suggestions** | Intelligent crowd redistribution recommendations |
| 📊 **Live Analytics** | Real-time count history, FPS, density charts |
| 🌙 **Dark UI** | Industrial dark theme with neon accents |

---

## 🛠️ Installation

```bash
# 1. Clone or extract this folder
cd crowd_monitor

# 2. Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run
streamlit run app.py
```

The YOLOv8 model (`yolov8n.pt`, ~6 MB) downloads automatically on first run.

---

## 📷 Supported Camera Sources

### Webcam
- Built-in laptop camera → index `0`
- USB camera → try index `1`, `2`, etc.

### RTSP / IP / CCTV Camera
```
rtsp://username:password@192.168.1.100:554/stream
rtsp://admin:12345@192.168.1.100:554/Streaming/Channels/101
rtsp://192.168.1.100/live.sdp
```

### Video File
- Upload `.mp4`, `.avi`, `.mov`, `.mkv` via the sidebar

### Demo Mode
- Fully simulated crowd scene — no camera needed

---

## ⚙️ Configuration

| Parameter | Default | Description |
|---|---|---|
| Confidence | 0.45 | YOLO detection confidence (0.1–0.9) |
| Zone Capacity | 50 | Max people per zone |
| Warning Threshold | 70% | % of capacity to trigger warning |
| Critical Threshold | 90% | % of capacity to trigger critical alert |
| Num Zones | 3 | Number of monitoring zones (1–6) |

---

## 🧠 How Zone Distribution Works

The camera frame is divided into N equal horizontal strips.  
Each detected person's bounding box center X-position determines their zone.

```
Frame Width
├── Zone A (0 – 33%)
├── Zone B (33 – 66%)
└── Zone C (66 – 100%)
```

---

## 📊 Alert Levels

| Level | Trigger | Action |
|---|---|---|
| ✅ Info | < 70% capacity | Normal monitoring |
| ⚠️ Warning | 70–90% capacity | Prepare for redirection |
| 🚨 Critical | > 90% capacity | Immediate action required |

---

## 🗂️ Project Structure

```
crowd_monitor/
├── app.py                  ← Main Streamlit application
├── requirements.txt
├── .streamlit/
│   └── config.toml         ← Dark theme config
└── utils/
    ├── detector.py         ← YOLOv8 people detector
    ├── alert_engine.py     ← Alert + suggestion logic
    ├── zone_manager.py     ← Spatial zone distribution
    └── analytics.py        ← Time-series tracking
```

---

## Run the logic tests

From the repository root, after installing the requirements:

```bash
python -m unittest discover -s tests -v
```

These tests check zone assignment, count conservation, alert thresholds and
cooldown timing. They do not open cameras, download YOLO weights or start
Streamlit. They test the standalone logic modules, not the separate threshold
logic currently implemented in `app.py`.

---

## 🔧 GPU Acceleration

For high-resolution or multi-camera setups, GPU is recommended:

```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

YOLO automatically uses CUDA if available.

---

## 📸 Screenshots

Launch the app and switch to **Demo Mode** to see the system in action without a camera.

---

## 📄 License

MIT — free for commercial and personal use.


CrowdSense AI is developed collaboratively by Abhishek Gaurav, Aryan Kumar and Ishan Gupta as part of our DTL project, combining our contributions to the design, development, and implementation to the project.
