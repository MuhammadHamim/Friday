# ─── Porcupine Wake Word ─────────────────────────────────────────────────────
ACCESS_KEY   = "DVy4O8aZO1YB+gK1IyrmdkonnfK4kxPJpxjCoTKeEGd82BhvstkMVA=="
DEVICE_INDEX = None           # None = system default microphone

# ─── Whisper (faster-whisper) ────────────────────────────────────────────────
WHISPER_MODEL = "base"        # tiny | base | small | medium | large
WHISPER_LANG  = "en"          # None for auto-detect

# ─── Audio Recording ─────────────────────────────────────────────────────────
SAMPLE_RATE        = 16000    # Hz (Whisper native rate)
CHANNELS           = 1        # mono
CHUNK_SECONDS      = 0.1      # seconds per read chunk
SILENCE_THRESHOLD  = 500      # RMS below this = silence
SILENCE_DURATION   = 1.0      # seconds of consecutive silence → stop recording
MAX_RECORD_SECONDS = 30       # safety cap: abort recording after this long

# ─── Ollama ──────────────────────────────────────────────────────────────────
OLLAMA_URL   = "http://localhost:11434"
OLLAMA_MODEL = "phi3"

# ─── Piper TTS ───────────────────────────────────────────────────────────────
PIPER_VOICE = "en_US-lessac-medium"  # voice model to download & use

# ─── YOLOv11 Vision ──────────────────────────────────────────────────────────
# yolo11l.pt: 53.4% mAP@50-95 — best accuracy/efficiency for RTX 5060
# Alternatives: yolo11m.pt (51.5% mAP, faster) | yolo11x.pt (54.7% mAP, slower)
YOLO_MODEL      = "yolo11l.pt"
YOLO_CONFIDENCE = 0.40          # minimum detection confidence threshold
YOLO_IOU        = 0.45          # NMS IoU threshold
YOLO_DEVICE     = "auto"        # "auto" → CUDA if available, else CPU
YOLO_CLASSES    = None          # None = all 80 COCO classes

# ─── Camera ──────────────────────────────────────────────────────────────────
CAMERA_INDEX  = 0               # 0 = first camera; change to 1 if Logitech not detected
CAMERA_WIDTH  = 1280
CAMERA_HEIGHT = 720
CAMERA_FPS    = 30

# ─── World Map ───────────────────────────────────────────────────────────────
WORLD_MAP_IOU_THRESHOLD = 0.30  # min IoU to treat detections as same object
WORLD_MAP_STALE_SECONDS = 2.0   # seconds before unseen object is evicted

# ─── Intent Classification ────────────────────────────────────────────────────
# Intent model: use a small/fast model. Pull first: ollama pull qwen2:1.5b
# Fallback: set to OLLAMA_MODEL (phi3) if qwen2:1.5b is not pulled yet.
INTENT_MODEL   = "qwen2:1.5b"   # lightweight model for fast JSON classification
INTENT_TIMEOUT = 8.0            # seconds before intent call times out

# ─── Task Logging ─────────────────────────────────────────────────────────────
TASK_LOG_PATH  = "logs/tasks.log"  # task dashboard tails this file
