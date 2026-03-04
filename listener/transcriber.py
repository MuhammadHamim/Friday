import ctranslate2
import numpy as np
from faster_whisper import WhisperModel

from config import WHISPER_MODEL, WHISPER_LANG, SAMPLE_RATE


def _load_model() -> WhisperModel:
    """Try CUDA first; silently fall back to CPU if CUDA libs are missing."""
    if ctranslate2.get_cuda_device_count() > 0:
        try:
            print(f"[Friday] Loading Whisper '{WHISPER_MODEL}' on cuda...")
            model = WhisperModel(WHISPER_MODEL, device="cuda", compute_type="float16")
            # Probe: consume the generator to confirm CUDA libs are actually usable
            probe_segments, _ = model.transcribe(np.zeros(16000, dtype=np.float32))
            list(probe_segments)
            return model
        except RuntimeError as exc:
            print(f"[Friday] CUDA unavailable ({exc}). Falling back to CPU.")

    print(f"[Friday] Loading Whisper '{WHISPER_MODEL}' on cpu...")
    return WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")


class Transcriber:
    """Loads Whisper once; reused for every transcription call."""

    def __init__(self):
        self._model = _load_model()
        print("[Friday] Whisper ready.")

    def transcribe(self, audio: np.ndarray) -> str:
        """
        Accepts a float32 numpy array at SAMPLE_RATE Hz.
        Returns the transcribed text (empty string if nothing heard).
        """
        segments, _ = self._model.transcribe(
            audio,
            language=WHISPER_LANG,
            beam_size=5,
            vad_filter=True,        # skip silent leading/trailing audio
        )
        return " ".join(seg.text.strip() for seg in segments).strip()
