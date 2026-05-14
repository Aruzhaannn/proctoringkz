import cv2
import numpy as np
import mediapipe as mp
from dataclasses import dataclass


@dataclass
class HeadPoseResult:
    pitch: float   # up / down  (+ = down)
    yaw: float     # left / right (+ = right)
    roll: float    # tilt
    looking_away: bool
    violation: str | None


# 3-D model points of canonical face (mm)
_FACE_3D = np.array([
    [0.0,    0.0,    0.0],       # nose tip      (1)
    [0.0,  -330.0,  -65.0],      # chin          (152)
    [-225.0, 170.0, -135.0],     # left  corner  (263)
    [225.0,  170.0, -135.0],     # right corner  (33)
    [-150.0,-150.0, -125.0],     # left  mouth   (287)
    [150.0, -150.0, -125.0],     # right mouth   (57)
], dtype=np.float64)

_LM_INDICES = [1, 152, 263, 33, 287, 57]

_YAW_LIMIT   = 30.0   # degrees
_PITCH_LIMIT = 25.0   # degrees


class HeadPoseEstimator:
    def __init__(self):
        self._face_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
        )

    def estimate(self, image: np.ndarray) -> HeadPoseResult:
        h, w = image.shape[:2]
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        mp_result = self._face_mesh.process(rgb)

        if not mp_result.multi_face_landmarks:
            return HeadPoseResult(
                pitch=0.0, yaw=0.0, roll=0.0,
                looking_away=True, violation="HEAD_NOT_DETECTED",
            )

        lm = mp_result.multi_face_landmarks[0].landmark
        face_2d = np.array(
            [[lm[i].x * w, lm[i].y * h] for i in _LM_INDICES],
            dtype=np.float64,
        )

        focal = float(w)
        cam = np.array([[focal, 0, w / 2],
                        [0, focal, h / 2],
                        [0, 0,     1    ]], dtype=np.float64)
        dist = np.zeros((4, 1), dtype=np.float64)

        _, rot_vec, _ = cv2.solvePnP(_FACE_3D, face_2d, cam, dist,
                                     flags=cv2.SOLVEPNP_ITERATIVE)
        rmat, _ = cv2.Rodrigues(rot_vec)
        angles, *_ = cv2.RQDecomp3x3(rmat)

        pitch = round(angles[0] * 360, 1)
        yaw   = round(angles[1] * 360, 1)
        roll  = round(angles[2] * 360, 1)

        looking_away = abs(yaw) > _YAW_LIMIT or abs(pitch) > _PITCH_LIMIT
        violation = "HEAD_TURNED" if looking_away else None

        return HeadPoseResult(
            pitch=pitch, yaw=yaw, roll=roll,
            looking_away=looking_away, violation=violation,
        )