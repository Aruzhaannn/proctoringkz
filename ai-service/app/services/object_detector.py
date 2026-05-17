import numpy as np
from dataclasses import dataclass, field
from ultralytics import YOLO


@dataclass
class ObjectResult:
    persons_detected: int
    objects: list[dict] = field(default_factory=list)
    violations: list[str] = field(default_factory=list)


class ObjectDetector:
    _PHONE_CLASSES = {"cell phone", "remote"}   # YOLO often classifies phones as "remote"
    _BOOK_CLASSES = {"book", "laptop"}          # laptop also suspicious during exam
    _PERSON_CLASS = "person"
    _PERSON_MIN_CONF = 0.45   # Higher threshold for persons to avoid false multi-person

    def __init__(self):
        # yolov8n.pt auto-downloads on first run (~6 MB)
        self._model = YOLO("yolov8n.pt")

    def detect(self, image: np.ndarray) -> ObjectResult:
        # Low confidence threshold (0.25) to catch phones even when partially visible
        results = self._model(image, verbose=False, conf=0.25)[0]

        persons = 0
        objects: list[dict] = []
        seen_violations: set[str] = set()

        for box in results.boxes:
            cls_id = int(box.cls[0])
            cls_name: str = results.names[cls_id]
            conf = float(box.conf[0])
            x1, y1, x2, y2 = (int(v) for v in box.xyxy[0])

            obj_info = {
                "class": cls_name,
                "confidence": round(conf, 2),
                "x": x1, "y": y1, "w": x2 - x1, "h": y2 - y1,
            }

            if cls_name == self._PERSON_CLASS:
                # Only count high-confidence person detections to avoid
                # YOLO detecting one person as two overlapping boxes
                if conf >= self._PERSON_MIN_CONF:
                    persons += 1
                    objects.append(obj_info)
            elif cls_name in self._PHONE_CLASSES:
                seen_violations.add("PHONE_DETECTED")
                objects.append(obj_info)
            elif cls_name in self._BOOK_CLASSES:
                seen_violations.add("BOOK_DETECTED")
                objects.append(obj_info)
            # Skip other irrelevant YOLO classes

        if persons == 0:
            # Don't add PERSON_ABSENT if face was detected (handled by face_detector)
            pass
        elif persons > 1:
            seen_violations.add("MULTIPLE_PERSONS")

        return ObjectResult(
            persons_detected=persons,
            objects=objects,
            violations=list(seen_violations),
        )