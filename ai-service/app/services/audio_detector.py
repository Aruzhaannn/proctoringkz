import io
import numpy as np
import soundfile as sf
import librosa
from dataclasses import dataclass


@dataclass
class AudioResult:
    is_speaking: bool
    noise_level: float      # 0.0 – 1.0 normalised RMS
    multiple_voices: bool
    violation: str | None


_SILENCE_RMS   = 0.008
_SPEAKING_RMS  = 0.025


class AudioDetector:
    """
    Analyses a raw audio chunk (WAV/FLAC/OGG bytes) for:
      - Voice activity (student is speaking)
      - Possible multiple voices (background conversation)
    """

    def analyze(self, audio_bytes: bytes) -> AudioResult:
        try:
            audio, sr = sf.read(io.BytesIO(audio_bytes), always_2d=False)
        except Exception:
            return AudioResult(is_speaking=False, noise_level=0.0,
                               multiple_voices=False, violation=None)

        if audio.ndim > 1:
            audio = audio.mean(axis=1)

        audio = audio.astype(np.float32)
        rms = float(np.sqrt(np.mean(audio ** 2)))
        noise_level = min(rms / 0.1, 1.0)   # normalise to ~0-1

        is_speaking = rms > _SPEAKING_RMS
        multiple_voices = False

        # Heuristic: multiple concurrent voices create higher spectral complexity
        if is_speaking and len(audio) >= sr // 2:
            try:
                zcr_var = float(np.var(librosa.feature.zero_crossing_rate(audio)[0]))
                flatness = float(np.mean(librosa.feature.spectral_flatness(y=audio)))
                multiple_voices = zcr_var > 0.005 and flatness > 0.08
            except Exception:
                pass

        violation: str | None = None
        if multiple_voices:
            violation = "MULTIPLE_VOICES"
        elif is_speaking:
            violation = "VOICE_DETECTED"

        return AudioResult(
            is_speaking=is_speaking,
            noise_level=round(noise_level, 3),
            multiple_voices=multiple_voices,
            violation=violation,
        )