import cv2
import numpy as np
from dataclasses import dataclass


@dataclass
class FaceResult:
    face_count: int
    faces: list[dict]
    violation: str | None


class FaceDetector:
    def __init__(self):
        self._cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

    def detect(self, image: np.ndarray) -> FaceResult:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        detected = self._cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80)
        )

        faces = []
        if len(detected) > 0:
            for x, y, w, h in detected:
                faces.append({"x": int(x), "y": int(y), "w": int(w), "h": int(h)})

        violation = None
        if len(faces) == 0:
            violation = "NO_FACE"
        elif len(faces) > 1:
            violation = "MULTIPLE_FACES"

        return FaceResult(face_count=len(faces), faces=faces, violation=violation)