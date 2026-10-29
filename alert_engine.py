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
        self._cooldown: Dict[str, Tuple[float, str]] = {}   # key → (last alert time, level)
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
            if self._can_alert(overall_key, now, "critical"):
                alerts.append({
                    "level": "critical",
                    "msg": f"OVERALL CRITICAL — {total_count}/{total_cap} people detected! Immediate action required.",
                    "time": now_ts,
                })
                self._cooldown[overall_key] = (now, "critical")
        elif total_count >= total_cap * self.warn_ratio:
            if self._can_alert(overall_key, now, "warn"):
                alerts.append({
                    "level": "warn",
                    "msg": f"OVERALL WARNING — {total_count}/{total_cap} people. Approaching capacity.",
                    "time": now_ts,
                })
                self._cooldown[overall_key] = (now, "warn")

        # Per-zone checks
        for name, cap in zip(zone_names, zone_caps):
            count = zone_counts.get(name, 0)
            ratio = count / cap if cap > 0 else 0
            key = f"zone_{name}"

            if ratio >= self.critical_ratio:
                if self._can_alert(key, now, "critical"):
                    alerts.append({
                        "level": "critical",
                        "msg": f"{name}: {count}/{cap} people — CRITICAL DENSITY. Redirect immediately!",
                        "time": now_ts,
                    })
                    self._cooldown[key] = (now, "critical")
            elif ratio >= self.warn_ratio:
                if self._can_alert(key, now, "warn"):
                    alerts.append({
                        "level": "warn",
                        "msg": f"{name}: {count}/{cap} people — High density warning.",
                        "time": now_ts,
                    })
                    self._cooldown[key] = (now, "warn")

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
    _SEVERITY = {"info": 0, "warn": 1, "critical": 2}

    def _can_alert(self, key: str, now: float, level: str) -> bool:
        last = self._cooldown.get(key)
        if last is None:
            return True
        last_t, last_level = last
        if now - last_t >= self._cooldown_secs:
            return True
        # A more severe condition (e.g. warn -> critical) fires immediately;
        # repeats and de-escalations stay throttled.
        return self._SEVERITY[level] > self._SEVERITY[last_level]


def update_cycle_feedback(engine: AlertEngine, zone_names: List[str],
                          zone_caps: List[int], current_counts: Dict[str, int],
                          alerts_log) -> List[str]:
    """Run one monitoring cycle of alert and routing feedback.

    This is the exact path app.py wires into its monitoring loop: new engine
    alerts are appended to alerts_log (newest first, consecutive-duplicate
    suppressed) and the engine's routing suggestions for the cycle are
    returned. The engine instance owns cooldown state; app.py keeps it in
    st.session_state so cooldowns persist across reruns of one session and
    are never shared between sessions.
    """
    total_count = sum(current_counts.values())
    total_cap = sum(zone_caps)
    for alert in engine.check(zone_names, current_counts, zone_caps,
                              total_count, total_cap):
        if not alerts_log or alerts_log[0]["msg"] != alert["msg"]:
            alerts_log.appendleft({
                "time": alert["time"],
                "msg": alert["msg"],
                "type": "crit" if alert["level"] == "critical" else "warn",
            })
    return engine.suggest(zone_names, current_counts, zone_caps,
                          total_count, total_cap)


def load_state(ratio: float, warn_ratio: float = 0.70,
               critical_ratio: float = 0.90) -> str:
    """Classify a zone load ratio for display.

    Uses the same inclusive thresholds as alert classification: a zone at or
    above warn_ratio shows the warn color whenever the zone is in the warn
    band. The alert log is a throttled history, so its entries need not
    reflect the current bar color.
    """
    if ratio >= critical_ratio:
        return "critical"
    if ratio >= warn_ratio:
        return "warn"
    return "normal"
