"""
Camera node: background daemon thread.

Responsibilities:
  - Capture frames from the Logitech webcam
  - Run YOLO inference on every frame
  - Push detections into the WorldMap
  - Render an annotated OpenCV window (bounding boxes, tracked IDs, FPS HUD)
"""

import threading
import time
from typing import TYPE_CHECKING, Optional

import cv2

from vision.world_map import WorldMap, _iou
from config import CAMERA_INDEX, CAMERA_WIDTH, CAMERA_HEIGHT, CAMERA_FPS

if TYPE_CHECKING:
    from vision.yolo_engine import YOLOEngine

# ── Display constants ─────────────────────────────────────────────────────────
_WINDOW    = "Friday — World View"
_BOX_COLOR = (0, 220, 80)         # green  ─ bounding boxes & label bg
_HUD_COLOR = (0, 190, 255)        # amber  ─ FPS / object count overlay
_FONT      = cv2.FONT_HERSHEY_SIMPLEX


class CameraNode:
    """
    Runs YOLO + WorldMap updates on a daemon thread.
    Call start() once after construction; call stop() on shutdown.
    """

    def __init__(self, world_map: WorldMap, yolo: "YOLOEngine") -> None:
        self._world_map = world_map
        self._yolo      = yolo
        self._stop      = threading.Event()
        self._thread    = threading.Thread(
            target=self._run, name="CameraNode", daemon=True
        )

    def start(self) -> None:
        self._thread.start()
        print("[Vision] Camera node started.")

    def stop(self) -> None:
        self._stop.set()
        self._thread.join(timeout=5.0)
        cv2.destroyAllWindows()

    # ── Main capture loop ─────────────────────────────────────────────────────

    def _run(self) -> None:
        # CAP_DSHOW avoids Logitech camera negotiation delays on Windows
        cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH,  CAMERA_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
        cap.set(cv2.CAP_PROP_FPS,          CAMERA_FPS)

        if not cap.isOpened():
            print(
                f"[Vision] ERROR: Cannot open camera index {CAMERA_INDEX}. "
                "Check CAMERA_INDEX in config.py or try index 1."
            )
            return

        cv2.namedWindow(_WINDOW, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(_WINDOW, CAMERA_WIDTH, CAMERA_HEIGHT)

        fps_timer  = time.perf_counter()
        fps_frames = 0
        fps_display = 0.0

        while not self._stop.is_set():
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.02)
                continue

            # Inference + world map update
            detections = self._yolo.detect(frame)
            self._world_map.update(detections)

            # Render and display
            snapshot  = self._world_map.get_snapshot()
            annotated = _annotate(frame, detections, snapshot, fps_display)
            cv2.imshow(_WINDOW, annotated)

            # 'q' in the OpenCV window signals a clean shutdown
            if cv2.waitKey(1) & 0xFF == ord("q"):
                self._stop.set()
                break

            # Rolling FPS measurement
            fps_frames += 1
            elapsed = time.perf_counter() - fps_timer
            if elapsed >= 1.0:
                fps_display = fps_frames / elapsed
                fps_frames  = 0
                fps_timer   = time.perf_counter()

        cap.release()
        cv2.destroyAllWindows()


# ── Frame annotation (pure function, no side effects) ─────────────────────────

def _annotate(frame, detections: list, snapshot: dict, fps: float):
    """Draw bounding boxes, tracked IDs, confidence scores, and HUD onto frame."""
    for det in detections:
        x1, y1, x2, y2 = (int(v) for v in det["bbox"])
        label           = det["label"]
        conf            = det["confidence"]
        tracked_id      = _resolve_tracked_id(snapshot, det["bbox"], label)
        caption         = f"{tracked_id}  {conf:.2f}" if tracked_id else f"{label}  {conf:.2f}"

        # Bounding box
        cv2.rectangle(frame, (x1, y1), (x2, y2), _BOX_COLOR, 2)

        # Label background + text
        (tw, th), _ = cv2.getTextSize(caption, _FONT, 0.55, 2)
        cv2.rectangle(frame, (x1, y1 - th - 8), (x1 + tw + 6, y1), _BOX_COLOR, -1)
        cv2.putText(frame, caption, (x1 + 3, y1 - 4), _FONT, 0.55, (0, 0, 0), 2)

    # HUD — FPS and total tracked objects
    cv2.putText(frame, f"FPS: {fps:.1f}",         (10, 30), _FONT, 0.9,  _HUD_COLOR, 2)
    cv2.putText(frame, f"Objects: {len(snapshot)}", (10, 62), _FONT, 0.75, _HUD_COLOR, 2)
    return frame


def _resolve_tracked_id(snapshot: dict, bbox: list, label: str) -> Optional[str]:
    """Find the world-map ID that best matches this detection by IoU."""
    best_id, best_iou = None, 0.0
    for obj in snapshot.values():
        if obj.label != label:
            continue
        iou = _iou(bbox, obj.bbox)
        if iou > best_iou:
            best_iou, best_id = iou, obj.id
    return best_id if best_iou > 0.10 else None
