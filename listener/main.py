"""
Friday Pipeline
---------------
Loop:
  1. Wait for 'Hey Friday' wake word
  2. Record voice until 1 s of silence
  3. Transcribe with Whisper
  4. Print the result
  5. Repeat

Run:
  ..\\fridayWake\\Scripts\\python.exe main.py
"""

from wake_detector import WakeWordDetector
from recorder import record_until_silence
from transcriber import Transcriber


def main():
    detector     = WakeWordDetector()
    transcriber  = Transcriber()

    print("\n[Friday] Pipeline ready. Say 'Hey Friday' to start.\n")

    try:
        while True:
            # ── Step 1: wake word ──────────────────────────────────────────
            detected = detector.listen()
            if not detected:
                break                   # KeyboardInterrupt inside listen()

            print("[Friday] Wake word detected!\n")

            # ── Step 2: record ─────────────────────────────────────────────
            audio = record_until_silence()

            # ── Step 3 & 4: transcribe + print ─────────────────────────────
            text = transcriber.transcribe(audio)
            if text:
                print(f"\n[You] {text}\n")
            else:
                print("[Friday] (nothing heard)\n")

    except KeyboardInterrupt:
        pass

    finally:
        detector.cleanup()
        print("[Friday] Shut down.")


if __name__ == "__main__":
    main()
