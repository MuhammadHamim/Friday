import struct
import sys
import pvporcupine
import pyaudio


class WakeWordDetector:
    """
    Production-ready Porcupine wake word detector.
    Blocks until wake word detected.
    Returns True when detected.
    """

    def __init__(self, access_key: str, model_path: str, device_index: int = None):
        self.access_key = access_key
        self.model_path = model_path

        self.porcupine = pvporcupine.create(
            access_key=self.access_key,
            keyword_paths=[self.model_path]
        )

        self.audio = pyaudio.PyAudio()

        self.stream = self.audio.open(
            rate=self.porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=self.porcupine.frame_length,
        )

    def listen(self) -> bool:
        print("Listening for wake word... Say 'Hey Friday'")
        try:
            while True:
                pcm = self.stream.read(
                    self.porcupine.frame_length,
                    exception_on_overflow=False
                )

                pcm = struct.unpack_from(
                    "h" * self.porcupine.frame_length,
                    pcm
                )

                # Show audio level so you can confirm mic is working
                volume = max(abs(s) for s in pcm)
                bar = "#" * (volume // 2000)
                print(f"\rAudio level: {volume:5d} |{bar:<16}|", end="", flush=True)

                result = self.porcupine.process(pcm)

                if result >= 0:
                    print()
                    return True

        except KeyboardInterrupt:
            return False

        finally:
            self.cleanup()

    def cleanup(self):
        if self.stream:
            self.stream.close()
        if self.audio:
            self.audio.terminate()
        if self.porcupine:
            self.porcupine.delete()


if __name__ == "__main__":
    ACCESS_KEY = "DVy4O8aZO1YB+gK1IyrmdkonnfK4kxPJpxjCoTKeEGd82BhvstkMVA=="
    MODEL_PATH = "models/Hey-Friday_en_windows_v4_0_0.ppn"

    # List available input devices
    p = pyaudio.PyAudio()
    print("Available microphones:")
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        if info["maxInputChannels"] > 0:
            marker = " <-- default" if i == p.get_default_input_device_info()["index"] else ""
            print(f"  [{i}] {info['name']}{marker}")
    p.terminate()

    # Set DEVICE_INDEX to the index of your microphone, or leave as None for default
    DEVICE_INDEX = None

    detector = WakeWordDetector(
        access_key=ACCESS_KEY,
        model_path=MODEL_PATH,
        device_index=DEVICE_INDEX,
    )

    detected = detector.listen()

    if detected:
        print("Wake word detected!")
        sys.exit(0)

    sys.exit(1)