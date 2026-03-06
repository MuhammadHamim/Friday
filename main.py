"""
Friday — AI Desk Assistant
--------------------------
Startup sequence:
  1. Warm up Ollama (blocks until model is resident in memory)
  2. Load Whisper STT
  3. Load Piper TTS
  4. Load YOLOv11
  5. Start camera node  → OpenCV window opens, world map begins updating
  6. Load intent parser
  7. Initialise wake word detector
  8. Enter wake word loop

Interaction loop (per wake word detection):
  a. Record voice until silence
  b. Transcribe with Whisper
  c. Launch two parallel threads:
       • Intent thread  — classifies utterance; if task, executes it async
       • Conversation thread — streams LLM reply sentence-by-sentence to TTS
  d. Wait for conversation to finish; intent/task runs freely in background
  e. Return to wake word listening

Run:
    .\\fridayWake\\Scripts\\python.exe main.py
"""

import sys
import threading
from pathlib import Path
from typing import Optional

# Ensure the friday_wake/ root is in sys.path so all sub-packages resolve config
sys.path.insert(0, str(Path(__file__).parent))

from wakeword.wake_detector  import WakeWordDetector
from listener.recorder       import record_until_silence
from listener.transcriber    import Transcriber
from llm.client              import warmup, ask
from tts.speaker             import Speaker
from vision.world_map        import WorldMap
from vision.yolo_engine      import YOLOEngine
from vision.camera_node      import CameraNode
from intent.intent_parser    import IntentParser
from task.task_executor      import TaskExecutor


# ── Interaction handler ───────────────────────────────────────────────────────

def _handle_interaction(
    text:          str,
    world_map:     WorldMap,
    speaker:       Speaker,
    intent_parser: IntentParser,
    task_executor: TaskExecutor,
) -> None:
    """
    Runs intent classification and LLM conversation in parallel.

    • Intent thread:       fast non-streaming Ollama call → dispatches task if needed
    • Conversation thread: streaming Ollama call → speaks each sentence via TTS

    The function blocks until the conversation is complete; the task (if any)
    continues on its own daemon thread and may speak after the conversation ends.
    """
    world_context = _summarize_world(world_map.get_snapshot())

    def _intent() -> None:
        intent = intent_parser.parse(text)
        print(
            f"[Intent] {intent.intent_type}  "
            f"target={intent.target_object!r}"
        )
        if intent.intent_type != "CHAT":
            task_executor.execute_async(intent)

    def _conversation() -> None:
        ask(text, on_sentence=speaker.speak, world_context=world_context)

    t_intent = threading.Thread(target=_intent,       name="IntentThread", daemon=True)
    t_conv   = threading.Thread(target=_conversation, name="ConvThread",   daemon=True)

    t_intent.start()
    t_conv.start()
    t_conv.join()   # wait for spoken reply to finish; intent/task run freely


def _summarize_world(snapshot: dict) -> Optional[str]:
    """Build a compact world-context string from the current world map snapshot."""
    if not snapshot:
        return None
    parts = [
        f"{obj.id} at ({int(obj.centroid[0])},{int(obj.centroid[1])})"
        for obj in snapshot.values()
    ]
    return "Visible on desk: " + "; ".join(parts) + "."


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    print("[Friday] ── Initializing all systems ──────────────────────────")

    # 1. Ollama warmup (blocking — model must be resident before first interaction)
    warmup()

    # 2. Whisper STT
    transcriber = Transcriber()

    # 3. Piper TTS
    speaker = Speaker()

    # 4. YOLOv11
    yolo = YOLOEngine()

    # 5. World map + camera node (starts immediately — OpenCV window opens here)
    world_map   = WorldMap()
    camera_node = CameraNode(world_map, yolo)
    camera_node.start()

    # 6. Intent parser
    intent_parser = IntentParser()

    # 7. Task executor
    task_executor = TaskExecutor(world_map, speaker.speak)

    # 8. Wake word detector
    detector = WakeWordDetector()

    print("\n[Friday] ── All systems ready. Say 'Hey Friday' to begin. ────\n")

    try:
        while True:
            if not detector.listen():
                break                          # Ctrl+C inside listen()

            print("[Friday] Wake word detected!\n")

            audio = record_until_silence()
            text  = transcriber.transcribe(audio)

            if not text:
                print("[Friday] (nothing heard)\n")
                continue

            print(f"[You]    {text}")
            _handle_interaction(text, world_map, speaker, intent_parser, task_executor)
            print()

    except KeyboardInterrupt:
        pass

    finally:
        world_map.clear()
        camera_node.stop()
        detector.cleanup()
        speaker.cleanup()
        print("\n[Friday] Shut down cleanly.")


if __name__ == "__main__":
    main()
