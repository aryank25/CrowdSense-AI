"""Deterministic checks for frame zones and count-only fallback."""
import random
import unittest
from unittest.mock import patch

from zone_manager import ZoneManager


class ZoneManagerTests(unittest.TestCase):
    def setUp(self):
        self.manager = ZoneManager()
        self.manager.setup_zones(["A", "B", "C"], [10, 20, 30])

    def test_no_zones_returns_no_counts(self):
        self.assertEqual(ZoneManager().distribute(5, [], (100, 300, 3)), {})

    def test_box_centers_at_boundaries_enter_zone_on_right(self):
        # Width 300 gives boundaries at x=100 and x=200.
        boxes = [(0, 0, 20, 20, .9), (90, 0, 110, 20, .9),
                 (190, 0, 210, 20, .9), (290, 0, 310, 20, .9)]
        counts = self.manager.distribute(4, boxes, (100, 300, 3))
        self.assertEqual(counts, {"A": 1, "B": 1, "C": 2})

    def test_count_only_fallback_conserves_total_and_is_nonnegative(self):
        # Use a local generator so this test does not change global RNG state.
        rng = random.Random(17)
        with patch("random.randint", side_effect=rng.randint):
            for total in [0, 1, 2, 7, 60, 101]:
                with self.subTest(total=total):
                    counts = self.manager.distribute(total, [], (100, 300, 3))
                    self.assertEqual(sum(counts.values()), total)
                    self.assertTrue(all(count >= 0 for count in counts.values()))
                    self.assertEqual(set(counts), {"A", "B", "C"})

    def test_boundaries_cover_width_without_gaps(self):
        for width in [300, 301]:
            with self.subTest(width=width):
                boundaries = self.manager.get_zone_boundaries(width)
                self.assertEqual(boundaries[0][0], 0)
                self.assertEqual(boundaries[-1][1], width)
                self.assertEqual([end for _, end in boundaries[:-1]],
                                 [start for start, _ in boundaries[1:]])


if __name__ == "__main__":
    unittest.main()
