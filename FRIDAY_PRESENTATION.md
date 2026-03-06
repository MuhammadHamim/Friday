# FRIDAY — Progress Presentation Slides

> **Duration:** 5–8 minutes
> **Date:** Wednesday, March 11, 2026

---

> ### How to use this file
> Each section = one slide.
> **SLIDE TITLE** → use as the slide heading.
> **Bullet points** → use as slide content (keep minimal on slide — expand verbally).
> **[SPEAKER NOTE]** → what to say out loud; do NOT put on slide.

---

## SLIDE 1 — Title Slide

**Title:** FRIDAY
**Subtitle:** Friendly Robotic Intelligence for Daily Assistance, Yeah!

**Visual suggestion:** A dramatic render or photo of the robotic arm on a desk, with glowing blue accents (Tony Stark / Iron Man aesthetic).

**Team:** [Team Name / University / Department]
**Date:** March 2026

---

[SPEAKER NOTE]
> "Good [morning/afternoon]. Today we're presenting our progress on FRIDAY — an AI-powered robotic arm desk assistant. Think of it as your own personal desk robot that you talk to naturally and it physically helps you. In the next few minutes we'll walk you through what we've built, what we're still building, and where we're headed."

---

## SLIDE 2 — The Problem & Motivation

**Title:** Why FRIDAY?

**Content:**
- Everyday desk tasks — fetching a pen, handing an item — require physical interruption to your workflow
- Voice assistants today (Siri, Alexa) can only *talk* — they cannot *act*
- Robotics today is expensive, cloud-dependent, and complex to set up
- **Our goal:** A smart, affordable, offline desk assistant that listens, understands, and physically acts

**Visual suggestion:** Split image — left: someone frustrated reaching across a desk; right: FRIDAY arm elegantly handing them a pen.

---

[SPEAKER NOTE]
> "The core problem we're solving is simple: current voice assistants are limited to words. They can tell you where your pen is, but they can't hand it to you. FRIDAY bridges that gap — it understands your natural voice commands and physically carries them out. And it runs fully offline — no cloud, no subscription, no data leaving your desk."

---

## SLIDE 3 — What is FRIDAY?

**Title:** FRIDAY — System Overview

**Content (use a visual diagram, not bullet points):**

```
VOICE  →  UNDERSTAND  →  SEE  →  ACT
```

| Layer | What it does |
|-------|-------------|
| 🎙️ Voice | Listens for "Hey Friday", records your command |
| 🧠 Understand | Transcribes speech, runs AI to understand intent |
| 👁️ See | Detects where objects are on your desk (camera + AI) |
| 🦾 Act | Commands the robotic arm to move and grasp |

**Visual suggestion:** A clean 4-block horizontal pipeline diagram with icons.

---

[SPEAKER NOTE]
> "FRIDAY has four core layers. First it listens — it's always waiting for the wake word 'Hey Friday', and only then activates. Second, it understands your command using speech recognition and AI. Third, it sees — a camera and an object detection model locate where the requested item actually is on the desk. And fourth, it acts — the robotic arm physically moves to that position."

---

## SLIDE 4 — Hardware

**Title:** Hardware Stack

**Content:**

| Component | Spec |
|-----------|------|
| 🖥️ Main Computer | Windows PC (dev) → Orange Pi 5 (16GB, final) |
| 🦾 Robotic Arm | 6-DOF, 3D-printed, 6× SG90 servo motors |
| ⚡ Arm Controller | ESP32-S3 microcontroller |
| 📷 Camera | USB Camera — 1280×720, 30 FPS |
| 🎤 Microphone | USB/system microphone |

**Visual suggestion:** Annotated photo of the actual hardware — arm, ESP32, camera, PC — all labeled.

---

[SPEAKER NOTE]
> "On the hardware side, we have a 6-DOF robotic arm that we 3D-printed in-house and equipped with 6 SG90 servo motors. An ESP32-S3 microcontroller acts as the arm's brain — it receives target coordinates from our software and drives the servos. A standard USB camera provides the vision, and a microphone handles voice input. Eventually this will all run on an Orange Pi 5 instead of a PC."

---

## SLIDE 5 — Software Architecture

**Title:** Software Stack — All Local, No Cloud

**Content:**

| What | How |
|------|-----|
| 🔊 Wake Word | Porcupine ("Hey Friday" custom model) |
| 📝 Speech-to-Text | faster-whisper (GPU-accelerated) |
| 🧠 Conversation AI | Ollama + phi3 (runs locally) |
| 🎯 Intent Classifier | Ollama + qwen2:1.5b (lightweight, fast) |
| 🔈 Voice Output | Piper TTS (natural voice synthesis) |
| 👁️ Object Detection | YOLOv11l (GPU, 30 FPS) |
| 🗺️ Object Tracker | Custom World Map (real-time positions) |
| 🦾 Task Execution | Python dispatcher → ESP32-S3 → Servos |

**Visual suggestion:** Layered block architecture diagram (voice → AI → vision → hardware).

---

