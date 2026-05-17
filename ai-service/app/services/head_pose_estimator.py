import cv2
import numpy as np
from dataclasses import dataclass


@dataclass
class HeadPoseResult:
    pitch: float   # up / down  (+ = down)
    yaw: float     # left / right (+ = right)
    roll: float    # tilt
    looking_away: bool
    violation: str | None


_FACE_CASCADE = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)
_EYE_CASCADE = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_eye.xml"
)
_PROFILE_CASCADE = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_profileface.xml"
)

_YAW_LIMIT   = 30.0
_PITCH_LIMIT = 25.0


class HeadPoseEstimator:
    def estimate(self, image: np.ndarray) -> HeadPoseResult:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        h, w = image.shape[:2]

        faces = _FACE_CASCADE.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))
        if len(faces) == 0:
            # Check for profile face (head turned sideways)
            profiles = _PROFILE_CASCADE.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))
            if len(profiles) > 0:
                return HeadPoseResult(pitch=0.0, yaw=45.0, roll=0.0, looking_away=True, violation="HEAD_TURNED")
            return HeadPoseResult(pitch=0.0, yaw=0.0, roll=0.0, looking_away=True, violation="HEAD_NOT_DETECTED")

        x, y, fw, fh = faces[0]
        face_roi = gray[y:y + fh, x:x + fw]

        eyes = _EYE_CASCADE.detectMultiScale(face_roi, scaleFactor=1.1, minNeighbors=5)

        yaw = 0.0
        pitch = 0.0
        roll = 0.0

        if len(eyes) >= 2:
            # Estimate yaw from eye symmetry relative to face center
            eye_centers = [(ex + ew // 2, ey + eh // 2) for ex, ey, ew, eh in eyes[:2]]
            avg_x = sum(c[0] for c in eye_centers) / 2
            face_cx = fw / 2
            offset_ratio = (avg_x - face_cx) / (face_cx + 1e-6)
            yaw = round(offset_ratio * _YAW_LIMIT * 2, 1)

            # Estimate roll from eye height difference
            dy = eye_centers[0][1] - eye_centers[1][1]
            dx = eye_centers[0][0] - eye_centers[1][0] + 1e-6
            roll = round(float(np.degrees(np.arctan2(dy, dx))), 1)

            # Estimate pitch from face vertical position in frame
            face_cy_ratio = (y + fh / 2) / (h + 1e-6)
            pitch = round((face_cy_ratio - 0.5) * _PITCH_LIMIT * 2, 1)
        elif len(eyes) == 1:
            # Only one eye visible — head likely turned
            ex, ey, ew, eh = eyes[0]
            eye_cx = ex + ew // 2
            face_cx = fw / 2
            yaw = 35.0 if eye_cx < face_cx else -35.0
        else:
            # No eyes detected
            yaw = 0.0

        looking_away = abs(yaw) > _YAW_LIMIT or abs(pitch) > _PITCH_LIMIT
        violation = "HEAD_TURNED" if looking_away else None

        return HeadPoseResult(pitch=pitch, yaw=yaw, roll=roll, looking_away=looking_away, violation=violation)