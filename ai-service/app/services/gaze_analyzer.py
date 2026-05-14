import cv2
import numpy as np
from dataclasses import dataclass


@dataclass
class GazeResult:
    looking_away: bool
    direction: str  # "center", "left", "right", "up", "down", "unknown"
    violation: str | None


class GazeAnalyzer:
    def __init__(self):
        self._eye_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_eye.xml"
        )

    def analyze(self, image: np.ndarray, face: dict) -> GazeResult:
        x, y, w, h = face["x"], face["y"], face["w"], face["h"]
        face_roi = image[y : y + h, x : x + w]
        gray_roi = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)

        eyes = self._eye_cascade.detectMultiScale(gray_roi, scaleFactor=1.1, minNeighbors=5)

        if len(eyes) < 2:
            return GazeResult(looking_away=True, direction="unknown", violation="GAZE_AWAY")

        # Compare eye positions relative to face center
        eye_centers = [(ex + ew // 2, ey + eh // 2) for ex, ey, ew, eh in eyes]
        avg_x = sum(c[0] for c in eye_centers) / len(eye_centers)
        face_center_x = w // 2

        offset_ratio = (avg_x - face_center_x) / face_center_x

        if offset_ratio < -0.3:
            direction = "left"
        elif offset_ratio > 0.3:
            direction = "right"
        else:
            direction = "center"

        looking_away = direction != "center"
        violation = "GAZE_AWAY" if looking_away else None

        return GazeResult(looking_away=looking_away, direction=direction, violation=violation)