[SPEAKER NOTE]
> "Everything runs locally — no internet connection is needed during operation. We use open-source models: faster-whisper for speech recognition, phi3 running through Ollama for conversation, and YOLOv11 for computer vision. A key design choice was keeping AI models small and fast enough to run on affordable hardware — which is critical for our Orange Pi 5 target."

---

## SLIDE 6 — What We Have Built ✅

**Title:** Progress — What's Done

**Content (use large checkmarks ✅, keep text minimal):**

✅ Wake word detection — "Hey Friday" (custom trained model)
✅ Voice recording with automatic silence detection (no buttons needed)
✅ Speech-to-text transcription (GPU, ~0.3s per sentence)
✅ Local LLM conversation (phi3, streaming replies)
✅ Natural voice output (Piper TTS)
✅ Real-time object detection (YOLOv11, 30 FPS, GPU)
✅ Object position tracking (World Map, IoU-based)
✅ Intent classification — understands FIND / GIVE / PICK / PLACE / MOVE
✅ Task execution framework (dispatches arm commands)
✅ Parallel pipeline (Friday speaks while arm executes)

**Visual suggestion:** Timeline or checklist graphic with green checkmarks. Maybe a progress bar at ~75%.

---

[SPEAKER NOTE]
> "We've completed the entire software pipeline — from wake word to task dispatch. Ten major components are done and working. The full voice pipeline has been tested: Friday wakes up, transcribes commands accurately, generates natural conversational replies via TTS, and simultaneously classifies the intent. The vision pipeline is live — the camera detects and tracks objects in real time at 30 frames per second, maintaining a live map of where everything on the desk is."

---

## SLIDE 7 — What We Are Completing Now 🔧

**Title:** In Progress — Arm Integration

**Content:**

🔧 **ESP32-S3 ↔ Software bridge** — sending target coordinates to the arm
🔧 **Inverse Kinematics** — computing servo angles from target position
🔧 **Full end-to-end test** — "Hey Friday, give me the pen" → arm actually moves

**Expected demo by Wednesday:**
1. Say "Hey Friday, give me the pen"
2. Friday responds: "Sure, let me find the pen for you"
3. YOLO finds the pen → gets pixel coordinates
4. Arm moves to the pen's position
5. Arm attempts to pick up and extend toward user

> ⚠️ Accuracy will not be perfect at this stage — that is expected and is our next focus.

**Visual suggestion:** A simple before/after comparison — "Before: arm sits still" vs "After: arm moves to detected object."

---

[SPEAKER NOTE]
> "The one remaining piece we're actively completing right now is wiring the arm into the pipeline. The software knows where objects are — we just need to send those coordinates to the ESP32-S3, which will drive the servos accordingly. We expect a working end-to-end demo by Wednesday. The arm movement may not be perfectly accurate at this stage — but the key milestone is that it moves and attempts the correct action. Accuracy is our very next engineering challenge after this presentation."

---

## SLIDE 8 — Live Pipeline Demo (Optional)

**Title:** How It Works — End-to-End

**Content (use a flow diagram):**

```
"Hey Friday, give me the pen"
          ↓
  [Wake Word Detected]
          ↓
  [Voice Recorded]  ← stops automatically after silence
          ↓
  [Whisper STT: "give me the pen"]
          ↓
    ┌─────┴──────┐
    ↓            ↓
[Intent: GIVE]  [phi3: "Sure, let me find..."]
[target: pen]       ↓
    ↓           [Piper TTS: speaks]
[World Map]
[pen_1 @ (640,380)]
    ↓
[ESP32-S3 → Arm moves → picks pen]
```

**Visual suggestion:** Animated build of this flow — reveal each step one by one during the slide.

---

[SPEAKER NOTE]
> "Here's the complete pipeline in action. The user says the wake word. Friday records the command and Whisper converts it to text in under half a second. Then two things happen in parallel — the intent classifier figures out what action to take, while phi3 starts generating a natural conversational reply that is spoken out loud immediately. Meanwhile, the world map provides the pen's location, and those coordinates go to the ESP32-S3 which drives the arm. The whole interaction from wake word to arm movement takes a few seconds."

---

## SLIDE 9 — Current Challenges

**Title:** Challenges We're Working Through

**Content:**

| Challenge | Status |
|-----------|--------|
| 🎯 **Object detection accuracy** | YOLO uses a generic 80-class model — not trained on our specific desk objects | Solving with custom dataset |
| 📐 **Coordinate calibration** | Camera pixels ≠ real-world coordinates — needs geometric mapping | Solving with camera calibration (checkerboard method) |
| 🤏 **Arm precision** | SG90 servos have positional error (~2°) — affects fine grasping | Mechanical + software improvements planned |
| 📏 **Depth estimation** | Single camera can't easily measure object distance | Investigating depth camera / object-size estimation |

**Visual suggestion:** 2×2 challenge card layout with icons.

---

[SPEAKER NOTE]
> "We want to be transparent about the challenges. The biggest one is that our YOLO model is a general-purpose model trained on 80 everyday classes like 'person', 'car', 'chair'. It works on common objects, but for precise desk-use cases — detecting a specific pen vs a pencil at an angle — we need to fine-tune it on our own dataset. The second challenge is coordinate calibration: the camera sees pixels, but the arm needs real-world distances. We're solving this with standard camera calibration techniques. Arm accuracy is a hardware challenge that improves with both mechanical refinement and software feedback loops."

