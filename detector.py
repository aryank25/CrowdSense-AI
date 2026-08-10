"""
CrowdSense AI — Crowd Detector
Uses YOLOv8 to detect people in video frames.
Falls back to a simulation mode if ultralytics is unavailable.
"""

import cv2
import numpy as np
import random
import math
from datetime import datetime

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False


class CrowdDetector:
    """
    People detector using YOLOv8n.
    Auto-downloads the model on first run.
    Falls back to demo simulation if YOLO not installed.
    """

    # COCO class index for "person"
    PERSON_CLASS = 0

    # Bounding box colors (BGR)
    COLOR_BOX = (0, 229, 255)       # Cyan
    COLOR_TEXT_BG = (0, 100, 120)
    COLOR_WARN = (0, 214, 255)
    COLOR_CRIT = (45, 45, 255)

    def __init__(self, model_name: str = "yolov8n.pt", confidence: float = 0.45):
        self.confidence = confidence
        self.model = None

        if YOLO_AVAILABLE:
            try:
                self.model = YOLO(model_name)
                print(f"[CrowdDetector] YOLOv8 loaded: {model_name}")
            except Exception as e:
                print(f"[CrowdDetector] YOLO load failed: {e}. Using demo mode.")
        else:
            print("[CrowdDetector] ultralytics not installed. Using demo mode.")

    # ── Real Detection ─────────────────────────────────────────────────────────
    def detect(self, frame: np.ndarray):
        """
        Detect people in frame.
        Returns: (annotated_frame, count, boxes)
        boxes = list of (x1, y1, x2, y2, confidence)
        """
        if self.model is None:
            return self._demo_detect(frame)

        results = self.model(
            frame,
            conf=self.confidence,
            classes=[self.PERSON_CLASS],
            verbose=False
        )

        boxes = []
        annotated = frame.copy()

        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = float(box.conf[0])
                boxes.append((x1, y1, x2, y2, conf))
                self._draw_box(annotated, x1, y1, x2, y2, conf)

        self._draw_overlay(annotated, len(boxes))
        return annotated, len(boxes), boxes

    # ── Demo / Simulation Mode ─────────────────────────────────────────────────
    def generate_demo_frame(self, frame_num: int) -> np.ndarray:
        """Generate a synthetic demo frame simulating a crowd scene."""
        h, w = 480, 640
        frame = np.zeros((h, w, 3), dtype=np.uint8)

        # Background gradient
        for y in range(h):
            val = int(12 + (y / h) * 18)
            frame[y, :] = [val, int(val * 1.2), int(val * 1.6)]

        # Grid lines (floor perspective)
        for i in range(0, w, 60):
            cv2.line(frame, (i, h // 2), (w // 2, h // 3), (20, 35, 55), 1)
        for j in range(h // 3, h, 40):
            cv2.line(frame, (0, j), (w, j), (20, 35, 55), 1)

        return frame

    def _demo_detect(self, frame: np.ndarray):
        """Simulate crowd detection with animated people."""
        annotated = frame.copy()
        h, w = frame.shape[:2]

        # Simulate varying crowd size
        t = datetime.now().timestamp()
        base = 8 + int(6 * math.sin(t * 0.3))
        count = max(2, base + random.randint(-2, 2))

        boxes = []
        for i in range(count):
            # Spread people across frame
            cx = int(w * (0.08 + 0.84 * (i / max(count - 1, 1)) + random.uniform(-0.05, 0.05)))
            cy = int(h * random.uniform(0.4, 0.85))
            bw = random.randint(30, 55)
            bh = int(bw * 2.2)
            x1, y1 = max(0, cx - bw // 2), max(0, cy - bh // 2)
            x2, y2 = min(w, cx + bw // 2), min(h, cy + bh // 2)
            conf = random.uniform(0.55, 0.98)
            boxes.append((x1, y1, x2, y2, conf))
            self._draw_box(annotated, x1, y1, x2, y2, conf)

        # Watermark
        cv2.putText(annotated, "DEMO MODE", (10, h - 12),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (60, 100, 130), 1)

        self._draw_overlay(annotated, count)
        return annotated, count, boxes

    # ── Drawing Helpers ────────────────────────────────────────────────────────
    def _draw_box(self, frame, x1, y1, x2, y2, conf):
        """Draw a person bounding box with confidence label."""
        # Box
        cv2.rectangle(frame, (x1, y1), (x2, y2), self.COLOR_BOX, 2)

        # Confidence label background
        label = f"{conf:.0%}"
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
        cv2.rectangle(frame, (x1, y1 - th - 6), (x1 + tw + 6, y1), self.COLOR_TEXT_BG, -1)
        cv2.putText(frame, label, (x1 + 3, y1 - 4),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (220, 240, 255), 1)

        # Body center dot
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        cv2.circle(frame, (cx, cy), 3, self.COLOR_BOX, -1)

    def _draw_overlay(self, frame, count):
        """Draw the HUD overlay on the frame."""
        h, w = frame.shape[:2]

        # Semi-transparent top bar
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 44), (8, 12, 20), -1)
        cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

        # Count display
        cv2.putText(frame, f"PEOPLE: {count}", (10, 28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 229, 255), 2)

        # Timestamp
        ts = datetime.now().strftime("%H:%M:%S")
        cv2.putText(frame, ts, (w - 80, 28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (100, 140, 160), 1)

        # Bottom border line
        cv2.line(frame, (0, 44), (w, 44), (30, 50, 80), 1)
