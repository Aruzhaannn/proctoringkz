import cv2
import numpy as np
from fastapi import APIRouter, File, Form, UploadFile, HTTPException

from app.models.schemas import AnalyzeResponse, AudioAnalyzeResponse
from app.services.face_detector import FaceDetector
from app.services.gaze_analyzer import GazeAnalyzer
from app.services.head_pose_estimator import HeadPoseEstimator
from app.services.object_detector import ObjectDetector
from app.services.audio_detector import AudioDetector

router = APIRouter()

_face_detector   = FaceDetector()
_gaze_analyzer   = GazeAnalyzer()
_head_pose       = HeadPoseEstimator()
_object_detector = ObjectDetector()
_audio_detector  = AudioDetector()

# Violation weights for cheat score
_WEIGHTS: dict[str, int] = {
    "NO_FACE":           40,
    "MULTIPLE_FACES":    60,
    "PERSON_ABSENT":     40,
    "MULTIPLE_PERSONS":  50,
    "GAZE_AWAY":         20,
    "HEAD_TURNED":       25,
    "HEAD_NOT_DETECTED": 15,
    "PHONE_DETECTED":    70,
    "BOOK_DETECTED":     40,
    "VOICE_DETECTED":    30,
    "MULTIPLE_VOICES":   50,
}


def _cheat_score(violations: list[str]) -> int:
    return min(sum(_WEIGHTS.get(v, 10) for v in violations), 100)


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_frame(
    session_id: str = Form(...),
    frame: UploadFile = File(...),
):
    data = await frame.read()
    arr = np.frombuffer(data, np.uint8)
    image = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if image is None:
        raise HTTPException(status_code=400, detail="Invalid image")

    violations: list[str] = []

    # ── 1. Face detection (Haar Cascade) ──────────────────────────────────
    face_result = _face_detector.detect(image)
    if face_result.violation:
        violations.append(face_result.violation)

    gaze_direction = "unknown"
    looking_away   = False
    if face_result.face_count == 1:
        gaze = _gaze_analyzer.analyze(image, face_result.faces[0])
        gaze_direction = gaze.direction
        looking_away   = gaze.looking_away
        if gaze.violation:
            violations.append(gaze.violation)

    # ── 2. Head pose (MediaPipe FaceMesh) ─────────────────────────────────
    head = _head_pose.estimate(image)
    if head.violation:
        violations.append(head.violation)

    # ── 3. Object / person detection (YOLOv8) ─────────────────────────────
    obj = _object_detector.detect(image)
    violations.extend(obj.violations)

    score   = _cheat_score(violations)
    message = "OK" if not violations else ", ".join(violations)

    return AnalyzeResponse(
        exam_session_id=session_id,
        face_count=face_result.face_count,
        faces=face_result.faces,
        gaze_direction=gaze_direction,
        looking_away=looking_away,
        head_pitch=head.pitch,
        head_yaw=head.yaw,
        head_roll=head.roll,
        head_turned=head.looking_away,
        persons_detected=obj.persons_detected,
        detected_objects=obj.objects,
        violations=violations,
        cheat_score=score,
        message=message,
    )


@router.post("/analyze/audio", response_model=AudioAnalyzeResponse)
async def analyze_audio(
    session_id: str = Form(...),
    audio: UploadFile = File(...),
):
    data = await audio.read()
    result = _audio_detector.analyze(data)

    violations = [result.violation] if result.violation else []
    score   = _cheat_score(violations)
    message = "OK" if not violations else violations[0]

    return AudioAnalyzeResponse(
        exam_session_id=session_id,
        is_speaking=result.is_speaking,
        noise_level=result.noise_level,
        multiple_voices=result.multiple_voices,
        violations=violations,
        cheat_score=score,
        message=message,
    )