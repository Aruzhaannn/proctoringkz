import cv2
import numpy as np
from dataclasses import dataclass
from ultralytics import YOLO


@dataclass
class FaceResult:
    face_count: int
    faces: list[dict]
    landmarks: list[list] | None   # MediaPipe FaceMesh landmarks (for gaze)
    pose_keypoints: list[dict] | None  # YOLO pose keypoints per person
    violation: str | None


# YOLO pose keypoint indices (COCO format)
_KP_NOSE       = 0
_KP_LEFT_EYE   = 1
_KP_RIGHT_EYE  = 2
_KP_LEFT_EAR   = 3
_KP_RIGHT_EAR  = 4
_KP_LEFT_SHOULDER  = 5
_KP_RIGHT_SHOULDER = 6

# Debounce: consecutive frames with no face before flagging
_NO_FACE_DEBOUNCE = 3


class FaceDetector:
    """
    Hybrid face detector:
    - YOLOv8s-pose for robust person detection + body/face keypoints
    - MediaPipe FaceMesh for detailed iris landmarks (gaze analysis only)
    
    YOLOv8-pose is much more robust than MediaPipe Face Detection for:
    - Detecting faces at various angles and distances
    - Handling partial occlusion
    - Accurate person counting
    """

    def __init__(self):
        # YOLOv8s-pose: detects persons + 17 COCO keypoints per person
        self._pose_model = YOLO("yolov8s-pose.pt")
        
        # MediaPipe FaceMesh — only for iris landmarks (gaze analysis)
        import mediapipe as mp
        self._mp_mesh = mp.solutions.face_mesh
        self._mesh = self._mp_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=3,
            refine_landmarks=True,       # Enable iris landmarks (468 → 478)
            min_detection_confidence=0.5,
            min_tracking_confidence=0.4
        )
        self._no_face_counter = 0

    def detect(self, image: np.ndarray) -> FaceResult:
        h, w = image.shape[:2]
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # ── 1. YOLOv8-pose: person detection + keypoints ─────────
        pose_results = self._pose_model(image, verbose=False, conf=0.40)[0]
        
        faces: list[dict] = []
        all_pose_keypoints: list[dict] = []
        
        if pose_results.keypoints is not None and len(pose_results.keypoints) > 0:
            for i, (box, kps) in enumerate(zip(pose_results.boxes, pose_results.keypoints)):
                conf = float(box.conf[0])
                if conf < 0.40:
                    continue
                
                # Extract keypoints for this person
                kp_data = kps.data[0]  # shape: (17, 3) — x, y, confidence
                kp_xy = kps.xy[0]      # shape: (17, 2) — x, y only
                
                # Get face bounding box from keypoints (nose + eyes + ears)
                face_kp_indices = [_KP_NOSE, _KP_LEFT_EYE, _KP_RIGHT_EYE, _KP_LEFT_EAR, _KP_RIGHT_EAR]
                face_points = []
                for idx in face_kp_indices:
                    kp_conf = float(kp_data[idx][2]) if kp_data.shape[1] > 2 else 1.0
                    if kp_conf > 0.3:  # keypoint is visible
                        face_points.append((float(kp_xy[idx][0]), float(kp_xy[idx][1])))
                
                if len(face_points) >= 3:  # need at least nose + 2 others
                    xs = [p[0] for p in face_points]
                    ys = [p[1] for p in face_points]
                    margin_x = (max(xs) - min(xs)) * 0.3
                    margin_y = (max(ys) - min(ys)) * 0.5
                    
                    fx = max(0, int(min(xs) - margin_x))
                    fy = max(0, int(min(ys) - margin_y))
                    fw = min(int(max(xs) - min(xs) + 2 * margin_x), w - fx)
                    fh = min(int(max(ys) - min(ys) + 2 * margin_y), h - fy)
                    
                    faces.append({
                        "x": fx, "y": fy, "w": fw, "h": fh,
                        "confidence": round(conf, 2),
                        "source": "yolo-pose"
                    })
                
                # Store keypoints for head pose estimation
                keypoint_dict = {
                    "person_conf": round(conf, 2),
                    "nose":            _extract_kp(kp_data, kp_xy, _KP_NOSE),
                    "left_eye":        _extract_kp(kp_data, kp_xy, _KP_LEFT_EYE),
                    "right_eye":       _extract_kp(kp_data, kp_xy, _KP_RIGHT_EYE),
                    "left_ear":        _extract_kp(kp_data, kp_xy, _KP_LEFT_EAR),
                    "right_ear":       _extract_kp(kp_data, kp_xy, _KP_RIGHT_EAR),
                    "left_shoulder":   _extract_kp(kp_data, kp_xy, _KP_LEFT_SHOULDER),
                    "right_shoulder":  _extract_kp(kp_data, kp_xy, _KP_RIGHT_SHOULDER),
                }
                all_pose_keypoints.append(keypoint_dict)

        face_count = len(faces)

        # ── 2. MediaPipe FaceMesh: iris landmarks for gaze ────────
        mesh_result = self._mesh.process(rgb)
        landmarks = None
        
        if mesh_result.multi_face_landmarks:
            # Use first face's landmarks for gaze analysis
            first = mesh_result.multi_face_landmarks[0]
            landmarks = [
                [lm.x * w, lm.y * h, lm.z * w]
                for lm in first.landmark
            ]
            
            # If YOLO found 0 faces but FaceMesh found some, use FaceMesh count
            if face_count == 0:
                face_count = len(mesh_result.multi_face_landmarks)
                for fl in mesh_result.multi_face_landmarks:
                    xs = [lm.x * w for lm in fl.landmark]
                    ys = [lm.y * h for lm in fl.landmark]
                    x = max(0, int(min(xs)))
                    y = max(0, int(min(ys)))
                    fw = int(max(xs) - min(xs))
                    fh = int(max(ys) - min(ys))
                    faces.append({"x": x, "y": y, "w": fw, "h": fh,
                                  "confidence": 0.5, "source": "mediapipe"})

        # ── 3. Determine violations ──────────────────────────────
        violation = None
        if face_count == 0:
            self._no_face_counter += 1
            if self._no_face_counter >= _NO_FACE_DEBOUNCE:
                violation = "NO_FACE"
        else:
            self._no_face_counter = 0
            if face_count > 1:
                violation = "MULTIPLE_FACES"

        return FaceResult(
            face_count=face_count,
            faces=faces,
            landmarks=landmarks,
            pose_keypoints=all_pose_keypoints if all_pose_keypoints else None,
            violation=violation
        )


def _extract_kp(kp_data, kp_xy, idx: int) -> dict:
    """Extract a single keypoint as {x, y, conf}."""
    conf = float(kp_data[idx][2]) if kp_data.shape[1] > 2 else 0.0
    return {
        "x": float(kp_xy[idx][0]),
        "y": float(kp_xy[idx][1]),
        "conf": round(conf, 2),
        "visible": conf > 0.3
    }