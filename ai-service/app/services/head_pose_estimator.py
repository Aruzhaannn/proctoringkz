"""
Head pose estimation using solvePnP (MediaPipe landmarks) and YOLO-pose keypoints.
Estimates pitch, yaw, roll angles and flags HEAD_TURNED violations.
"""

import cv2
import numpy as np
from dataclasses import dataclass


@dataclass
class HeadPoseResult:
    pitch: float = 0.0
    yaw: float = 0.0
    roll: float = 0.0
    looking_away: bool = False
    violation: str | None = None


# MediaPipe FaceMesh landmark indices for solvePnP
# nose tip, chin, left eye outer, right eye outer, left mouth, right mouth
_FACE_3D_MODEL = np.array([
    [0.0, 0.0, 0.0],            # Nose tip
    [0.0, -330.0, -65.0],       # Chin
    [-225.0, 170.0, -135.0],    # Left eye outer corner
    [225.0, 170.0, -135.0],     # Right eye outer corner
    [-150.0, -150.0, -125.0],   # Left mouth corner
    [150.0, -150.0, -125.0],    # Right mouth corner
], dtype=np.float64)

_FACE_LM_INDICES = [1, 152, 33, 263, 61, 291]

# Thresholds for head turn detection (degrees) — generous to reduce false positives
_YAW_THRESHOLD   = 25.0    # left-right turn
_PITCH_THRESHOLD = 25.0    # up-down tilt

# Debounce: consecutive frames before flagging
_HEAD_TURN_DEBOUNCE = 3


class HeadPoseEstimator:
    """Estimates head orientation using MediaPipe landmarks or YOLO-pose keypoints."""

    def __init__(self):
        self._turn_counter = 0

    def estimate_from_landmarks(self, landmarks: list[list], image_shape: tuple) -> HeadPoseResult:
        """
        Estimate head pose using solvePnP from MediaPipe FaceMesh landmarks.

        Args:
            landmarks: list of [x, y, z] for 478 landmarks (pixel coords)
            image_shape: (height, width, channels)

        Returns:
            HeadPoseResult with pitch, yaw, roll, and violation info
        """
        if not landmarks or len(landmarks) < 300:
            return HeadPoseResult()

        h, w = image_shape[:2]

        try:
            # Extract 2D points for solvePnP
            image_points = np.array([
                [landmarks[idx][0], landmarks[idx][1]]
                for idx in _FACE_LM_INDICES
            ], dtype=np.float64)

            # Camera matrix approximation
            focal_length = w
            center = (w / 2, h / 2)
            camera_matrix = np.array([
                [focal_length, 0, center[0]],
                [0, focal_length, center[1]],
                [0, 0, 1],
            ], dtype=np.float64)
            dist_coeffs = np.zeros((4, 1))

            success, rotation_vec, translation_vec = cv2.solvePnP(
                _FACE_3D_MODEL, image_points, camera_matrix, dist_coeffs,
                flags=cv2.SOLVEPNP_ITERATIVE,
            )

            if not success:
                return HeadPoseResult()

            # Convert rotation vector to Euler angles
            rmat, _ = cv2.Rodrigues(rotation_vec)
            angles, _, _, _, _, _ = cv2.RQDecomp3x3(rmat)

            pitch = float(angles[0])
            yaw = float(angles[1])
            roll = float(angles[2])

            return self._evaluate(pitch, yaw, roll)

        except Exception:
            return HeadPoseResult()

    def estimate_from_yolo_keypoints(self, keypoints: list, image_shape: tuple) -> HeadPoseResult:
        """
        Estimate head pose from YOLO-pose keypoints.

        YOLO-pose provides 17 keypoints in COCO format:
        0=nose, 1=left_eye, 2=right_eye, 3=left_ear, 4=right_ear, ...

        Args:
            keypoints: list of [x, y, conf] for 17 keypoints
            image_shape: (height, width, channels)

        Returns:
            HeadPoseResult
        """
        if not keypoints or len(keypoints) < 5:
            return HeadPoseResult()

        try:
            nose      = keypoints[0][:2]
            left_eye  = keypoints[1][:2]
            right_eye = keypoints[2][:2]
            left_ear  = keypoints[3][:2]
            right_ear = keypoints[4][:2]

            # Estimate yaw from ear-to-nose ratios
            eye_center_x = (left_eye[0] + right_eye[0]) / 2
            eye_dist = abs(right_eye[0] - left_eye[0]) + 1e-6

            # Nose displacement from eye center → yaw
            nose_offset = (nose[0] - eye_center_x) / eye_dist
            yaw = float(nose_offset * 45)   # rough mapping

            # Ear visibility → additional yaw cue
            l_ear_conf = keypoints[3][2] if len(keypoints[3]) > 2 else 0.5
            r_ear_conf = keypoints[4][2] if len(keypoints[4]) > 2 else 0.5
            if l_ear_conf < 0.3 and r_ear_conf > 0.5:
                yaw = max(yaw, 20)   # facing right
            elif r_ear_conf < 0.3 and l_ear_conf > 0.5:
                yaw = min(yaw, -20)  # facing left

            # Pitch from nose-to-eye vertical ratio
            eye_center_y = (left_eye[1] + right_eye[1]) / 2
            eye_height = abs(right_eye[1] - left_eye[1]) + 1e-6
            nose_v_offset = (nose[1] - eye_center_y) / (eye_dist + 1e-6)
            pitch = float((nose_v_offset - 0.5) * 40)

            roll = 0.0  # hard to estimate from YOLO keypoints

            return self._evaluate(pitch, yaw, roll)

        except Exception:
            return HeadPoseResult()

    def _evaluate(self, pitch: float, yaw: float, roll: float) -> HeadPoseResult:
        """Evaluate angles and determine if head is turned beyond thresholds."""
        turned = abs(yaw) > _YAW_THRESHOLD or abs(pitch) > _PITCH_THRESHOLD

        if turned:
            self._turn_counter += 1
        else:
            self._turn_counter = 0

        # Only flag after debounce
        flagged = turned and self._turn_counter >= _HEAD_TURN_DEBOUNCE
        violation = "HEAD_TURNED" if flagged else None

        return HeadPoseResult(
            pitch=round(pitch, 1),
            yaw=round(yaw, 1),
            roll=round(roll, 1),
            looking_away=flagged,
            violation=violation,
        )
