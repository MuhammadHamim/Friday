"""
YOLOv11 inference engine.

Loads the model once at startup; `detect()` is safe to call from any thread
(ultralytics handles its own internal thread safety for inference).
"""

import torch
from ultralytics import YOLO

from config import YOLO_MODEL, YOLO_CONFIDENCE, YOLO_IOU, YOLO_DEVICE, YOLO_CLASSES


def _resolve_device() -> str:
    if YOLO_DEVICE != "auto":
        return YOLO_DEVICE
    if torch.cuda.is_available():
        name = torch.cuda.get_device_name(0)
        print(f"[Vision] CUDA available — {name}")
        return "cuda"
    print("[Vision] CUDA not available — running YOLO on CPU.")
    return "cpu"


class YOLOEngine:
    """
    Wraps a YOLOv11 model for single-call inference.

    Selected model: yolo11l.pt  (53.4% mAP@50-95, ~4 ms on RTX 5060)
    Configurable via YOLO_MODEL in config.py.
    """

    def __init__(self) -> None:
        self._device = _resolve_device()
        print(f"[Vision] Loading YOLO '{YOLO_MODEL}' on {self._device} …")
        self._model = YOLO(YOLO_MODEL)
        self._model.to(self._device)
        print(f"[Vision] YOLO ready.")

    def detect(self, frame) -> list:
        """
        Run inference on a BGR NumPy frame (as returned by cv2.VideoCapture).

        Returns:
            [{"label": str, "bbox": [x1, y1, x2, y2], "confidence": float}, …]
        """
        results = self._model.predict(
            frame,
            verbose=False,
            conf=YOLO_CONFIDENCE,
            iou=YOLO_IOU,
            device=self._device,
            classes=YOLO_CLASSES,
        )
        detections = []
        for result in results:
            for box in result.boxes:
                detections.append({
                    "label":      result.names[int(box.cls[0])],
                    "bbox":       box.xyxy[0].tolist(),
                    "confidence": float(box.conf[0]),
                })
        return detections
