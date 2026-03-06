# FRIDAY — Project Overview & Technical Deep Dive

---

## 1. What is FRIDAY?

**FRIDAY** stands for **Friendly Robotic Intelligence for Daily Assistance, Yeah!**

It is an AI-powered robotic arm desk assistant — think Tony Stark's FRIDAY from the Iron Man films, but built for your desk. You talk to it naturally, it understands what you want, looks around using a camera, and physically picks up or hands you objects using a robotic arm.

**The one-line pitch:**
> *"You say 'give me the pen', FRIDAY finds the pen on your desk, and the arm picks it up and hands it to you."*

---

## 2. Project Goal

| Goal | Description |
|------|-------------|
| **Conversational AI** | Understand natural language commands, hold a conversation, and respond with a human voice |
| **Computer Vision** | Detect and track objects on a desk in real time using a camera |
| **Robotic Manipulation** | Physically pick up, place, or hand over objects via a 6-DOF robotic arm |
| **Always-On Listening** | Wake-word activated — only activates when the user says "Hey Friday" |
| **Edge-Ready** | Designed to eventually run fully offline on an Orange Pi 5 (no cloud) |

---

## 3. Hardware

| Component | Details |
|-----------|---------|
| **Main Computer** | Windows PC (development) → Orange Pi 5 16GB (final deployment) |
| **Robotic Arm** | 6-DOF arm, 3D-printed, powered by 6× SG90 servo motors |
| **Arm Controller** | ESP32-S3 microcontroller (receives commands from PC via serial/WiFi) |
| **Camera** | USB camera, 1280×720 resolution, 30 FPS |
| **Microphone** | USB/built-in microphone (system default) |
| **GPU** | NVIDIA RTX (for YOLO inference and Whisper transcription) |

---

## 4. Software Stack

Every component runs **locally** — no internet required during operation.

| Layer | Technology | What it Does |
|-------|-----------|--------------|
| **Wake Word** | Porcupine (Hey Friday `.ppn` model) | Listens always-on for "Hey Friday" |
| **Speech-to-Text** | faster-whisper (base model) | Converts voice → text after wake |
| **Language Model** | Ollama + phi3 | Powers conversation and replies |
| **Intent Classifier** | Ollama + qwen2:1.5b | Decides what action the user wants |
| **Text-to-Speech** | Piper TTS (en_US-lessac-medium) | Speaks Friday's replies out loud |
| **Object Detection** | YOLOv11l (GPU-accelerated) | Detects objects in camera frame |
| **Object Tracker** | Custom World Map (IoU-based) | Tracks object positions over time |
| **Task Executor** | Custom Python dispatcher | Translates intent → arm commands |
| **Arm Control** | ESP32-S3 + SG90 servos | Physically moves the arm |

---

## 5. System Architecture — How Everything Connects

```
User speaks "Hey Friday, give me the pen"
        │
        ▼
┌─────────────────────┐
│  Wake Word Detector  │  ← Porcupine runs always-on
│  "Hey Friday"        │    Uses < 1% CPU
└────────┬────────────┘
         │ detected
         ▼
┌─────────────────────┐
│  Voice Recorder     │  ← Records until 1 second of silence
│  VAD (silence det.) │    16kHz mono audio
└────────┬────────────┘
         │ audio buffer
         ▼
┌─────────────────────┐
│  Whisper STT        │  ← faster-whisper transcribes in ~0.3s
│  "give me the pen"  │    GPU-accelerated, English
└────────┬────────────┘
         │ text
         ├──────────────────────────────────┐
         ▼                                  ▼
┌─────────────────┐              ┌──────────────────────┐
│  Intent Parser  │              │  LLM Conversation    │
│  qwen2:1.5b     │              │  phi3 (streaming)    │
│  → GIVE, "pen"  │              │  → "Sure, let me..." │
└────────┬────────┘              └──────────┬───────────┘
         │                                  │ sentence-by-sentence
         ▼                                  ▼
┌─────────────────┐              ┌──────────────────────┐
│  Task Executor  │              │  Piper TTS           │
│                 │              │  Speaks each sentence│
│  1. Query       │              └──────────────────────┘
│     World Map   │
│  2. Find "pen"  │◄──── World Map: pen_1 at (640, 380)
│  3. Send coords │
│     to ESP32-S3 │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  ESP32-S3       │  ← Receives target coordinates
│  + SG90 Servos  │  ← Computes joint angles (IK)
│  ARM MOVES      │  ← Physically picks up the pen
└─────────────────┘
```

