"""
Object/person detection using YOLOv8.
Detects: persons (multiple → violation), phones, books/notebooks.
"""

import numpy as np
from dataclasses import dataclass, field
from ultralytics import YOLO


@dataclass
class ObjectDetectionResult:
    persons_detected: int = 0
    objects: list[dict] = field(default_factory=list)
    violations: list[str] = field(default_factory=list)


# COCO class IDs
_PERSON_ID    = 0
_PHONE_ID     = 67    # "cell phone"
_BOOK_ID      = 73    # "book"
_LAPTOP_ID    = 63    # "laptop" (not a violation, but logged)
_REMOTE_ID    = 65    # "remote" (can look like a phone)

# Detection confidence thresholds — lower for phones (they're small objects)
_PHONE_CONF   = 0.25
_PERSON_CONF  = 0.45
_DEFAULT_CONF = 0.40


class ObjectDetector:
    """
    YOLOv8 nano model for real-time object detection.
    Detects persons, phones, books, and other suspicious objects.
    """

    def __init__(self, model_path: str = "yolov8n.pt"):
        self._model = YOLO(model_path)

    def detect(self, image: np.ndarray) -> ObjectDetectionResult:
        """
        Run YOLOv8 inference on a BGR image.

        Returns:
            ObjectDetectionResult with person count, detected objects, and violations.
        """
        # Run inference with low confidence to catch phones
        results = self._model(image, conf=0.20, verbose=False)

        persons = 0
        objects = []
        violations = []

        for result in results:
            if result.boxes is None:
                continue

            for box in result.boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                xyxy = box.xyxy[0].cpu().numpy()

                cls_name = self._model.names.get(cls_id, f"class_{cls_id}")

                # ── Person detection ──────────────────────────────
                if cls_id == _PERSON_ID and conf >= _PERSON_CONF:
                    persons += 1
                    objects.append({
                        "label": "person",
                        "confidence": round(conf, 2),
                        "bbox": [int(x) for x in xyxy],
                    })

                # ── Phone detection ───────────────────────────────
                elif cls_id in (_PHONE_ID, _REMOTE_ID) and conf >= _PHONE_CONF:
                    objects.append({
                        "label": "phone",
                        "confidence": round(conf, 2),
                        "bbox": [int(x) for x in xyxy],
                    })
                    if "PHONE_DETECTED" not in violations:
                        violations.append("PHONE_DETECTED")

                # ── Book detection ────────────────────────────────
                elif cls_id == _BOOK_ID and conf >= _DEFAULT_CONF:
                    objects.append({
                        "label": "book",
                        "confidence": round(conf, 2),
                        "bbox": [int(x) for x in xyxy],
                    })
                    if "BOOK_DETECTED" not in violations:
                        violations.append("BOOK_DETECTED")

        # Flag multiple persons (someone else in frame)
        if persons >= 2:
            violations.append("MULTIPLE_PERSONS")
        elif persons == 0:
            # Person not detected by YOLO — might be too close to camera
            # Don't flag as violation, face_detector handles this
            pass

        return ObjectDetectionResult(
            persons_detected=persons,
            objects=objects,
            violations=violations,
        )
