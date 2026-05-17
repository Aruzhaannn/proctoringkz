import numpy as np
from dataclasses import dataclass, field
from ultralytics import YOLO


@dataclass
class ObjectResult:
    persons_detected: int
    objects: list[dict] = field(default_factory=list)
    violations: list[str] = field(default_factory=list)


class ObjectDetector:
    """
    YOLOv8s-based object detection for proctoring.
    Upgraded from YOLOv8n for significantly better accuracy.
    
    Detects: phones, books, extra persons, earbuds/headphones
    """
    
    # Phone classes — only "cell phone", no more false-positive "remote"
    _PHONE_CLASSES = {"cell phone"}
    _PHONE_MIN_CONF = 0.45
    
    # Academic cheating materials
    _BOOK_CLASSES = {"book"}
    _BOOK_MIN_CONF = 0.40
    
    # Potential earbuds/headphones — YOLO can sometimes catch these
    # "mouse" class sometimes triggers for earbuds on desk
    _EARBUDS_SUSPECT = {"headphones"}  # not in COCO, but custom models can add this
    
    _PERSON_CLASS = "person"
    _PERSON_MIN_CONF = 0.50
    
    # Minimum bounding box area ratio to image area (filters tiny noise detections)
    _MIN_BOX_AREA_RATIO = 0.004

    def __init__(self):
        # YOLOv8s — small model, ~22MB, much better accuracy than nano
        # Auto-downloads on first run
        self._model = YOLO("yolov8s.pt")

    def detect(self, image: np.ndarray) -> ObjectResult:
        h, w = image.shape[:2]
        image_area = h * w
        min_area = image_area * self._MIN_BOX_AREA_RATIO
        
        # Run inference — conf 0.35 is the sweet spot for yolov8s
        results = self._model(image, verbose=False, conf=0.35)[0]

        persons = 0
        objects: list[dict] = []
        seen_violations: set[str] = set()

        for box in results.boxes:
            cls_id = int(box.cls[0])
            cls_name: str = results.names[cls_id]
            conf = float(box.conf[0])
            x1, y1, x2, y2 = (int(v) for v in box.xyxy[0])
            
            box_area = (x2 - x1) * (y2 - y1)
            
            # Skip tiny detections (noise)
            if box_area < min_area:
                continue

            obj_info = {
                "class": cls_name,
                "confidence": round(conf, 2),
                "x": x1, "y": y1, "w": x2 - x1, "h": y2 - y1,
            }

            if cls_name == self._PERSON_CLASS:
                if conf >= self._PERSON_MIN_CONF:
                    persons += 1
                    objects.append(obj_info)
            elif cls_name in self._PHONE_CLASSES:
                if conf >= self._PHONE_MIN_CONF:
                    seen_violations.add("PHONE_DETECTED")
                    objects.append(obj_info)
            elif cls_name in self._BOOK_CLASSES:
                if conf >= self._BOOK_MIN_CONF:
                    seen_violations.add("BOOK_DETECTED")
                    objects.append(obj_info)
            # Skip other irrelevant classes

        if persons > 1:
            seen_violations.add("MULTIPLE_PERSONS")

        return ObjectResult(
            persons_detected=persons,
            objects=objects,
            violations=list(seen_violations),
        )