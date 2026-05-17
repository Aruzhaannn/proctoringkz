from pydantic import BaseModel


class AnalyzeResponse(BaseModel):
    exam_session_id: str

    # Face (Haar Cascade)
    face_count: int
    faces: list[dict]

    # Gaze (Haar eye cascade)
    gaze_direction: str
    looking_away: bool
    gaze_h: float = 0.0
    gaze_v: float = 0.0

    # Head pose (MediaPipe)
    head_pitch: float
    head_yaw: float
    head_roll: float
    head_turned: bool

    # Object / person detection (YOLOv8)
    persons_detected: int
    detected_objects: list[dict]

    # Aggregated
    violations: list[str]
    cheat_score: int        # 0 – 100
    risk_level: str         # low | medium | high | critical
    detected_events: list[str]
    final_decision: str     # allow | warn | flag | terminate
    explanation: str
    message: str


class AudioAnalyzeResponse(BaseModel):
    exam_session_id: str
    is_speaking: bool
    noise_level: float
    multiple_voices: bool
    violations: list[str]
    cheat_score: int
    message: str