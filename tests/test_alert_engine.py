"""Check alert thresholds and cooldown without waiting for real time."""
import unittest
from unittest.mock import patch

from alert_engine import AlertEngine, update_cycle_feedback, load_state


class AlertEngineTests(unittest.TestCase):
    def test_exact_thresholds_for_overall_and_zone(self):
        cases = [(6, None), (7, "warn"), (8, "warn"), (9, "critical"),
                 (10, "critical")]
        for count, expected in cases:
            with self.subTest(count=count):
                engine = AlertEngine()
                with patch("time.time", return_value=100.):
                    alerts = engine.check(["A"], {"A": count}, [10], count, 10)
                if expected is None:
                    self.assertEqual(alerts, [])
                else:
                    self.assertEqual(len(alerts), 2)
                    self.assertEqual([a["level"] for a in alerts],
                                     [expected, expected])

    def test_cooldown_expires_at_exact_boundary(self):
        engine = AlertEngine()
        for timestamp, expected_count in [(100., 2), (104.999, 0), (105., 2)]:
            with self.subTest(timestamp=timestamp):
                with patch("time.time", return_value=timestamp):
                    alerts = engine.check(["A"], {"A": 9}, [10], 9, 10)
                self.assertEqual(len(alerts), expected_count)

    def test_cooldown_for_one_zone_does_not_suppress_another(self):
        engine = AlertEngine()
        with patch("time.time", return_value=100.):
            first = engine.check(["A", "B"], {"A": 9, "B": 0}, [10, 10], 9, 20)
            second = engine.check(["A", "B"], {"A": 0, "B": 9}, [10, 10], 9, 20)
        self.assertEqual(len(first), 1)
        self.assertIn("A:", first[0]["msg"])
        self.assertEqual(len(second), 1)
        self.assertIn("B:", second[0]["msg"])



