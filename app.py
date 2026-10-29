import streamlit as st
import cv2
import numpy as np
import time
import sys
import os
from datetime import datetime
from collections import deque

# ─── Smart Import Resolution Hack ───────────────────────────────────────────
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
UTILS_DIR = os.path.join(CURRENT_DIR, "utils")

if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)
if os.path.exists(UTILS_DIR) and UTILS_DIR not in sys.path:
    sys.path.insert(0, UTILS_DIR)

try:
    from utils.detector import CrowdDetector
    from utils.alert_engine import AlertEngine, update_cycle_feedback, load_state
    from utils.zone_manager import ZoneManager
    from utils.analytics import AnalyticsTracker
except ModuleNotFoundError:
    from detector import CrowdDetector
    from alert_engine import AlertEngine, update_cycle_feedback, load_state
    from zone_manager import ZoneManager
    from analytics import AnalyticsTracker

# ─── Page Configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CROWDSENSE AI",
    page_icon="👁️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Theme State Controller Engine ─────────────────────────────────────────────
if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "Light UI Mode"

# Inject Sidebar Control Box First to Avoid Screen Flicker
with st.sidebar:
    st.markdown("### 🎨 INTERFACE MATRIX DESIGN")
    selected_theme = st.selectbox(
        "Select Active Engine Theme", 
        ["Light UI Mode", "Dark UI Mode"], 
        key="theme_switcher_widget"
    )
    st.session_state.theme_mode = selected_theme
    st.markdown("---")

