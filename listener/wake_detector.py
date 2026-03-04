import struct
import pvporcupine
import pyaudio

from config import ACCESS_KEY, MODEL_PATH, DEVICE_INDEX


class WakeWordDetector:
    """Blocks until 'Hey Friday' is detected, then returns."""

    def __init__(self):
        self._porcupine = pvporcupine.create(
            access_key=ACCESS_KEY,
            keyword_paths=[MODEL_PATH],
        )
        self._audio = pyaudio.PyAudio()

    def listen(self) -> bool:
        """Open mic, block until wake word detected or KeyboardInterrupt."""
        stream = self._audio.open(
            rate=self._porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            input_device_index=DEVICE_INDEX,
            frames_per_buffer=self._porcupine.frame_length,
        )
        print("[Friday] Waiting for wake word... say 'Hey Friday'")
        try:
            while True:
                pcm = stream.read(
                    self._porcupine.frame_length,
                    exception_on_overflow=False,
                )
                pcm = struct.unpack_from("h" * self._porcupine.frame_length, pcm)

                volume = max(abs(s) for s in pcm)
                bar = "#" * (volume // 2000)
                print(f"\rAudio level: {volume:5d} |{bar:<16}|", end="", flush=True)

                if self._porcupine.process(pcm) >= 0:
                    print()   # newline after the level bar
                    return True
        except KeyboardInterrupt:
            return False
        finally:
            stream.close()

    def cleanup(self):
        self._audio.terminate()
        self._porcupine.delete()
