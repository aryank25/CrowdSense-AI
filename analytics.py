"""
CrowdSense AI — Analytics Tracker
Tracks crowd metrics over time for reporting and visualization.
"""

from collections import deque
from datetime import datetime
from typing import Dict, List, Optional
import json


class AnalyticsTracker:
    """
    Stores time-series crowd data and computes summary statistics.
    """

    def __init__(self, max_history: int = 3600):
        self.max_history = max_history
        self.history: deque = deque(maxlen=max_history)
        self.zone_history: Dict[str, deque] = {}
        self.alert_log: List[Dict] = []
        self.session_start = datetime.now()

    def record(self, total_count: int, zone_counts: Dict[str, int]):
        entry = {
            "ts": datetime.now().isoformat(),
            "count": total_count,
            "zones": zone_counts.copy(),
        }
        self.history.append(entry)
        for name, count in zone_counts.items():
            if name not in self.zone_history:
                self.zone_history[name] = deque(maxlen=self.max_history)
            self.zone_history[name].append(count)

    def log_alert(self, alert: Dict):
        self.alert_log.append(alert)

    # ── Stats ──────────────────────────────────────────────────────────────────
    @property
    def count_series(self) -> List[int]:
        return [e["count"] for e in self.history]

    @property
    def peak(self) -> int:
        s = self.count_series
        return max(s) if s else 0

    @property
    def average(self) -> float:
        s = self.count_series
        return sum(s) / len(s) if s else 0.0

    @property
    def session_duration(self) -> str:
        delta = datetime.now() - self.session_start
        mins, secs = divmod(int(delta.total_seconds()), 60)
        return f"{mins:02d}:{secs:02d}"

    def export_json(self) -> str:
        return json.dumps({
            "session_start": self.session_start.isoformat(),
            "total_frames": len(self.history),
            "peak": self.peak,
            "average": round(self.average, 2),
            "history": list(self.history)[-100:],  # last 100 entries
            "alerts": self.alert_log[-50:],
        }, indent=2)