# ─── Dual Theme CSS Engine Injector ──────────────────────────────────────────
if st.session_state.theme_mode == "Dark UI Mode":
    # 🌌 Sleek Dark Matrix Theme
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Space+Mono:wght@400;700&display=swap');

    :root {
        --bg-matrix: #04060a;
        --surface-cyber: #080d1a;
        --panel-border: #162238;
        --accent-core: #ffffff;
        --neon-cyan: #00e5ff;
        --neon-orange: #ff6b35;
        --neon-green: #39ff14;
        --neon-red: #ff0055;
        --text-primary: #f0f4f8;
        --text-muted: #52667d;
    }

    html, body, [class*="css"], .stApp {
        background-color: var(--bg-matrix) !important;
        color: var(--text-primary) !important;
        font-family: 'Space Mono', monospace !important;
    }

    #MainMenu, footer, header { visibility: hidden; }

    [data-testid="stSidebar"] {
        background: var(--surface-cyber) !important;
        border-right: 2px solid var(--panel-border) !important;
    }

    .cyber-panel {
        background: var(--surface-cyber) !important;
        border: 1px solid var(--panel-border) !important;
        border-radius: 6px !important;
        padding: 16px !important;
        margin-bottom: 16px !important;
        box-shadow: inset 0 0 15px rgba(0, 229, 255, 0.03) !important;
    }
    .cyber-panel strong { color: #ffffff !important; }

    .zone-container { border-top: 3px solid var(--neon-cyan) !important; }

    .route-card {
        background: #0d1b2a !important;
        border: 1px solid var(--panel-border) !important;
        border-left: 4px solid var(--neon-orange) !important;
        padding: 12px !important;
        margin-bottom: 10px !important;
        border-radius: 0 4px 4px 0 !important;
    }

    [data-testid="stMetric"] {
        background: #0b1224 !important;
        border: 1px solid var(--panel-border) !important;
        border-radius: 4px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.5) !important;
    }
    [data-testid="stMetricValue"] { 
        color: var(--neon-cyan) !important; 
        font-family: 'Orbitron', sans-serif !important; 
        font-weight: 700 !important;
    }
    [data-testid="stMetricLabel"] { color: var(--text-muted) !important; }

    .matrix-header {
        border-bottom: 2px solid var(--panel-border);
        padding-bottom: 10px;
        margin-bottom: 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .matrix-title {
        font-family: 'Orbitron', sans-serif;
        font-size: 1.8rem;
        font-weight: 900;
        letter-spacing: 2px;
        background: linear-gradient(90deg, #ffffff, var(--neon-cyan));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .ticker-box {
        font-size: 0.75rem;
        padding: 6px 10px;
        background: rgba(0, 229, 255, 0.05);
        border: 1px solid rgba(0, 229, 255, 0.2);
        color: var(--neon-cyan);
        border-radius: 4px;
    }

    button[data-baseweb="tab"] { color: var(--text-muted) !important; }
    button[aria-selected="true"] { color: var(--neon-cyan) !important; }

    .log-terminal {
        font-family: 'Space Mono', monospace;
        font-size: 0.8rem;
        background: #080d1a;
        color: #52667d;
        padding: 16px;
        border-radius: 6px;
        min-height: 120px;
        border: 1px solid var(--panel-border);
    }
    </style>
    """, unsafe_allow_html=True)
else:
    # ☀️ Polished Light UI Theme (With High Contrast Button Interventions)
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');

    :root {
        --bg-matrix: #f8fafc;
        --surface-cyber: #ffffff;
        --panel-border: #cbd5e1;
        --accent-core: #0f172a;
        --neon-cyan: #0284c7;
        --neon-orange: #ea580c;
        --neon-green: #16a34a;
        --neon-red: #dc2626;
        --text-primary: #0f172a;
        --text-muted: #475569;
    }

    html, body, [class*="css"], .stApp {
        background-color: var(--bg-matrix) !important;
        color: var(--text-primary) !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }

    #MainMenu, footer, header { visibility: hidden; }

    [data-testid="stMarkdownContainer"] p, 
    [data-testid="stMarkdownContainer"] h1, 
    [data-testid="stMarkdownContainer"] h2, 
    [data-testid="stMarkdownContainer"] h3,
    [data-testid="stWidgetLabel"] p,
    label {
        color: var(--text-primary) !important;
        font-weight: 600 !important;
    }

    [data-testid="stSidebar"] {
        background-color: #f1f5f9 !important;
        border-right: 1px solid var(--panel-border) !important;
    }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] h3 {
        color: #1e293b !important;
    }

    /* 🎚️ Absolute Slider Tracker Label Adjustments */
    [data-testid="stSlider"] [data-testid="stWidgetLabel"] p {
        color: #0f172a !important;
        font-weight: 700 !important;
    }
    div[data-testid="stSlider"] div,
    div[data-role="stSlider"] div,
    div[data-testid="stSlider"] span,
    div[class*="stSlider"] p {
        color: #0f172a !important;
        font-weight: 700 !important;
    }

    /* 🛑 Secondary Button Rules Override (STOP Button) */
    .stButton button {
        color: #0f172a !important;
        font-weight: 700 !important;
        background-color: #ffffff !important;
        border: 1px solid var(--panel-border) !important;
    }
    
    /* ⚡ Primary Button Deep Priority Injection Override (ENGAGE Button Fixes) */
    .stButton button[kind="primary"],
    div[data-testid="stSidebar"] .stButton button[kind="primary"],
    .stButton button[data-baseweb="button"][kind="primary"] {
        color: #ffffff !important;
        background-color: #0f172a !important;
        border: 1px solid #0f172a !important;
        font-weight: 700 !important;
    }

    .cyber-panel {
        background: var(--surface-cyber) !important;
        border: 1px solid var(--panel-border) !important;
        border-radius: 8px !important;
        padding: 16px !important;
        margin-bottom: 16px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;
    }
    .cyber-panel strong { color: var(--text-primary) !important; }

    .zone-container { border-top: 4px solid var(--neon-cyan) !important; }

    .route-card {
        background: #f8fafc !important;
        border: 1px solid var(--panel-border) !important;
        border-left: 4px solid var(--neon-orange) !important;
        padding: 14px !important;
        margin-bottom: 10px !important;
        border-radius: 4px !important;
    }

    [data-testid="stMetric"] {
        background: var(--surface-cyber) !important;
        border: 1px solid var(--panel-border) !important;
        border-radius: 8px !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05) !important;
        padding: 12px 20px !important;
    }
    [data-testid="stMetricValue"] { 
        color: var(--accent-core) !important; 
        font-family: 'Plus Jakarta Sans', sans-serif !important; 
        font-weight: 800 !important;
    }
    [data-testid="stMetricLabel"] {
        color: var(--text-muted) !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
    }

    .matrix-header {
        border-bottom: 1px solid var(--panel-border);
        padding-bottom: 14px;
        margin-bottom: 24px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .matrix-title {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 2rem;
        font-weight: 800;
        letter-spacing: -1px;
        color: var(--accent-core);
    }

    .ticker-box {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.8rem;
        font-weight: 600;
        padding: 8px 14px;
        background: #e0f2fe;
        border: 1px solid #bae6fd;
        color: #0369a1;
        border-radius: 6px;
    }

    button[data-baseweb="tab"] {
        font-weight: 700 !important;
        color: var(--text-muted) !important;
    }
    button[aria-selected="true"] {
        color: var(--accent-core) !important;
        border-bottom-color: var(--accent-core) !important;
    }

    .log-terminal {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.8rem;
        background: #0f172a;
        color: #cbd5e1;
        padding: 16px;
        border-radius: 8px;
        min-height: 120px;
    }
    </style>
    """, unsafe_allow_html=True)

# ─── Streamlit Engine Core State Management ─────────────────────────────────────
if "running" not in st.session_state:
    st.session_state.running = False
if "global_history" not in st.session_state:
    st.session_state.global_history = deque(maxlen=100)
if "alerts_log" not in st.session_state:
    st.session_state.alerts_log = deque(maxlen=30)

# Cached Object Constructors
@st.cache_resource
def get_detector(conf): return CrowdDetector(confidence=conf)
def get_alert_engine():
    # AlertEngine holds mutable per-user cooldown state, so it must stay
    # session-local (st.cache_resource would share it across all sessions).
    if "alert_engine" not in st.session_state:
        st.session_state.alert_engine = AlertEngine()
    return st.session_state.alert_engine

# ─── UI Matrix Command Header ──────────────────────────────────────────────────
st.markdown(f"""
<div class="matrix-header">
    <div>
        <div class="matrix-title">CROWDSENSE</div>
        <div style="color:var(--text-muted); font-size:0.8rem; font-weight: 700; letter-spacing:0.5px;">REAL-TIME SECURITY MATRIX</div>
    </div>
    <div class="ticker-box">SYSTEM STATUS: ONLINE | EDGE ENGINE v4.2.1</div>
</div>
""", unsafe_allow_html=True)

# ─── Sidebar Control Panel ─────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🛠️ SECURITY CORES")
    confidence = st.slider("Detection Threshold", 0.1, 0.9, 0.45, 0.05)
    
    st.markdown("---")
    st.markdown("### 🎛️ CAMERA VECTOR MAP")
    
    zones_setup = []
    zone_letters = ["A", "B", "C"]
    for i, z_name in enumerate(zone_letters):
        st.markdown(f"### 🤖 CONFIG: ZONE {z_name}")
        src_mode = st.selectbox(f"Feed Hardware Vector", ["Demo Simulation", "Webcam / Built-in", "Video Loop File"], key=f"src_mode_{i}")
        
        src_target = 0
        if src_mode == "Webcam / Built-in":
            src_target = st.number_input(f"Core Port ID Source", min_value=0, max_value=5, value=i, key=f"src_idx_{i}")
        elif src_mode == "Video Loop File":
            uploaded_file = st.file_uploader(f"Payload Video (.mp4)", type=["mp4","avi"], key=f"src_file_{i}")
            src_target = uploaded_file
            
        z_cap = st.number_input(f"Max Allocation Safety Cap", min_value=5, max_value=500, value=40, key=f"src_cap_{i}")
        zones_setup.append({"name": f"ZONE {z_name}", "mode": src_mode, "target": src_target, "capacity": z_cap})
        st.markdown("---")

    col_a, col_b = st.columns(2)
    with col_a:
        eng_start = st.button("⚡ ENGAGE", use_container_width=True, type="primary")
    with col_b:
        eng_stop = st.button("🛑 STOP", use_container_width=True)

    if eng_start:
        st.session_state.running = True
        st.session_state.alerts_log.clear()
        st.session_state.global_history.clear()
    if eng_stop:
        st.session_state.running = False

# ─── Primary System Workspace Tabs ────────────────────────────────=============
tab_matrix, tab_intel = st.tabs(["🖥️ HOLOGRAPHIC MATRIX", "📊 MATRIX TELEMETRY"])

# ──────────────────────────────────────────────────────────────────────────────
# WORKSPACE TAB 1: LIVE HOLOGRAPHIC GRID
# ──────────────────────────────────────────────────────────────────────────────
with tab_matrix:
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    g_total = m_col1.empty()
    g_status = m_col2.empty()
    g_fps = m_col3.empty()
    g_time = m_col4.empty()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    cam_col1, cam_col2, cam_col3 = st.columns(3)
    
    with cam_col1:
        st.markdown(f"<div class='cyber-panel zone-container'><strong>ZONE A FEED</strong></div>", unsafe_allow_html=True)
        view_alpha = st.empty()
        stat_alpha = st.empty()
        
    with cam_col2:
        st.markdown(f"<div class='cyber-panel zone-container'><strong>ZONE B FEED</strong></div>", unsafe_allow_html=True)
        view_bravo = st.empty()
        stat_bravo = st.empty()
        
    with cam_col3:
        st.markdown(f"<div class='cyber-panel zone-container'><strong>ZONE C FEED</strong></div>", unsafe_allow_html=True)
        view_charlie = st.empty()
        stat_charlie = st.empty()

    st.markdown("<br>", unsafe_allow_html=True)
    col_logs, col_routes = st.columns([1, 1])

    with col_logs:
        st.markdown("### 🚨 SECURITY LOG TRANSMISSIONS")
        realtime_logs_window = st.empty()

    with col_routes:
        st.markdown("### 🧭 ALTERNATE ROUTING VECTOR")
        routing_feedback_window = st.empty()

    # ─── Multi-Threaded Execution Cycle Loop ──────────────────────────────────
    if st.session_state.running:
        detector = get_detector(confidence)
        alert_engine = get_alert_engine()
        
        caps = []
        for config in zones_setup:
            if config["mode"] == "Webcam / Built-in":
                caps.append(cv2.VideoCapture(int(config["target"])))
            elif config["mode"] == "Video Loop File" and config["target"] is not None:
                import tempfile
                t_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
                t_file.write(config["target"].read())
                caps.append(cv2.VideoCapture(t_file.name))
            else:
                caps.append(None)

        frame_index = 0
        fps_tracker = deque(maxlen=20)

        while st.session_state.running:
            t_start = time.time()
            current_counts = {}
            processed_frames = []

            for idx, config in enumerate(zones_setup):
                cap_device = caps[idx]
                frame = None
                
                if cap_device is not None:
                    ret, frame = cap_device.read()
                    if not ret:
                        cap_device.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        ret, frame = cap_device.read()

                if frame is None:
                    frame = detector.generate_demo_frame(frame_index + (idx * 30))

                rendered_frame, count, _ = detector.detect(frame)
                current_counts[config["name"]] = count
                
                rendered_frame = cv2.cvtColor(rendered_frame, cv2.COLOR_BGR2RGB)
                processed_frames.append(rendered_frame)

            aggregated_sum = sum(current_counts.values())
            st.session_state.global_history.append(aggregated_sum)
            
            view_alpha.image(processed_frames[0], use_container_width=True)
            view_bravo.image(processed_frames[1], use_container_width=True)
            view_charlie.image(processed_frames[2], use_container_width=True)

            placeholders = [stat_alpha, stat_bravo, stat_charlie]

            for idx, config in enumerate(zones_setup):
                z_name = config["name"]
                count = current_counts[z_name]
                cap = config["capacity"]
                ratio = (count / cap) if cap > 0 else 0
                load_factor = min(100, int(ratio * 100))

                # Indicator uses the same inclusive engine thresholds as the
                # alerts, so bar color matches the current alert classification.
                state = load_state(ratio, alert_engine.warn_ratio, alert_engine.critical_ratio)
                color = {"critical": "var(--neon-red)", "warn": "var(--neon-orange)"}.get(state, "var(--neon-green)")

                placeholders[idx].markdown(f"""
                <div class="cyber-panel">
                    <div style="display:flex; justify-content:space-between; font-size:0.85rem; font-weight:700;">
                        <span>LOAD FACTOR:</span>
                        <span style="color:{color}; font-weight:bold;">{load_factor}%</span>
                    </div>
                    <div style="background:#e2e8f0; border-radius:4px; height:8px; width:100%; margin-top:8px;">
                        <div style="background:{color}; width:{load_factor}%; height:100%; border-radius:4px;"></div>
                    </div>
                    <div style="margin-top:10px; font-size:0.8rem; color:var(--text-muted); font-weight:700;">
                        ALLOCATION: {count} / {cap} MAX UNITS
                    </div>
                </div>
                """, unsafe_allow_html=True)


            # Alerts and routing come from the tested AlertEngine integration
            # path; the engine lives in session state, so its 5s per-key
            # cooldown persists across reruns of this session only.
            zone_names = [config["name"] for config in zones_setup]
            zone_caps = [config["capacity"] for config in zones_setup]
            suggestions = update_cycle_feedback(
                alert_engine, zone_names, zone_caps, current_counts,
                st.session_state.alerts_log)

            routes_html = ""
            if not (len(suggestions) == 1 and suggestions[0].startswith("✅")):
                for suggestion in suggestions:
                    routes_html += f"""
                    <div class="route-card">
                        <div style="font-size:0.85rem; margin-top:6px; font-weight:600;">
                            {suggestion}
                        </div>
                    </div>
                    """
            else:
                routes_html = f"""
                <div style="color:var(--text-muted); font-size:0.85rem; font-weight:700; border:1px dashed var(--panel-border); padding:20px; border-radius:8px; background: {'#ffffff' if st.session_state.theme_mode == 'Light UI Mode' else 'var(--surface-cyber)'}; text-align: center;">
                    🟢 ALL TRAFFIC ROUTES NOMINAL. Foot traffic loads remain balanced.
                </div>
                """
            routing_feedback_window.markdown(routes_html, unsafe_allow_html=True)

            fps_tracker.append(time.time() - t_start)
            current_fps = 1.0 / (sum(fps_tracker) / len(fps_tracker)) if fps_tracker else 0
            
            g_total.metric("Total Visitors", aggregated_sum)
            g_status.metric("System Status", "ACTIVE" if aggregated_sum < 100 else "HEAVY LOAD")
            g_fps.metric("Processing Velocity", f"{current_fps:.1f} FPS")
            g_time.metric("System Time", datetime.now().strftime("%H:%M:%S"))

            log_html = "<div class='log-terminal'>"
            for alert in list(st.session_state.alerts_log)[:5]:
                color = "#f87171" if alert["type"] == "crit" else "#38bdf8"
                log_html += f"<div style='margin-bottom:6px; color:{color}'>[{alert['time']}] {alert['msg']}</div>"
            if len(st.session_state.alerts_log) == 0:
                log_html += "<div style='color:#94a3b8;'>📡 STEADY LINK STATUS. NO SECURITY METRIC ANOMALIES DETECTED.</div>"
            log_html += "</div>"
            realtime_logs_window.markdown(log_html, unsafe_allow_html=True)

            frame_index += 1
            time.sleep(0.01)

        for cap_device in caps:
            if cap_device is not None: cap_device.release()

    else:
        for placeholder in [view_alpha, view_bravo, view_charlie]:
            placeholder.markdown(f"""
            <div style="background:{'#ffffff' if st.session_state.theme_mode == 'Light UI Mode' else '#060a12'}; border:1px dashed var(--panel-border); border-radius: 8px; height:200px; 
                        display:flex; align-items:center; justify-content:center; color:var(--text-muted); font-size:0.8rem; font-weight:700;">
                [ FEED TERMINATED // DECK OFFLINE ]
            </div>
            """, unsafe_allow_html=True)
        g_total.metric("Total Visitors", "OFFLINE")
        g_status.metric("System Status", "STANDBY")
        g_fps.metric("Processing Velocity", "0.0 FPS")
        g_time.metric("System Time", "--:--:--")
        routing_feedback_window.markdown(f"<div style='color:var(--text-muted); font-size:0.85rem; font-weight:700; text-align:center; border: 1px dashed var(--panel-border); background: {'white' if st.session_state.theme_mode == 'Light UI Mode' else 'var(--surface-cyber)'}; padding: 20px; border-radius: 8px;'>CORE ENGINE DISENGAGED</div>", unsafe_allow_html=True)
        realtime_logs_window.markdown("<div class='log-terminal' style='color:#94a3b8;'>📡 CORE ENGINE DISENGAGED</div>", unsafe_allow_html=True)

# ─── WORKSPACE TAB 2: ADVANCED ANALYTICS QUANT VECTOR ──────────────────────────
with tab_intel:
    st.markdown("### 📊 TEMPORAL TOTAL VISITOR DISTRIBUTION MATRIX")
    
    series_data = list(st.session_state.global_history)
    
    if len(series_data) > 1:
        import pandas as pd
        import altair as alt

        chart_dataframe = pd.DataFrame({
            "Timeline Ticks": list(range(len(series_data))), 
            "Aggregated Population": series_data
        })

        line_color = "#0284c7" if st.session_state.theme_mode == "Light UI Mode" else "#00e5ff"
        bg_color = "#ffffff" if st.session_state.theme_mode == "Light UI Mode" else "#080d1a"
        grid_color = "#f1f5f9" if st.session_state.theme_mode == "Light UI Mode" else "#162238"

        advanced_chart = alt.Chart(chart_dataframe).mark_line(
            color=line_color, 
            strokeWidth=2.5
        ).encode(
            x=alt.X("Timeline Ticks:Q", title="Timeline Ticks"),
            y=alt.Y("Aggregated Population:Q", title="Total Crowd Density")
        ).properties(
            height=320, 
            background=bg_color
        ).configure_axis(
            labelColor="#475569", 
            gridColor=grid_color, 
            titleColor="#475569",
            labelFont="Plus Jakarta Sans",
            titleFont="Plus Jakarta Sans"
        ).configure_view(
            strokeWidth=0
        )

        st.altair_chart(advanced_chart, use_container_width=True)
        
    elif len(series_data) == 1:
        st.info("📡 Telemetry data pipeline stream opened. Accumulating matrix coordinates (Waiting for index tick #2)...")
    else:
        st.markdown(f"<div style='color:var(--text-muted); background: {'white' if st.session_state.theme_mode == 'Light UI Mode' else 'var(--surface-cyber)'}; border: 1px solid var(--panel-border); padding:24px; border-radius:8px; text-align: center; font-weight:700;'>No telemetry logs compiled. Boot up multi-cam engine to record tracking histories.</div>", unsafe_allow_html=True)