class AppCycleIntegrationTests(unittest.TestCase):
    """Drive update_cycle_feedback - the exact function app.py wires in."""

    ZONES = ["ZONE A", "ZONE B", "ZONE C"]
    CAPS = [40, 40, 40]

    def make_log(self):
        from collections import deque
        return deque(maxlen=30)

    def test_cycle_appends_engine_alerts_to_app_log(self):
        engine = AlertEngine()
        log = self.make_log()
        counts = {"ZONE A": 37, "ZONE B": 5, "ZONE C": 5}
        with patch("time.time", return_value=1000.):
            update_cycle_feedback(engine, self.ZONES, self.CAPS, counts, log)
        # 37/40 = 0.925 >= critical: one log entry, newest first, app shape.
        self.assertEqual(len(log), 1)
        self.assertEqual(log[0]["type"], "crit")
        self.assertIn("ZONE A", log[0]["msg"])
        self.assertIn("time", log[0])

    def test_cooldown_and_dedup_semantics_across_frames(self):
        engine = AlertEngine()
        log = self.make_log()
        counts = {"ZONE A": 37, "ZONE B": 5, "ZONE C": 5}
        with patch("time.time", return_value=1000.):
            update_cycle_feedback(engine, self.ZONES, self.CAPS, counts, log)
        self.assertEqual(len(log), 1)
        with patch("time.time", return_value=1000.5):
            update_cycle_feedback(engine, self.ZONES, self.CAPS, counts, log)
        self.assertEqual(len(log), 1)  # cooldown: not re-emitted 0.5s later
        with patch("time.time", return_value=1006.):
            update_cycle_feedback(engine, self.ZONES, self.CAPS, counts, log)
        # Cooldown expired so the engine re-emits, but the message is
        # identical to the newest log entry and the consecutive-duplicate
        # guard (same rule the old inline code used) keeps the log stable.
        self.assertEqual(len(log), 1)
        # A genuinely new condition logs immediately - different engine key,
        # different message, no dedup against it.
        counts["ZONE B"] = 38
        with patch("time.time", return_value=1006.5):
            update_cycle_feedback(engine, self.ZONES, self.CAPS, counts, log)
        self.assertEqual(len(log), 2)
        self.assertIn("ZONE B", log[0]["msg"])

    def test_overall_and_warn_entries_use_warn_type(self):
        engine = AlertEngine()
        log = self.make_log()
        counts = {"ZONE A": 30, "ZONE B": 30, "ZONE C": 30}
        with patch("time.time", return_value=2000.):
            update_cycle_feedback(engine, self.ZONES, self.CAPS, counts, log)
        self.assertEqual(len(log), 4)  # 3 zone warns + 1 overall warn
        self.assertTrue(all(entry["type"] == "warn" for entry in log))
        self.assertTrue(any("OVERALL" in entry["msg"] for entry in log))

    def test_exact_boundary_now_alerts(self):
        # Pins a deliberate behavior change: the old inline app logic compared
        # a truncated integer percent with >, so exactly 70% stayed green;
        # the engine compares the raw ratio with >=, so 28/40 warns.
        engine = AlertEngine()
        log = self.make_log()
        counts = {"ZONE A": 28, "ZONE B": 0, "ZONE C": 0}
        with patch("time.time", return_value=3000.):
            update_cycle_feedback(engine, self.ZONES, self.CAPS, counts, log)
        self.assertEqual(len(log), 1)
        self.assertEqual(log[0]["type"], "warn")

    def test_routing_suggestions_returned_for_overload(self):
        engine = AlertEngine()
        log = self.make_log()
        counts = {"ZONE A": 37, "ZONE B": 10, "ZONE C": 5}
        with patch("time.time", return_value=4000.):
            suggestions = update_cycle_feedback(engine, self.ZONES, self.CAPS, counts, log)
        self.assertTrue(any("ZONE A" in s and "ZONE C" in s for s in suggestions))

    def test_routing_all_clear_drives_nominal_card(self):
        engine = AlertEngine()
        log = self.make_log()
        counts = {"ZONE A": 5, "ZONE B": 5, "ZONE C": 5}
        with patch("time.time", return_value=5000.):
            suggestions = update_cycle_feedback(engine, self.ZONES, self.CAPS, counts, log)
        # app.py shows the ALL ROUTES NOMINAL card exactly in this case.
        self.assertEqual(len(suggestions), 1)
        self.assertTrue(suggestions[0].startswith("✅"))
        self.assertEqual(len(log), 0)
    def test_escalation_bypasses_cooldown_and_logs_immediately(self):
        # A zone going warn -> critical must not wait for the cooldown window;
        # the old inline code logged a newly critical zone at once.
        engine = AlertEngine()
        log = self.make_log()
        counts = {"ZONE A": 28, "ZONE B": 0, "ZONE C": 0}
        with patch("time.time", return_value=1000.):
            update_cycle_feedback(engine, self.ZONES, self.CAPS, counts, log)
        self.assertEqual(log[0]["type"], "warn")
        counts["ZONE A"] = 38
        with patch("time.time", return_value=1000.5):
            update_cycle_feedback(engine, self.ZONES, self.CAPS, counts, log)
        self.assertEqual(len(log), 2)  # critical fires immediately
        self.assertEqual(log[0]["type"], "crit")
        # Repeats stay throttled afterwards.
        with patch("time.time", return_value=1001.):
            update_cycle_feedback(engine, self.ZONES, self.CAPS, counts, log)
        self.assertEqual(len(log), 2)

    def test_deescalation_stays_throttled(self):
        engine = AlertEngine()
        log = self.make_log()
        counts = {"ZONE A": 38, "ZONE B": 0, "ZONE C": 0}
        with patch("time.time", return_value=1000.):
            update_cycle_feedback(engine, self.ZONES, self.CAPS, counts, log)
        self.assertEqual(log[0]["type"], "crit")
        counts["ZONE A"] = 28
        with patch("time.time", return_value=1000.5):
            update_cycle_feedback(engine, self.ZONES, self.CAPS, counts, log)
        self.assertEqual(len(log), 1)  # crit -> warn inside window: suppressed
        with patch("time.time", return_value=1006.):
            update_cycle_feedback(engine, self.ZONES, self.CAPS, counts, log)
        self.assertEqual(len(log), 2)
        self.assertEqual(log[0]["type"], "warn")

    def test_multiple_active_zones_relog_after_cooldown(self):
        # The consecutive-duplicate guard compares only the newest entry, so
        # with two zones alerting, both re-log after each cooldown window.
        engine = AlertEngine()
        log = self.make_log()
        counts = {"ZONE A": 38, "ZONE B": 38, "ZONE C": 0}
        with patch("time.time", return_value=1000.):
            update_cycle_feedback(engine, self.ZONES, self.CAPS, counts, log)
        self.assertEqual(len(log), 2)
        with patch("time.time", return_value=1001.):
            update_cycle_feedback(engine, self.ZONES, self.CAPS, counts, log)
        self.assertEqual(len(log), 2)  # inside window: nothing new
        with patch("time.time", return_value=1006.):
            update_cycle_feedback(engine, self.ZONES, self.CAPS, counts, log)
        self.assertEqual(len(log), 4)  # after window: both re-log, fresh times


class LoadStateTests(unittest.TestCase):
    """Display classification matches engine alert thresholds at boundaries."""

    def test_boundaries_and_nearby_ratios(self):
        cases = [(0.0, "normal"), (0.69, "normal"), (0.70, "warn"),
                 (0.705, "warn"), (0.89, "warn"), (0.90, "critical"),
                 (0.95, "critical"), (1.2, "critical")]
        for ratio, expected in cases:
            with self.subTest(ratio=ratio):
                self.assertEqual(load_state(ratio), expected)


if __name__ == "__main__":
    unittest.main()
