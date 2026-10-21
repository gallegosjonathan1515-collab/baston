"""Wrapper de YOLOv8: detección (+ tracking ByteTrack opcional)."""
from dataclasses import dataclass
from typing import Optional

from ultralytics import YOLO

import config


@dataclass
class Detection:
    cls_id: int
    name: str
    conf: float
    x1: int
    y1: int
    x2: int
    y2: int
    track_id: Optional[int] = None
    ghost: bool = False

    @property
    def area(self) -> int:
        return max(self.x2 - self.x1, 0) * max(self.y2 - self.y1, 0)


class Detector:
    def __init__(self):
        self.model = YOLO(config.MODEL_PATH)
        self.names = self.model.names

    def detect(self, frame) -> list:
        kwargs = dict(imgsz=config.IMGSZ, conf=config.CONF,
                      classes=config.ALLOWED_CLASSES, verbose=False)
        if config.USE_TRACKING:
            results = self.model.track(frame, persist=True, tracker=config.TRACKER, **kwargs)[0]
        else:
            results = self.model.predict(frame, **kwargs)[0]

        boxes = results.boxes
        if boxes is None or len(boxes) == 0:
            return []
        ids = boxes.id.int().tolist() if boxes.id is not None else [None] * len(boxes)

        detections = []
        for box, tid in zip(boxes, ids):
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            cls_id = int(box.cls[0])
            detections.append(Detection(cls_id, self.names[cls_id], float(box.conf[0]),
                                        x1, y1, x2, y2, track_id=tid))
        return detections
