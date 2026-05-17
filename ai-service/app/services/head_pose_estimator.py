import numpy as np
import math
from dataclasses import dataclass


@dataclass
class HeadPoseResult:
    pitch: float   # up / down  (+ = looking down, - = looking up)
    yaw: float     # left / right (+ = looking right, - = looking left)
    roll: float    # tilt
    looking_away: bool
    violation: str | None


# Thresholds — generous to avoid false positives
_YAW_LIMIT   = 55.0    # degrees
_PITCH_LIMIT = 50.0    # degrees

# Debounce: consecutive frame threshold
_HEAD_TURN_DEBOUNCE = 3


class HeadPoseEstimator:
    """
    Head pose estimation using YOLO-pose keypoints.
    
    Uses nose, eyes, ears, and shoulders from YOLO pose model
    to estimate head yaw, pitch, and roll.
    
    This is MORE ROBUST than MediaPipe solvePnP because:
    - YOLO-pose handles occlusion better
    - Works at wider angle ranges
    - Keypoint confidence scores help filter noise
    - Ear visibility is a strong indicator of head turn
    """

    def __init__(self):
        self._turned_counter = 0

    def estimate_from_yolo_keypoints(self, keypoints: dict, image_shape: tuple = None) -> HeadPoseResult:
        """
        Estimate head pose from YOLO-pose keypoints.
        
        Args:
            keypoints: dict with 'nose', 'left_eye', 'right_eye', 
                       'left_ear', 'right_ear', 'left_shoulder', 'right_shoulder'
                       Each has {x, y, conf, visible}
        
        Returns:
            HeadPoseResult with yaw, pitch, roll and violation
        """
        if not keypoints:
            return HeadPoseResult(pitch=0, yaw=0, roll=0, looking_away=False, violation=None)
        
        nose = keypoints.get("nose", {})
        l_eye = keypoints.get("left_eye", {})
        r_eye = keypoints.get("right_eye", {})
        l_ear = keypoints.get("left_ear", {})
        r_ear = keypoints.get("right_ear", {})
        l_shoulder = keypoints.get("left_shoulder", {})
        r_shoulder = keypoints.get("right_shoulder", {})
        
        # Need at least nose + one eye to estimate anything
        if not nose.get("visible") or not (l_eye.get("visible") or r_eye.get("visible")):
            return HeadPoseResult(pitch=0, yaw=0, roll=0, looking_away=False, violation=None)
        
        # ── YAW estimation (left/right head turn) ────────────────
        yaw = self._estimate_yaw(nose, l_eye, r_eye, l_ear, r_ear)
        
        # ── PITCH estimation (up/down) ───────────────────────────
        pitch = self._estimate_pitch(nose, l_eye, r_eye, l_shoulder, r_shoulder)
        
        # ── ROLL estimation (head tilt) ──────────────────────────
        roll = self._estimate_roll(l_eye, r_eye, l_shoulder, r_shoulder)
        
        # ── Determine if looking away ────────────────────────────
        is_turned = abs(yaw) > _YAW_LIMIT or abs(pitch) > _PITCH_LIMIT
        
        if is_turned:
            self._turned_counter += 1
        else:
            self._turned_counter = 0
        
        actually_turned = is_turned and self._turned_counter >= _HEAD_TURN_DEBOUNCE
        violation = "HEAD_TURNED" if actually_turned else None
        
        return HeadPoseResult(
            pitch=round(pitch, 1),
            yaw=round(yaw, 1),
            roll=round(roll, 1),
            looking_away=actually_turned,
            violation=violation
        )
    
    def _estimate_yaw(self, nose, l_eye, r_eye, l_ear, r_ear) -> float:
        """
        Estimate yaw angle using multiple cues:
        1. Nose position relative to eye midpoint
        2. Ear visibility asymmetry (strong cue!)
        """
        yaw = 0.0
        
        # Method 1: Nose offset from eye midpoint
        if l_eye.get("visible") and r_eye.get("visible"):
            eye_mid_x = (l_eye["x"] + r_eye["x"]) / 2
            eye_dist = abs(r_eye["x"] - l_eye["x"]) + 1e-6
            nose_offset = (nose["x"] - eye_mid_x) / eye_dist
            yaw = nose_offset * 60  # Approximate degrees
        elif l_eye.get("visible"):
            # Only left eye visible → head is turned right
            yaw = 30
        elif r_eye.get("visible"):
            # Only right eye visible → head is turned left
            yaw = -30
        
        # Method 2: Ear visibility (very reliable indicator)
        l_ear_vis = l_ear.get("visible", False)
        r_ear_vis = r_ear.get("visible", False)
        
        if l_ear_vis and not r_ear_vis:
            # Left ear visible, right ear hidden → head turned RIGHT
            yaw = max(yaw, 40)
        elif r_ear_vis and not l_ear_vis:
            # Right ear visible, left ear hidden → head turned LEFT
            yaw = min(yaw, -40)
        elif l_ear_vis and r_ear_vis:
            # Both ears visible → facing roughly forward
            # Use ear-to-nose distance ratio for fine-tuning
            l_ear_dist = abs(nose["x"] - l_ear["x"])
            r_ear_dist = abs(nose["x"] - r_ear["x"])
            total = l_ear_dist + r_ear_dist + 1e-6
            ratio = (r_ear_dist - l_ear_dist) / total
            ear_yaw = ratio * 50
            # Blend with eye-based yaw
            yaw = (yaw + ear_yaw) / 2
        
        return yaw
    
    def _estimate_pitch(self, nose, l_eye, r_eye, l_shoulder, r_shoulder) -> float:
        """Estimate pitch angle from vertical positions of keypoints."""
        pitch = 0.0
        
        # Use nose position relative to eyes
        eye_y = 0
        eye_count = 0
        if l_eye.get("visible"):
            eye_y += l_eye["y"]
            eye_count += 1
        if r_eye.get("visible"):
            eye_y += r_eye["y"]
            eye_count += 1
        
        if eye_count == 0:
            return 0.0
        
        eye_y /= eye_count
        
        # Nose-to-eye vertical ratio
        # In a neutral pose, nose is below eyes by ~35% of face height
        # Estimate face height from eye-shoulder distance or eye spacing
        if l_shoulder.get("visible") and r_shoulder.get("visible"):
            shoulder_y = (l_shoulder["y"] + r_shoulder["y"]) / 2
            face_ref = abs(shoulder_y - eye_y) + 1e-6
        else:
            # Fall back to inter-eye distance as reference
            if l_eye.get("visible") and r_eye.get("visible"):
                face_ref = abs(r_eye["x"] - l_eye["x"]) * 1.5 + 1e-6
            else:
                return 0.0
        
        nose_ratio = (nose["y"] - eye_y) / face_ref
        # Normal ratio is ~0.15-0.25. Deviation indicates pitch
        pitch = (nose_ratio - 0.20) * 150  # Scale to approximate degrees
        
        return max(-80, min(80, pitch))
    
    def _estimate_roll(self, l_eye, r_eye, l_shoulder, r_shoulder) -> float:
        """Estimate roll angle from eye/shoulder line tilt."""
        if l_eye.get("visible") and r_eye.get("visible"):
            dy = r_eye["y"] - l_eye["y"]
            dx = r_eye["x"] - l_eye["x"] + 1e-6
            return math.degrees(math.atan2(dy, dx))
        
        if l_shoulder.get("visible") and r_shoulder.get("visible"):
            dy = r_shoulder["y"] - l_shoulder["y"]
            dx = r_shoulder["x"] - l_shoulder["x"] + 1e-6
            return math.degrees(math.atan2(dy, dx))
        
        return 0.0
    
    # ── Legacy interface (MediaPipe fallback) ────────────────────
    def estimate_from_landmarks(self, landmarks: list[list], image_shape: tuple) -> HeadPoseResult:
        """Fallback: estimate from MediaPipe FaceMesh landmarks."""
        if not landmarks or len(landmarks) < 468:
            return HeadPoseResult(pitch=0, yaw=0, roll=0, looking_away=False, violation=None)
        
        try:
            # Use nose tip (1) vs face center
            nose = landmarks[1]
            l_cheek = landmarks[234]
            r_cheek = landmarks[454]
            chin = landmarks[152]
            l_eye_lm = landmarks[33]
            r_eye_lm = landmarks[263]
            
            face_cx = (l_cheek[0] + r_cheek[0]) / 2
            face_w = abs(r_cheek[0] - l_cheek[0]) + 1e-6
            
            yaw = ((nose[0] - face_cx) / face_w) * 60
            
            eye_mid_y = (l_eye_lm[1] + r_eye_lm[1]) / 2
            face_h = abs(chin[1] - eye_mid_y) + 1e-6
            pitch = ((nose[1] - eye_mid_y) / face_h - 0.35) * 80
            
            dy = r_eye_lm[1] - l_eye_lm[1]
            dx = r_eye_lm[0] - l_eye_lm[0] + 1e-6
            roll = math.degrees(math.atan2(dy, dx))
            
            is_turned = abs(yaw) > _YAW_LIMIT or abs(pitch) > _PITCH_LIMIT
            
            if is_turned:
                self._turned_counter += 1
            else:
                self._turned_counter = 0
            
            actually_turned = is_turned and self._turned_counter >= _HEAD_TURN_DEBOUNCE
            violation = "HEAD_TURNED" if actually_turned else None
            
            return HeadPoseResult(
                pitch=round(pitch, 1), yaw=round(yaw, 1), roll=round(roll, 1),
                looking_away=actually_turned, violation=violation
            )
        except (IndexError, TypeError):
            return HeadPoseResult(pitch=0, yaw=0, roll=0, looking_away=False, violation=None)
    
    def estimate(self, image: np.ndarray) -> HeadPoseResult:
        """Legacy interface."""
        return HeadPoseResult(pitch=0, yaw=0, roll=0, looking_away=False, violation=None)