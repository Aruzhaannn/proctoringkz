import cv2
import numpy as np
import mediapipe as mp
from dataclasses import dataclass


@dataclass
class FaceResult:
    face_count: int
    faces: list[dict]
    landmarks: list[list] | None   # raw landmark coords for first face (for gaze/head)
    violation: str | None


class FaceDetector:
    """MediaPipe Face Detection — much more accurate than Haar Cascade."""

    def __init__(self):
        self._mp_face = mp.solutions.face_detection
        self._detector = self._mp_face.FaceDetection(
            model_selection=1,       # 0 = short range (<2m), 1 = full range (<5m)
            min_detection_confidence=0.35
        )
        # Also keep FaceMesh for landmark extraction (gaze + head pose)
        self._mp_mesh = mp.solutions.face_mesh
        self._mesh = self._mp_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=5,
            refine_landmarks=True,
            min_detection_confidence=0.35,
            min_tracking_confidence=0.3
        )

    def detect(self, image: np.ndarray) -> FaceResult:
        h, w = image.shape[:2]
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # ── MediaPipe Face Detection (bounding boxes) ────────────
        det_result = self._detector.process(rgb)
        faces: list[dict] = []

        if det_result.detections:
            for det in det_result.detections:
                bbox = det.location_data.relative_bounding_box
                x = max(0, int(bbox.xmin * w))
                y = max(0, int(bbox.ymin * h))
                fw = min(int(bbox.width * w), w - x)
                fh = min(int(bbox.height * h), h - y)
                conf = round(det.score[0], 2) if det.score else 0.0
                faces.append({"x": x, "y": y, "w": fw, "h": fh, "confidence": conf})

        # ── MediaPipe Face Mesh (landmarks for first face) ───────
        mesh_result = self._mesh.process(rgb)
        landmarks = None
        mesh_face_count = 0

        if mesh_result.multi_face_landmarks:
            mesh_face_count = len(mesh_result.multi_face_landmarks)
            first = mesh_result.multi_face_landmarks[0]
            landmarks = [
                [lm.x * w, lm.y * h, lm.z * w]
                for lm in first.landmark
            ]
            # If face_detection found 0 but mesh found faces, use mesh count
            if len(faces) == 0 and mesh_face_count > 0:
                for fl in mesh_result.multi_face_landmarks:
                    xs = [lm.x * w for lm in fl.landmark]
                    ys = [lm.y * h for lm in fl.landmark]
                    x = max(0, int(min(xs)))
                    y = max(0, int(min(ys)))
                    fw = int(max(xs) - min(xs))
                    fh = int(max(ys) - min(ys))
                    faces.append({"x": x, "y": y, "w": fw, "h": fh, "confidence": 0.5})

        # Take the max of both detectors
        face_count = max(len(faces), mesh_face_count)

        violation = None
        if face_count == 0:
            violation = "NO_FACE"
        elif face_count > 1:
            violation = "MULTIPLE_FACES"

        return FaceResult(
            face_count=face_count,
            faces=faces,
            landmarks=landmarks,
            violation=violation
        )