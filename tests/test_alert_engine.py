"""Check alert thresholds and cooldown without waiting for real time."""
import unittest
from unittest.mock import patch

from alert_engine import AlertEngine


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


if __name__ == "__main__":
    unittest.main()
