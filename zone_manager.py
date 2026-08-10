"""
CrowdSense AI — Zone Manager
Distributes detected people across defined spatial zones
based on bounding box position in the frame.
"""

from typing import List, Dict, Tuple, Optional
import numpy as np


class ZoneManager:
    """
    Divides the camera frame into N horizontal zones and assigns
    each detected person to a zone based on their bounding box center.

    If no bounding box data is available (demo total-count-only mode),
    uses proportional random distribution instead.
    """

    def __init__(self):
        self.zones: List[str] = []
        self.capacities: List[int] = []

    def setup_zones(self, names: List[str], capacities: List[int]):
        self.zones = names
        self.capacities = capacities

    def distribute(
        self,
        total_count: int,
        boxes: List[Tuple],
        frame_shape: Tuple[int, int, int],
    ) -> Dict[str, int]:
        """
        Assign people to zones.

        Args:
            total_count: Total number of people detected.
            boxes: List of (x1, y1, x2, y2, conf) bounding boxes.
            frame_shape: (height, width, channels)

        Returns:
            Dict mapping zone_name → count
        """
        if not self.zones:
            return {}

        n = len(self.zones)
        counts = {name: 0 for name in self.zones}

        if boxes:
            # Assign each box to a zone based on center X position
            h, w = frame_shape[:2]
            zone_width = w / n

            for (x1, y1, x2, y2, *_) in boxes:
                cx = (x1 + x2) / 2
                zone_idx = min(int(cx / zone_width), n - 1)
                counts[self.zones[zone_idx]] += 1
        else:
            # No box data — distribute proportionally using weighted random
            counts = self._proportional_distribute(total_count)

        return counts

    def _proportional_distribute(self, total: int) -> Dict[str, int]:
        """
        Distribute total count across zones proportionally,
        weighted by capacity so larger zones get more.
        """
        if not self.zones:
            return {}

        import random
        n = len(self.zones)
        counts = {name: 0 for name in self.zones}

        if total == 0:
            return counts

        # Capacity-weighted distribution
        total_cap = sum(self.capacities) or 1
        remaining = total
        for i, (name, cap) in enumerate(zip(self.zones, self.capacities)):
            if i == n - 1:
                counts[name] = remaining
            else:
                weight = cap / total_cap
                zone_count = min(remaining, max(0, int(total * weight + random.randint(-1, 1))))
                counts[name] = zone_count
                remaining -= zone_count

        return counts

    def get_zone_boundaries(self, frame_width: int) -> List[Tuple[int, int]]:
        """Return pixel X boundaries for each zone."""
        n = len(self.zones)
        if n == 0:
            return []
        zone_w = frame_width / n
        return [(int(i * zone_w), int((i + 1) * zone_w)) for i in range(n)]

    def draw_zones(self, frame: np.ndarray) -> np.ndarray:
        """
        Overlay zone dividers on the frame (optional visualization).
        """
        import cv2
        h, w = frame.shape[:2]
        n = len(self.zones)
        zone_w = w // n

        for i, name in enumerate(self.zones):
            x = i * zone_w
            # Divider line
            if i > 0:
                cv2.line(frame, (x, 0), (x, h), (30, 60, 100), 1)
            # Zone label
            cv2.putText(frame, name, (x + 5, h - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (60, 120, 160), 1)

        return frame
