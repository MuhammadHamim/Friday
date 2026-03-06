from pathlib import Path
import threading

import pyaudio
from huggingface_hub import hf_hub_download
from piper.voice import PiperVoice

from config import PIPER_VOICE

# Voice model files cached here
_VOICES_DIR = Path(__file__).parent / "voices"
_VOICES_DIR.mkdir(exist_ok=True)

_VOICE_REPO = "rhasspy/piper-voices"


def _get_voice_file(repo_path: str, filename: str) -> Path:
    """Return local path to a voice file, downloading from HF if needed."""
    # HF hub nests files; check the actual nested path, not flat
    nested = _VOICES_DIR / repo_path / filename
    if nested.exists():
        return nested

    print(f"[Friday] Downloading voice file '{filename}'...")
    downloaded = hf_hub_download(
        repo_id=_VOICE_REPO,
        filename=f"{repo_path}/{filename}",
        local_dir=str(_VOICES_DIR),
    )
    return Path(downloaded)


def _load_voice() -> PiperVoice:
    """Download (if needed) and load the configured Piper voice model."""
    name = PIPER_VOICE             # e.g. "en_US-lessac-medium"
    lang_code, voice_name, quality = name.split("-")  # "en_US", "lessac", "medium"
    lang_short = lang_code.split("_")[0]              # "en"
    repo_path  = f"{lang_short}/{lang_code}/{voice_name}/{quality}"

    onnx_path = _get_voice_file(repo_path, f"{name}.onnx")
    _get_voice_file(repo_path, f"{name}.onnx.json")   # must sit beside .onnx

    print(f"[Friday] Loading Piper voice '{PIPER_VOICE}'...")
    model = PiperVoice.load(str(onnx_path))
    print("[Friday] Piper TTS ready.")
    return model


class Speaker:
    """Synthesizes text to speech and plays it through the default audio output."""

    def __init__(self):
        self._voice = _load_voice()
        self._pa    = pyaudio.PyAudio()
        self._lock  = threading.Lock()   # serializes concurrent TTS calls

    def speak(self, text: str) -> None:
        """
        Convert text to speech via Piper and play it.
        Thread-safe: concurrent callers queue behind each other.
        Blocks until audio finishes playing.
        """
        if not text.strip():
            return

        # Piper 1.4+ API: synthesize() yields AudioChunk objects
        chunks = list(self._voice.synthesize(text))
        if not chunks:
            return

        sample_rate = chunks[0].sample_rate
        audio_bytes = b"".join(chunk.audio_int16_bytes for chunk in chunks)

        with self._lock:
            stream = self._pa.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=sample_rate,
                output=True,
            )
            stream.write(audio_bytes)
            stream.stop_stream()
            stream.close()

    def cleanup(self):
        self._pa.terminate()
