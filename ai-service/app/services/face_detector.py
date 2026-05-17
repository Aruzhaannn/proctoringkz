"""
Face & person detection using YOLOv8-pose (primary) + MediaPipe FaceMesh (landmarks).

YOLOv8-pose → person count, bounding boxes, 17 COCO pose keypoints (for head pose)
MediaPipe FaceMesh → 478 face landmarks including iris (for gaze analysis)
"""

import cv2
import numpy as np
import mediapipe as mp
from dataclasses import dataclass, field
from ultralytics import YOLO


@dataclass
class FaceDetectionResult:
    face_count: int = 0
    faces: list[dict] = field(default_factory=list)
    landmarks: list[list] | None = None        # 478 MediaPipe landmarks [x, y, z]
    pose_keypoints: list[list] | None = None    # YOLO-pose 17 keypoints per person
    violation: str | None = None


class FaceDetector:
    """
    Hybrid detector:
    1) YOLOv8-pose — fast person detection + 17 COCO pose keypoints
       (nose, eyes, ears, shoulders, etc.) → used for head pose estimation
    2) MediaPipe FaceMesh — 478 face landmarks with iris refinement
       → used for gaze analysis (iris tracking)

    This combines YOLO's robustness for person/pose with MediaPipe's
    precision for face mesh and iris landmarks.
    """

    def __init__(
        self,
        yolo_model: str = "yolov8n-pose.pt",
        max_faces: int = 5,
        person_conf: float = 0.40,
        min_detection_confidence: float = 0.5,
    ):
        # ── YOLOv8-pose for person detection + keypoints ──
        self._yolo = YOLO(yolo_model)
        self._person_conf = person_conf

        # ── MediaPipe FaceMesh for detailed face landmarks (iris) ──
        self._face_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=max_faces,
            refine_landmarks=True,       # enables iris landmarks (468-477)
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=0.5,
        )

    def detect(self, image: np.ndarray) -> FaceDetectionResult:
        """
        Detect faces/persons in a BGR image.

        Pipeline:
        1. YOLOv8-pose → person bboxes + pose keypoints
        2. MediaPipe FaceMesh → face landmarks (for primary face)
        3. Combine results → FaceDetectionResult

        Returns:
            FaceDetectionResult with face count, bboxes, landmarks, keypoints, violation
        """
        h, w = image.shape[:2]

        # ═══════════════════════════════════════════════════════
        # Stage 1: YOLOv8-pose — person detection + keypoints
        # ═══════════════════════════════════════════════════════
        yolo_results = self._yolo(image, conf=self._person_conf, verbose=False)

        faces = []
        all_keypoints = []

        for result in yolo_results:
            if result.boxes is None:
                continue

            for i, box in enumerate(result.boxes):
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])

                # Only person class (COCO id=0)
                if cls_id != 0:
                    continue

                xyxy = box.xyxy[0].cpu().numpy()
                faces.append({
                    "x": int(xyxy[0]),
                    "y": int(xyxy[1]),
                    "width": int(xyxy[2] - xyxy[0]),
                    "height": int(xyxy[3] - xyxy[1]),
                    "confidence": round(conf, 2),
                })

                # Extract pose keypoints (17 COCO keypoints: [x, y, conf])
                if result.keypoints is not None and i < len(result.keypoints):
                    kp = result.keypoints[i]
                    if kp.data is not None and kp.data.shape[-1] >= 2:
                        kp_data = kp.data[0].cpu().numpy()  # shape: (17, 3)
                        all_keypoints.append(kp_data.tolist())

        face_count = len(faces)

        # ═══════════════════════════════════════════════════════
        # Stage 2: MediaPipe FaceMesh — detailed face landmarks
        # ═══════════════════════════════════════════════════════
        primary_landmarks = None

        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        mesh_results = self._face_mesh.process(rgb)

        if mesh_results.multi_face_landmarks:
            # Use the first face's landmarks for gaze analysis
            first_face = mesh_results.multi_face_landmarks[0]
            primary_landmarks = [
                [lm.x * w, lm.y * h, lm.z * w]
                for lm in first_face.landmark
            ]

            # If YOLO didn't detect any person but MediaPipe found a face,
            # count at least 1 face (person might be too close for YOLO)
            if face_count == 0:
                face_count = len(mesh_results.multi_face_landmarks)
                # Add a face entry from MediaPipe landmarks
                xs = [pt[0] for pt in primary_landmarks]
                ys = [pt[1] for pt in primary_landmarks]
                faces.append({
                    "x": int(min(xs)),
                    "y": int(min(ys)),
                    "width": int(max(xs) - min(xs)),
                    "height": int(max(ys) - min(ys)),
                    "confidence": 0.90,
                })

        # ═══════════════════════════════════════════════════════
        # Stage 3: Determine violation
        # ═══════════════════════════════════════════════════════
        violation = None
        if face_count == 0:
            violation = "NO_FACE"
        elif face_count >= 2:
            violation = "MULTIPLE_FACES"

        return FaceDetectionResult(
            face_count=face_count,
            faces=faces,
            landmarks=primary_landmarks,
            pose_keypoints=all_keypoints if all_keypoints else None,
            violation=violation,
        )
