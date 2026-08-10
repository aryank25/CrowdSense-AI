"""
CrowdSense AI — Alert Engine
3-tier alerting system with intelligent crowd suggestions.
"""

from datetime import datetime
from typing import List, Dict, Tuple


class AlertEngine:
    """
    Monitors crowd counts against thresholds and generates:
      - Alerts (critical / warn / info)
      - AI-powered zone redistribution suggestions
    """

    def __init__(self, warn_ratio: float = 0.70, critical_ratio: float = 0.90):
        self.warn_ratio = warn_ratio
        self.critical_ratio = critical_ratio
        self._cooldown: Dict[str, float] = {}   # key → last alert time
        self._cooldown_secs = 5.0

    # ── Alert Checking ─────────────────────────────────────────────────────────
    def check(
        self,
        zone_names: List[str],
        zone_counts: Dict[str, int],
        zone_caps: List[int],
        total_count: int,
        total_cap: int,
    ) -> List[Dict]:
        """
        Generate alerts for each zone and for the overall area.
        Returns a list of alert dicts: {level, msg, time}
        """
        now_ts = datetime.now().strftime("%H:%M:%S")
        import time
        now = time.time()
        alerts = []

        # Overall capacity check
        overall_key = "__overall__"
        if total_count >= total_cap * self.critical_ratio:
            if self._can_alert(overall_key, now):
                alerts.append({
                    "level": "critical",
                    "msg": f"OVERALL CRITICAL — {total_count}/{total_cap} people detected! Immediate action required.",
                    "time": now_ts,
                })
                self._cooldown[overall_key] = now
        elif total_count >= total_cap * self.warn_ratio:
            if self._can_alert(overall_key, now):
                alerts.append({
                    "level": "warn",
                    "msg": f"OVERALL WARNING — {total_count}/{total_cap} people. Approaching capacity.",
                    "time": now_ts,
                })
                self._cooldown[overall_key] = now

        # Per-zone checks
        for name, cap in zip(zone_names, zone_caps):
            count = zone_counts.get(name, 0)
            ratio = count / cap if cap > 0 else 0
            key = f"zone_{name}"

            if ratio >= self.critical_ratio:
                if self._can_alert(key, now):
                    alerts.append({
                        "level": "critical",
                        "msg": f"{name}: {count}/{cap} people — CRITICAL DENSITY. Redirect immediately!",
                        "time": now_ts,
                    })
                    self._cooldown[key] = now
            elif ratio >= self.warn_ratio:
                if self._can_alert(key, now):
                    alerts.append({
                        "level": "warn",
                        "msg": f"{name}: {count}/{cap} people — High density warning.",
                        "time": now_ts,
                    })
                    self._cooldown[key] = now

        return alerts

    # ── Suggestion Engine ──────────────────────────────────────────────────────
    def suggest(
        self,
        zone_names: List[str],
        zone_counts: Dict[str, int],
        zone_caps: List[int],
        total_count: int,
        total_cap: int,
    ) -> List[str]:
        """
        Generate intelligent crowd management suggestions based on
        current zone densities.
        """
        suggestions = []

        ratios = {}
        for name, cap in zip(zone_names, zone_caps):
            count = zone_counts.get(name, 0)
            ratios[name] = (count / cap if cap > 0 else 0, count, cap)

        # Find overcrowded and underutilized zones
        overcrowded = [(n, r, c, cap) for n, (r, c, cap) in ratios.items() if r >= self.warn_ratio]
        underused = [(n, r, c, cap) for n, (r, c, cap) in ratios.items() if r < 0.4]
        safe = [(n, r, c, cap) for n, (r, c, cap) in ratios.items() if 0.4 <= r < self.warn_ratio]

        # Sort
        overcrowded.sort(key=lambda x: x[1], reverse=True)
        underused.sort(key=lambda x: x[1])

        # Redirect suggestions
        for (oc_name, oc_r, oc_c, oc_cap) in overcrowded:
            if underused:
                target_name, _, _, target_cap = underused[0]
                redirect_count = min(oc_c - int(oc_cap * 0.6), 10)
                suggestions.append(
                    f"<strong>Redirect {redirect_count} people</strong> from "
                    f"<em>{oc_name}</em> ({int(oc_r*100)}% full) to "
                    f"<em>{target_name}</em> — significant capacity available."
                )
            elif safe:
                target_name = safe[0][0]
                suggestions.append(
                    f"Guide visitors from <em>{oc_name}</em> toward <em>{target_name}</em> "
                    f"to balance crowd distribution."
                )

        # Open more gates / staff suggestion
        if any(r >= self.critical_ratio for _, (r, _, _) in ratios.items()):
            suggestions.append(
                "🚪 <strong>Consider opening additional entry/exit points</strong> "
                "to accelerate crowd dispersal in critical zones."
            )

        # PA announcement suggestion
        if len(overcrowded) >= 2:
            zones_str = " and ".join(f"<em>{n}</em>" for n, *_ in overcrowded[:2])
            suggestions.append(
                f"📢 Issue a <strong>PA announcement</strong> directing visitors away from {zones_str}."
            )

        # Emergency if overall critical
        total_ratio = total_count / total_cap if total_cap > 0 else 0
        if total_ratio >= self.critical_ratio:
            suggestions.insert(0,
                "🚨 <strong>Emergency Protocol</strong> — Total capacity exceeded. "
                "Alert security staff and consider temporary entry suspension."
            )

        # All clear
        if not overcrowded and total_ratio < self.warn_ratio:
            suggestions.append(
                "✅ Crowd levels are well-distributed. No immediate action required. "
                "Continue monitoring."
            )

        return suggestions[:4]

    # ── Helpers ────────────────────────────────────────────────────────────────
    def _can_alert(self, key: str, now: float) -> bool:
        last = self._cooldown.get(key, 0)
        return (now - last) >= self._cooldown_secs
