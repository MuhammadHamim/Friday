"""
Thread-safe in-memory world map.

Objects are identified as  label_N  (e.g. cup_1, cup_2) and tracked across
frames using IoU matching.  Session-scoped: cleared on program exit.
"""

import threading
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from config import WORLD_MAP_IOU_THRESHOLD, WORLD_MAP_STALE_SECONDS


# ── Data model ────────────────────────────────────────────────────────────────

@dataclass
class TrackedObject:
    id:         str                    # "cup_1", "pen_2", …
    label:      str                    # COCO class name
    bbox:       List[float]            # [x1, y1, x2, y2] in pixels
    confidence: float
    centroid:   Tuple[float, float]    # (cx, cy) in pixels
    area:       float                  # bounding-box area in pixels²
    last_seen:  float                  # Unix timestamp (time.time())


# ── World map ─────────────────────────────────────────────────────────────────

class WorldMap:
    """
    Tracks detected objects within the current camera session.

    Thread safety: all public methods acquire `_lock` (RLock).
    IDs are stable within a session; counter resets on `clear()`.
    """

    def __init__(self) -> None:
        self._lock:           threading.RLock    = threading.RLock()
        self._objects:        Dict[str, TrackedObject] = {}
        self._label_counters: Dict[str, int]          = {}

    # ── Public API ────────────────────────────────────────────────────────────

    def update(self, detections: List[dict]) -> None:
        """
        Merge one frame's detections into the map.

        detections: [{"label": str, "bbox": [x1,y1,x2,y2], "confidence": float}, …]
        """
        now = time.time()
        with self._lock:
            for det in detections:
                best_id = self._match(det["bbox"], det["label"])
                if best_id:
                    obj             = self._objects[best_id]
                    obj.bbox        = det["bbox"]
                    obj.confidence  = det["confidence"]
                    obj.centroid    = _centroid(det["bbox"])
                    obj.area        = _area(det["bbox"])
                    obj.last_seen   = now
                else:
                    new_id = self._mint_id(det["label"])
                    self._objects[new_id] = TrackedObject(
                        id         = new_id,
                        label      = det["label"],
                        bbox       = det["bbox"],
                        confidence = det["confidence"],
                        centroid   = _centroid(det["bbox"]),
                        area       = _area(det["bbox"]),
                        last_seen  = now,
                    )

            # Evict objects not seen within the stale window
            stale = [
                oid for oid, obj in self._objects.items()
                if now - obj.last_seen > WORLD_MAP_STALE_SECONDS
            ]
            for oid in stale:
                del self._objects[oid]

    def get_snapshot(self) -> Dict[str, TrackedObject]:
        """Return a shallow copy of the current object dict (thread-safe read)."""
        with self._lock:
            return dict(self._objects)

    def find(self, label: str) -> List[TrackedObject]:
        """Return all tracked objects whose label matches (e.g. all 'cup' objects)."""
        with self._lock:
            return [o for o in self._objects.values() if o.label == label]

    def clear(self) -> None:
        """Reset the map and ID counters. Called on program shutdown."""
        with self._lock:
            self._objects.clear()
            self._label_counters.clear()

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _mint_id(self, label: str) -> str:
        self._label_counters[label] = self._label_counters.get(label, 0) + 1
        return f"{label}_{self._label_counters[label]}"

    def _match(self, bbox: List[float], label: str) -> Optional[str]:
        """Return the ID of the existing object with highest IoU, or None."""
        best_id, best_iou = None, 0.0
        for oid, obj in self._objects.items():
            if obj.label != label:
                continue
            iou = _iou(bbox, obj.bbox)
            if iou > best_iou:
                best_iou, best_id = iou, oid
        return best_id if best_iou >= WORLD_MAP_IOU_THRESHOLD else None


# ── Module-level geometry helpers (also used by camera_node) ──────────────────

def _centroid(bbox: List[float]) -> Tuple[float, float]:
    x1, y1, x2, y2 = bbox
    return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)


def _area(bbox: List[float]) -> float:
    x1, y1, x2, y2 = bbox
    return max(0.0, x2 - x1) * max(0.0, y2 - y1)


def _iou(a: List[float], b: List[float]) -> float:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    inter = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)
    if inter == 0.0:
        return 0.0
    union = (ax2 - ax1) * (ay2 - ay1) + (bx2 - bx1) * (by2 - by1) - inter
    return inter / union if union > 0.0 else 0.0