**Key design decision:** Intent classification and LLM conversation run **in parallel on separate threads**. This means Friday starts speaking a conversational reply _while simultaneously_ figuring out the physical task — making the system feel fast and natural.

---

## 6. What We Have Built (Completed)

### ✅ 1. Wake Word Detection
- Uses Picovoice Porcupine with a **custom "Hey Friday" voice model** (`.ppn` file trained for English Windows)
- Runs continuously in the background on near-zero CPU
- Only activates the full AI pipeline when the exact wake word is spoken

### ✅ 2. Voice Recording with VAD
- Records microphone audio at 16kHz (Whisper's native rate)
- Stops recording automatically after **1 second of silence** (no button needed)
- Safety cap: stops at 30 seconds maximum to prevent infinite recording

### ✅ 3. Speech-to-Text Transcription
- Uses **faster-whisper** (4-6× faster than original OpenAI Whisper, same accuracy)
- GPU-accelerated — transcribes a 5-second sentence in under 0.5 seconds
- English language, `base` model (fast + accurate enough for commands)

### ✅ 4. Conversational AI (LLM)
- Uses **Ollama** running **phi3** locally — no internet, no API keys, no cost
- Streams responses sentence-by-sentence to TTS so Friday starts speaking immediately
- Responds naturally in conversation while task execution runs in the background

### ✅ 5. Text-to-Speech Output
- Uses **Piper TTS** with `en_US-lessac-medium` voice — natural sounding, fast
- Each sentence from phi3 is spoken as soon as it is generated (streaming pipeline)

### ✅ 6. Object Detection (Computer Vision)
- Uses **YOLOv11l** — one of the most accurate YOLO variants available
- GPU-accelerated (~4ms per frame on our GPU)
- Camera feed: 1280×720 at 30 FPS with OpenCV window showing live detections

### ✅ 7. World Map (Object Tracker)
- Custom thread-safe object tracking using **IoU (Intersection over Union)** matching
- Assigns stable IDs to objects across frames (e.g. `pen_1`, `cup_2`)
- Automatically evicts objects not seen for 2 seconds (stale object removal)
- Provides a real-time snapshot: `{label, bbox, centroid, confidence, last_seen}`

### ✅ 8. Intent Classification
- Uses **qwen2:1.5b** (a small, fast LLM) via Ollama for intent parsing
- Classifies every user command into one of 6 intent types:

| Intent | Example Command |
|--------|----------------|
| `CHAT` | "What's the weather like?" |
| `FIND` | "Where is my pen?" |
| `PICK` | "Pick up the cup" |
| `PLACE` | "Put the pen on the left" |
| `GIVE` | "Give me the notebook" |
| `MOVE_ARM` | "Move your arm to the right" |

- Returns structured JSON: `{"intent_type": "GIVE", "target_object": "pen"}`
- Falls back to `CHAT` safely on any classifier error

### ✅ 9. Task Executor Framework
- Receives intent → queries world map for the target object → dispatches the action
- Currently announces actions via TTS and logs to a live dashboard
- Framework is complete — **arm command sending is being wired in now**

### ✅ 10. Concurrent Pipeline Architecture
- Intent thread and Conversation thread run **in parallel** (Python threading)
- Friday speaks its reply while the task executes in background
- Non-blocking, responsive, no awkward waiting

---

## 7. What Is Being Completed Before the Presentation

### 🔧 ESP32-S3 + Arm Integration
- The 6-DOF SG90 arm is assembled and the ESP32-S3 is programmed to receive commands
- The `task_executor.py` is being updated to send target coordinates (from world map) to the ESP32-S3 via serial/WiFi
- The ESP32-S3 computes Inverse Kinematics (IK) to determine servo angles and drives the arm

**Expected demo flow by Wednesday:**
1. "Hey Friday, give me the pen" → Friday says "Looking for the pen..."
2. YOLO detects pen → World map gives pixel coordinates
3. Coordinates sent to ESP32-S3 → arm moves to that position
4. Arm attempts to grasp and hand over (may not be perfectly accurate yet — that's expected)

---

## 8. Current Challenges

| Challenge | Description | Severity |
|-----------|-------------|----------|
| **General object detection** | YOLO is trained on 80 generic COCO classes (person, car, etc.) — not on desk-specific items like "our specific pen" or "stapler on the desk". Detection may be inconsistent for non-standard items | High |
| **Coordinate calibration** | Camera gives pixel coordinates; the arm needs real-world 3D coordinates. Mapping pixels → real-world requires camera calibration (intrinsics + extrinsics) | High |
| **Arm precision** | SG90 servos are inexpensive and have some positional error (~2°). Exact pick-up requires precise positioning that SG90s may struggle with for small objects | Medium |
| **No depth information** | Single 2D camera cannot determine object distance (depth) reliably — the arm needs depth to know how far to extend | Medium |
| **Platform migration** | Currently on Windows PC. Final target is Orange Pi 5 running ROS2 Jazzy, which requires adaptation | Low (future) |

---

## 9. How We Plan to Solve Them

| Challenge | Solution Plan |
|-----------|---------------|
| General object detection | Fine-tune YOLOv11 on a custom dataset of desk objects (pen, cup, notebook, etc.) using transfer learning. This keeps training fast (only the last layers) |
| Coordinate calibration | Camera calibration using a checkerboard pattern + OpenCV `calibrateCamera()`. Map pixel centroid to real-world XY using known camera height |
| Arm precision | Mechanical improvements (tighter joints, better servo linkages). Software: closed-loop correction using camera feedback |
| Depth estimation | Add a depth camera (Intel RealSense or similar) OR use stereo vision from two cameras OR estimate depth from object size using known reference objects |
| Platform migration | Use ROS2 Jazzy on Orange Pi 5 — all Python modules are already designed as ROS2-compatible node structures |

---

## 10. Future Work

- **Custom object detection model**: Train YOLO on desk-specific dataset for reliable detection of exact objects
- **3D spatial awareness**: Integrate depth camera for accurate 3D coordinate extraction
- **ROS2 deployment**: Migrate all Python modules to proper ROS2 nodes, topics, and services on Orange Pi 5
- **Improved arm design**: Upgrade from SG90 to higher-torque servos for heavier objects
- **Multi-object reasoning**: Handle "give me the blue pen, not the red one" — color/shape discrimination
- **Human detection**: Use YOLO's person detection to know _where_ the user is and extend the arm toward them for handover
- **Memory and context**: Let Friday remember what was placed where across sessions

---

## 11. Technology Glossary (for non-technical audience)

| Term | Plain English |
|------|---------------|
| **Wake word** | Like "Hey Siri" or "OK Google" — the trigger word "Hey Friday" activates the system |
| **STT (Speech-to-Text)** | Converts your spoken voice into written text the computer can process |
| **LLM (Large Language Model)** | The AI brain that understands language and generates human-like replies (like ChatGPT, but running locally) |
| **TTS (Text-to-Speech)** | Converts the AI's text reply back into spoken audio output |
| **YOLO** | "You Only Look Once" — a real-time object detection model that processes a camera frame and identifies where objects are |
| **World Map** | Our internal memory of what objects are visible and where they are right now |
| **Intent** | The system's understanding of _what action the user wants_ (find, pick, give, etc.) |
| **IK (Inverse Kinematics)** | Math that calculates what angles each servo motor must be at to move the arm tip to a target position |
| **ESP32-S3** | A small, affordable microcontroller that controls the servo motors of the arm |
| **IoU** | A measurement used to decide if two detected boxes are the same object in different frames |

---

*Document prepared: March 7, 2026 | FRIDAY Team (5 members)*
