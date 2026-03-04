import pyaudio
import numpy as np

from config import (
    DEVICE_INDEX,
    SAMPLE_RATE,
    CHANNELS,
    CHUNK_SECONDS,
    SILENCE_THRESHOLD,
    SILENCE_DURATION,
    MAX_RECORD_SECONDS,
)


def record_until_silence() -> np.ndarray:
    """
    Record from the microphone until SILENCE_DURATION seconds of silence.
    Returns a float32 numpy array normalised to [-1, 1] at SAMPLE_RATE Hz.
    """
    chunk_size          = int(SAMPLE_RATE * CHUNK_SECONDS)
    silent_chunks_limit = int(SILENCE_DURATION / CHUNK_SECONDS)
    max_chunks          = int(MAX_RECORD_SECONDS / CHUNK_SECONDS)

    audio  = pyaudio.PyAudio()
    stream = audio.open(
        rate=SAMPLE_RATE,
        channels=CHANNELS,
        format=pyaudio.paInt16,
        input=True,
        input_device_index=DEVICE_INDEX,
        frames_per_buffer=chunk_size,
    )

    print("[Friday] Recording — speak now...")
    frames         = []
    silent_chunks  = 0
    speech_started = False   # don't count silence until voice is detected

    try:
        while len(frames) < max_chunks:
            data  = stream.read(chunk_size, exception_on_overflow=False)
            frames.append(data)

            chunk = np.frombuffer(data, dtype=np.int16)
            rms   = np.sqrt(np.mean(chunk.astype(np.float32) ** 2))

            if rms >= SILENCE_THRESHOLD:
                speech_started = True   # voice detected
                silent_chunks  = 0
            elif speech_started:        # only count silence after speech began
                silent_chunks += 1
                if silent_chunks >= silent_chunks_limit:
                    break
    finally:
        stream.close()
        audio.terminate()

    print("[Friday] Recording done.")

    raw = b"".join(frames)
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
