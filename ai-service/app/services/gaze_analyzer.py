import numpy as np
from dataclasses import dataclass


@dataclass
class GazeResult:
    looking_away: bool
    direction: str  # "center", "left", "right", "up", "down", "unknown"
    violation: str | None


# MediaPipe FaceMesh landmark indices for iris + eye corners
_LEFT_IRIS   = [468, 469, 470, 471, 472]
_RIGHT_IRIS  = [473, 474, 475, 476, 477]
_LEFT_EYE_CORNERS  = (33, 133)    # outer, inner corner of left eye
_RIGHT_EYE_CORNERS = (362, 263)   # outer, inner corner of right eye
_LEFT_EYE_TOP_BOTTOM  = (159, 145)  # top, bottom of left eye
_RIGHT_EYE_TOP_BOTTOM = (386, 374)  # top, bottom of right eye

# Thresholds for gaze direction
_HORIZONTAL_THRESHOLD = 0.28    # ratio offset from center → looking left/right
_VERTICAL_THRESHOLD   = 0.25    # ratio offset from center → looking up/down


class GazeAnalyzer:
    """Iris-based gaze estimation using MediaPipe FaceMesh landmarks (468+10)."""

    def analyze_from_landmarks(self, landmarks: list[list]) -> GazeResult:
        """
        Analyze gaze direction from MediaPipe FaceMesh landmarks.

        Args:
            landmarks: list of [x, y, z] for each of 478 landmarks

        Returns:
            GazeResult with direction and violation info
        """
        if not landmarks or len(landmarks) < 478:
            # Not enough landmarks (no iris refinement), fall back to basic estimation
            return self._basic_from_landmarks(landmarks)

        try:
            # ── Left eye iris position relative to eye corners ────────
            l_iris_x = np.mean([landmarks[i][0] for i in _LEFT_IRIS])
            l_iris_y = np.mean([landmarks[i][1] for i in _LEFT_IRIS])

            l_outer = landmarks[_LEFT_EYE_CORNERS[0]]
            l_inner = landmarks[_LEFT_EYE_CORNERS[1]]
            l_top   = landmarks[_LEFT_EYE_TOP_BOTTOM[0]]
            l_bottom= landmarks[_LEFT_EYE_TOP_BOTTOM[1]]

            l_eye_width  = abs(l_inner[0] - l_outer[0]) + 1e-6
            l_eye_height = abs(l_bottom[1] - l_top[1]) + 1e-6
            l_center_x   = (l_outer[0] + l_inner[0]) / 2
            l_center_y   = (l_top[1] + l_bottom[1]) / 2

            l_ratio_h = (l_iris_x - l_center_x) / l_eye_width
            l_ratio_v = (l_iris_y - l_center_y) / l_eye_height

            # ── Right eye iris position relative to eye corners ───────
            r_iris_x = np.mean([landmarks[i][0] for i in _RIGHT_IRIS])
            r_iris_y = np.mean([landmarks[i][1] for i in _RIGHT_IRIS])

            r_outer = landmarks[_RIGHT_EYE_CORNERS[0]]
            r_inner = landmarks[_RIGHT_EYE_CORNERS[1]]
            r_top   = landmarks[_RIGHT_EYE_TOP_BOTTOM[0]]
            r_bottom= landmarks[_RIGHT_EYE_TOP_BOTTOM[1]]

            r_eye_width  = abs(r_inner[0] - r_outer[0]) + 1e-6
            r_eye_height = abs(r_bottom[1] - r_top[1]) + 1e-6
            r_center_x   = (r_outer[0] + r_inner[0]) / 2
            r_center_y   = (r_top[1] + r_bottom[1]) / 2

            r_ratio_h = (r_iris_x - r_center_x) / r_eye_width
            r_ratio_v = (r_iris_y - r_center_y) / r_eye_height

            # ── Average both eyes ─────────────────────────────────────
            avg_h = (l_ratio_h + r_ratio_h) / 2
            avg_v = (l_ratio_v + r_ratio_v) / 2

            # ── Determine direction ───────────────────────────────────
            direction = "center"

            if avg_h < -_HORIZONTAL_THRESHOLD:
                direction = "right"   # iris is toward outer (left in image = right from student POV)
            elif avg_h > _HORIZONTAL_THRESHOLD:
                direction = "left"

            if avg_v < -_VERTICAL_THRESHOLD:
                direction = "up"
            elif avg_v > _VERTICAL_THRESHOLD:
                direction = "down"

            # Combined diagonal
            if abs(avg_h) > _HORIZONTAL_THRESHOLD and abs(avg_v) > _VERTICAL_THRESHOLD:
                h_dir = "left" if avg_h > 0 else "right"
                v_dir = "up" if avg_v < 0 else "down"
                direction = f"{v_dir}-{h_dir}"

            looking_away = direction != "center"
            violation = "GAZE_AWAY" if looking_away else None

            return GazeResult(
                looking_away=looking_away,
                direction=direction,
                violation=violation
            )

        except (IndexError, TypeError, ZeroDivisionError):
            return GazeResult(looking_away=False, direction="unknown", violation=None)

    def _basic_from_landmarks(self, landmarks: list[list] | None) -> GazeResult:
        """Fallback: estimate gaze from basic landmarks (no iris data)."""
        if not landmarks or len(landmarks) < 468:
            return GazeResult(looking_away=True, direction="unknown", violation="GAZE_AWAY")

        # Use nose tip (1) vs face center to estimate rough gaze
        nose = landmarks[1]
        left_cheek  = landmarks[234]
        right_cheek = landmarks[454]

        face_cx = (left_cheek[0] + right_cheek[0]) / 2
        face_w  = abs(right_cheek[0] - left_cheek[0]) + 1e-6
        offset  = (nose[0] - face_cx) / face_w

        if offset < -0.15:
            return GazeResult(looking_away=True, direction="right", violation="GAZE_AWAY")
        elif offset > 0.15:
            return GazeResult(looking_away=True, direction="left", violation="GAZE_AWAY")

        return GazeResult(looking_away=False, direction="center", violation=None)

    # Keep old interface for backwards compat (not used anymore but safe)
    def analyze(self, image: np.ndarray, face: dict) -> GazeResult:
        return GazeResult(looking_away=False, direction="unknown", violation=None)