---

## SLIDE 10 — How We're Solving Them

**Title:** Our Solutions

**Content:**

🔬 **Custom YOLO training** — Collect photos of desk objects, label them, fine-tune YOLOv11 with transfer learning (only last layers — fast to train)

📐 **Camera calibration** — Checkerboard calibration + OpenCV to map pixel coordinates to real-world XY coordinates at known desk height

🔁 **Closed-loop correction** — Use the camera as feedback: after the arm moves, check if the object is still visible and correct the approach

📷 **Depth camera (future)** — Intel RealSense or similar to get accurate 3D coordinates

**Visual suggestion:** Before/after comparison for object detection accuracy (generic COCO vs custom-trained on desk objects).

---

[SPEAKER NOTE]
> "Our plan for each challenge is grounded in standard engineering solutions. Fine-tuning YOLO on a custom dataset is a well-understood process — it should take less than an hour of training on our GPU for solid results. Calibration is a mathematical process with well-established tools in OpenCV. And closed-loop correction, where the camera verifies and guides the arm's final approach, is the industry-standard method for pick-and-place robotics."

---

## SLIDE 11 — Future Work & Roadmap

**Title:** What's Next

**Content:**

**Short term (next 2–4 weeks):**
- ✦ Arm accuracy improvement (calibration + custom model)
- ✦ Custom YOLO dataset for desk objects
- ✦ Full end-to-end accuracy testing

**Medium term:**
- ✦ Migrate to Orange Pi 5 + ROS2 Jazzy (full offline embedded deployment)
- ✦ Add depth camera for 3D object localization
- ✦ Multi-object reasoning ("the blue pen, not the red one")

**Long term:**
- ✦ Human detection & handover (arm extends toward user automatically)
- ✦ Session memory ("where did you put the stapler last time?")
- ✦ Expanded task set (writing assistance, object sorting, workspace organization)

**Visual suggestion:** A roadmap timeline graphic with phases marked. Maybe Phase 1 (Now), Phase 2 (Month 1), Phase 3 (Competition).

---

[SPEAKER NOTE]
> "Looking ahead, our immediate priority after this milestone is accuracy — both in vision and arm movement. In parallel, we'll migrate to the Orange Pi 5 and ROS2, which is the final deployment target. Longer term, we want FRIDAY to learn the workspace — to know where things usually are, to recognize the user's position, and to handle more complex multi-step tasks."

---

## SLIDE 12 — Summary / What We Want You to Remember

**Title:** In Short

**Content (large, bold, minimal):**

> 🎙️ Say "Hey Friday"
> 🧠 Friday understands
> 👁️ Friday sees where it is
> 🦾 Friday picks it up

**Completed:** Full AI voice + vision pipeline
**In progress:** Arm integration & accuracy
**Goal:** Full autonomous pick-and-place by competition day

**Visual suggestion:** The 4-step tagline in large text with the arm photo.

---

[SPEAKER NOTE]
> "To summarize — we've built a complete AI voice and vision pipeline. The system can hear you, understand your intent, and see where objects are on the desk. We're now completing the final connection: making the arm physically act on that knowledge. By the competition, we aim for a fully autonomous FRIDAY that can pick and hand over objects on your desk from a single voice command."

---

## SLIDE 13 — Thank You / Q&A

**Title:** Thank You

**Content:**
- Team: [5 members — names if desired]
- Project: FRIDAY — AI Robotic Arm Desk Assistant
- Contact: [if applicable]

**Big text: "Questions?"**

**Visual suggestion:** The team photo OR a close-up of the arm — something visually strong to end on.

---

## Appendix — Technical Details (if asked in Q&A)

### Q: Why Ollama + phi3 instead of ChatGPT?
Because phi3 runs fully offline on a PC and is fast enough for real-time conversation. No API cost, no internet dependency, no data sent to external servers.

### Q: Why YOLOv11 specifically?
YOLOv11l offers 53.4% mAP (detection accuracy) while remaining fast enough for 30 FPS real-time inference on our GPU. It's the latest generation of YOLO and supports fine-tuning well.

### Q: What is Inverse Kinematics?
When you know where you want the tip of the arm to go (a 3D coordinate in space), IK calculates the angle that each of the 6 servo joints must be at. It's solving geometry "backwards" — from the target position to the joint configuration.

### Q: Why ESP32-S3 and not STM32?
ESP32-S3 has both WiFi and Bluetooth built in, which gives us flexibility in how we communicate between the PC/Orange Pi and the arm (serial USB or wireless). It's also cheaper and easier to program with Arduino/MicroPython.

### Q: How does the World Map work?
Every camera frame, YOLO detects objects and outputs bounding boxes. Our World Map uses IoU (Intersection over Union) to match new detections to previously known objects, updating their positions. Objects that haven't been seen for 2 seconds are automatically removed. This gives the system a stable, continuously-updated "mental model" of what's on the desk.

---

*Presentation content prepared: March 7, 2026 | FRIDAY Team*
