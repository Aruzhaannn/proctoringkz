import numpy as np
from dataclasses import dataclass


@dataclass
class HeadPoseResult:
    pitch: float   # up / down  (+ = looking down, - = looking up)
    yaw: float     # left / right (+ = looking right, - = looking left)
    roll: float    # tilt
    looking_away: bool
    violation: str | None


# MediaPipe FaceMesh key landmark indices for 3D head pose estimation
# These 6 points give a good 3D face reference
_NOSE_TIP    = 1
_CHIN        = 152
_LEFT_EYE    = 33
_RIGHT_EYE   = 263
_LEFT_MOUTH  = 61
_RIGHT_MOUTH = 291

# 3D model points (canonical face model in arbitrary units)
_MODEL_POINTS = np.array([
    [0.0,    0.0,    0.0],      # Nose tip
    [0.0,   -63.6,  -12.5],     # Chin
    [-43.3,  32.7,  -26.0],     # Left eye left corner
    [43.3,   32.7,  -26.0],     # Right eye right corner
    [-28.9, -28.9,  -24.1],     # Left mouth corner
    [28.9,  -28.9,  -24.1],     # Right mouth corner
], dtype=np.float64)

_YAW_LIMIT   = 20.0    # degrees — reduced from 30 for stricter detection
_PITCH_LIMIT = 20.0    # degrees — reduced from 25 for stricter detection


class HeadPoseEstimator:
    """Head pose estimation using MediaPipe FaceMesh landmarks + solvePnP."""

    def estimate_from_landmarks(self, landmarks: list[list], image_shape: tuple) -> HeadPoseResult:
        """
        Estimate head pose from MediaPipe FaceMesh landmarks using solvePnP.

        Args:
            landmarks: list of [x, y, z] for each of 468+ landmarks
            image_shape: (height, width) of the image

        Returns:
            HeadPoseResult with pitch, yaw, roll and violation
        """
        if not landmarks or len(landmarks) < 468:
            return HeadPoseResult(
                pitch=0.0, yaw=0.0, roll=0.0,
                looking_away=True, violation="HEAD_NOT_DETECTED"
            )

        h, w = image_shape[:2]

        try:
            # Extract 2D image points from landmarks
            indices = [_NOSE_TIP, _CHIN, _LEFT_EYE, _RIGHT_EYE, _LEFT_MOUTH, _RIGHT_MOUTH]
            image_points = np.array(
                [[landmarks[i][0], landmarks[i][1]] for i in indices],
                dtype=np.float64
            )

            # Camera matrix (approximate)
            focal_length = w
            center = (w / 2, h / 2)
            camera_matrix = np.array([
                [focal_length, 0,            center[0]],
                [0,            focal_length, center[1]],
                [0,            0,            1]
            ], dtype=np.float64)

            dist_coeffs = np.zeros((4, 1), dtype=np.float64)

            # Solve PnP to get rotation and translation vectors
            success, rotation_vec, translation_vec = cv2.solvePnP(
                _MODEL_POINTS, image_points, camera_matrix, dist_coeffs,
                flags=cv2.SOLVEPNP_ITERATIVE
            )

            if not success:
                return self._fallback_from_landmarks(landmarks, image_shape)

            # Convert rotation vector to rotation matrix, then to Euler angles
            rmat, _ = cv2.Rodrigues(rotation_vec)
            angles, _, _, _, _, _ = cv2.RQDecomp3x3(rmat)

            pitch = round(float(angles[0]), 1)  # up/down
            yaw   = round(float(angles[1]), 1)  # left/right
            roll  = round(float(angles[2]), 1)  # tilt

            looking_away = abs(yaw) > _YAW_LIMIT or abs(pitch) > _PITCH_LIMIT
            violation = "HEAD_TURNED" if looking_away else None

            return HeadPoseResult(
                pitch=pitch, yaw=yaw, roll=roll,
                looking_away=looking_away, violation=violation
            )

        except Exception:
            return self._fallback_from_landmarks(landmarks, image_shape)

    def _fallback_from_landmarks(self, landmarks: list[list], image_shape: tuple) -> HeadPoseResult:
        """Simplified head pose from landmark geometry when solvePnP fails."""
        h, w = image_shape[:2]

        try:
            nose  = landmarks[_NOSE_TIP]
            chin  = landmarks[_CHIN]
            l_eye = landmarks[_LEFT_EYE]
            r_eye = landmarks[_RIGHT_EYE]

            # Yaw: nose offset from midpoint between eyes
            eye_mid_x = (l_eye[0] + r_eye[0]) / 2
            eye_dist  = abs(r_eye[0] - l_eye[0]) + 1e-6
            yaw_ratio = (nose[0] - eye_mid_x) / eye_dist
            yaw = round(yaw_ratio * 60, 1)  # approximate degrees

            # Pitch: vertical position of nose relative to eyes/chin
            face_height = abs(chin[1] - ((l_eye[1] + r_eye[1]) / 2)) + 1e-6
            nose_ratio  = (nose[1] - (l_eye[1] + r_eye[1]) / 2) / face_height
            pitch = round((nose_ratio - 0.35) * 80, 1)

            # Roll: eye height difference
            dy = r_eye[1] - l_eye[1]
            dx = r_eye[0] - l_eye[0] + 1e-6
            roll = round(float(np.degrees(np.arctan2(dy, dx))), 1)

            looking_away = abs(yaw) > _YAW_LIMIT or abs(pitch) > _PITCH_LIMIT
            violation = "HEAD_TURNED" if looking_away else None

            return HeadPoseResult(
                pitch=pitch, yaw=yaw, roll=roll,
                looking_away=looking_away, violation=violation
            )
        except (IndexError, TypeError):
            return HeadPoseResult(
                pitch=0.0, yaw=0.0, roll=0.0,
                looking_away=True, violation="HEAD_NOT_DETECTED"
            )

    # Keep old interface for backwards compat
    def estimate(self, image: np.ndarray) -> HeadPoseResult:
        return HeadPoseResult(
            pitch=0.0, yaw=0.0, roll=0.0,
            looking_away=False, violation=None
        )


# OpenCV is needed for solvePnP
import cv2