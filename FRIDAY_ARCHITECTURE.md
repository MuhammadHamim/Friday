# FRIDAY — AI-Powered Robotic Arm Desk Assistant

## Architecture & ROS2 System Design Document

> **Version:** 0.1.0  
> **Target Platform:** Orange Pi 5 (16GB) + STM32 + ROS2 Jazzy  
> **Language:** Python  
> **Codename:** FRIDAY (Friendly Robotic Intelligence for Daily Assistance, Yeah!)

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Hardware Architecture](#2-hardware-architecture)
3. [Camera Strategy](#3-camera-strategy)
4. [Software Stack](#4-software-stack)
5. [ROS2 Package Structure](#5-ros2-package-structure)
6. [ROS2 Nodes (14 Nodes)](#6-ros2-nodes)
7. [ROS2 Topics](#7-ros2-topics)
8. [ROS2 Services](#8-ros2-services)
9. [ROS2 Actions](#9-ros2-actions)
10. [Custom Interface Definitions](#10-custom-interface-definitions)
11. [Behavioral State Machine](#11-behavioral-state-machine)
12. [Data Flow Examples](#12-data-flow-examples)
13. [Phase-Based Development Plan](#13-phase-based-development-plan)

---

## 1. System Overview

FRIDAY is a desk-mounted AI-powered robotic arm assistant inspired by Tony Stark's AI companion. It combines:

- **Conversational AI** — natural language understanding, LLM-powered responses, pet-like attentive behavior
- **Computer Vision** — real-time object detection and scene understanding on the desk
- **Robotic Manipulation** — 6-DOF arm with gripper to pick, place, and hand objects to the user

### Design Principles (from project skills)

| Principle                           | Application                                                                               |
| ----------------------------------- | ----------------------------------------------------------------------------------------- |
| **Conversation-Manipulation Split** | Task Manager decides: chat-only path vs. arm-movement path                                |
| **Hardware Integration Discipline** | Drivers isolated from logic; topics for streams, services for queries, actions for motion |
| **KISS**                            | Simple readable nodes; no over-engineering                                                |
| **OOP & Reusability**               | Base classes for nodes; shared utilities                                                  |
| **ROS2 Modularity**                 | 1 node = 1 responsibility; communicate via pub/sub, services, actions                     |
| **Phase Workflow**                  | Perception → Cognition → Action → Feedback                                                |

---

## 2. Hardware Architecture

### 2.1 Compute

| Component                                  | Role             | Notes                                                                                                                                                                                                                                                                     |
| ------------------------------------------ | ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Orange Pi 5 Ultra / Orange Pi 5 (16GB)** | Main brain       | Runs Ubuntu 24.04 + ROS2 Jazzy. Handles all AI inference (LLM, STT, TTS, Vision). RK3588 SoC with 6 TOPS NPU for YOLO acceleration. 16GB RAM for LLM.                                                                                                                     |
| **STM32H7 (NUCLEO-H753ZI2)**               | Motor controller | Runs micro-ROS agent or custom serial protocol. Generates PWM for 6 servos (TIM channels). Reads HX711 load cell, VL53L5CX ToF (I2C), E-stop GPIO. Real-time servo loop at 50-100Hz. Connected via USB-Serial (VCP) to Orange Pi. Cortex-M7 @ 480MHz, 2MB Flash, 1MB RAM. |

### 2.2 Sensors & I/O

| Sensor                  | Model                             | Connection                    | Purpose                                                                                                                                                            |
| ----------------------- | --------------------------------- | ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Microphone Array**    | ReSpeaker 4-Mic Array             | USB to Orange Pi              | Always-on audio capture at 16kHz. 4-mic circular array with built-in VAD, DOA (direction of arrival), and noise suppression.                                       |
| **Camera**              | Logitech C920 (1080p)             | USB to Orange Pi              | Fixed on robot's "head/base". Provides desk overview for scene mapping and object detection via YOLOv8. Always-on at 720p for inference, 1080p available. 78° FOV. |
| **Speaker**             | USB / 3.5mm Speaker               | USB or audio jack             | TTS audio output via Piper TTS.                                                                                                                                    |
| **Load Cell**           | YZC133 Mini Load Cell + HX711 ADC | HX711 → STM32 GPIO (CLK+DATA) | Mounted in gripper. Detects object weight for grasp verification. Range: 0-500g typical desk objects.                                                              |
| **ToF Distance Sensor** | ST VL53L5CX (8×8 multi-zone)      | I2C → STM32                   | Mounted on gripper/wrist. 8×8 zone ranging (up to 4m). Used for approach distance, surface detection, and obstacle avoidance during grasping.                      |
| **Emergency Stop**      | Schneider XB2BS542                | STM32 GPIO (NC contact)       | Mushroom-head E-stop. STM32 monitors NC contact — when pressed, immediately disables all servo PWM outputs and publishes E-stop status.                            |

### 2.3 Actuators (6-DOF + Gripper)

| Joint # | Joint Name     | Servo Model | Torque   | Voltage  | Notes                                      |
| ------- | -------------- | ----------- | -------- | -------- | ------------------------------------------ |
| 1       | Base Yaw       | **DS3225**  | 25 kg-cm | 4.8-6.8V | Rotate left/right. Metal gear, 270° range. |
| 2       | Shoulder Pitch | **DS3225**  | 25 kg-cm | 4.8-6.8V | Lift up/down. Highest load joint.          |
| 3       | Elbow Pitch    | **DS3225**  | 25 kg-cm | 4.8-6.8V | Fold/extend forearm.                       |
| 4       | Wrist Pitch    | **DS3218**  | 20 kg-cm | 4.8-6.8V | Tilt gripper up/down.                      |
| 5       | Wrist Roll     | **DS3218**  | 20 kg-cm | 4.8-6.8V | Rotate gripper CW/CCW.                     |
| 6       | Gripper        | **DS3218**  | 20 kg-cm | 4.8-6.8V | Open/close. Load cell mounted here.        |

> **PWM Spec**: All servos use standard 50Hz PWM. Pulse width 500µs (0°) to 2500µs (270°). STM32H7 TIM1/TIM8 channels generate PWM.

### 2.4 Power Distribution

| Component            | Model                | Input   | Output        | Supplies                              |
| -------------------- | -------------------- | ------- | ------------- | ------------------------------------- |
| **Main PSU**         | Mean Well LRS-350-24 | 220V AC | 24V DC, 14.6A | Everything (master supply)            |
| **Orange Pi BEC**    | DROK 24V→5V 5A       | 24V     | 5V, 5A        | Orange Pi 5 (needs 5V/4A)             |
| **Sensor/Logic BEC** | LM2596 24V→5V 2-3A   | 24V     | 5V, 2-3A      | STM32, HX711, VL53L5CX, misc logic    |
| **Servo Supply**     | XL4015 24V→**6V** 5A | 24V     | **6V**, 5A    | All 6 servos (DS3225/DS3218 max 6.8V) |
| **E-Stop**           | Schneider XB2BS542   | —       | —             | Cuts servo power rail when pressed    |

> **IMPORTANT**: DS3225/DS3218 servos are rated 4.8-6.8V. Set the XL4015 output to **6.0V** (not 12V). If you need a 12V rail for other peripherals, add a separate regulator.

> **E-Stop Wiring**: Wire the XB2BS542 NC contact in series with the servo power rail AND connect to STM32 GPIO for software detection.

### 2.5 Wiring Summary

```
                    ┌─────────────────────────────────────────────────┐
  220V AC ──►│ Mean Well LRS-350-24 │──► 24V DC Bus ──┬─────────────┤
                    └─────────────────────────────────────────────────┘
                                                       │             │
                                              ┌────────┴───┐  ┌──────┴──────┐
                                              │DROK 24V→5V │  │XL4015 24V→6V│
                                              │   (5A)     │  │    (5A)     │
                                              └─────┬──────┘  └──────┬──────┘
                                                    │                │
[ReSpeaker 4-Mic] ──USB──┐                         │         ┌──────┴──────┐
[Logitech C920] ───USB───┤                         │         │ E-STOP      │
[Speaker] ────USB/3.5mm──┼──► [Orange Pi 5 16GB] ◄─┘         │ (NC series) │
                         │        │                           └──────┬──────┘
                         │        │ USB Serial (VCP)                 │
                         │        ▼                           ┌──────▼──────┐
         ┌───────────────┼── [STM32H7 NUCLEO-H753ZI2] ◄──────┤ LM2596 5V   │
         │               │        │    │    │    │            └─────────────┘
         │               │       PWM  I2C  GPIO  GPIO
         │               │        │    │    │    │
         │               │        ▼    ▼    ▼    ▼
         │               │   [6×Servos] [VL53L5CX] [HX711+YZC133] [E-Stop GPIO]
         │               │   DS3225/18   ToF 8×8   Load Cell       NC Contact
```

---

## 3. Camera Strategy

### Current Setup: **Single Camera + ToF Sensor**

| Sensor          | Model          | Mount Point        | FOV / Range         | Purpose                                                                                                    | Always On?              |
| --------------- | -------------- | ------------------ | ------------------- | ---------------------------------------------------------------------------------------------------------- | ----------------------- |
| **Head Camera** | Logitech C920  | Fixed on base/head | 78° diagonal, 1080p | Scene overview: detect all objects on desk via YOLOv8, track user position. Runs at 720p for inference.    | **Yes**                 |
| **ToF Sensor**  | VL53L5CX       | Wrist/gripper      | 8×8 zones, up to 4m | Approach distance during grasping, surface detection, obstacle avoidance. Supplements single camera depth. | **During manipulation** |
| **Load Cell**   | YZC133 + HX711 | Inside gripper     | 0-500g              | Grasp verification: confirms object is held. More reliable than camera-based verification.                 | **During grasping**     |

### Why Single Camera + ToF + Load Cell?

1. **Logitech C920** provides excellent 1080p image quality for YOLO object detection at 78° FOV — wide enough for a desk workspace
2. **VL53L5CX ToF** compensates for lack of depth camera — provides real distance measurements during arm approach (8×8 zone grid = primitive depth map)
3. **YZC133 Load Cell** provides definitive grasp verification — if weight > threshold, object is held (more reliable than vision-based verification)
4. This combo is **simpler and more reliable** than a dual-camera setup for v1

### Future Upgrade Path (v2)

- Add a second USB camera on the wrist for visual servoing during grasping
- Add Intel RealSense D405 for proper depth mapping
- The `arm_vision_node` code is included but optional — ready for v2

---

## 4. Software Stack

| Layer                | Technology                                               | Runs On             |
| -------------------- | -------------------------------------------------------- | ------------------- |
| **OS**               | Ubuntu 24.04 LTS (arm64)                                 | Orange Pi 5         |
| **Middleware**       | ROS2 Jazzy Jalisco                                       | Orange Pi 5         |
| **Motor Control**    | Custom serial protocol (JSON-lines) or micro-ROS         | STM32H7             |
| **Wake Word**        | openWakeWord (Python, custom "Hey Friday" model)         | Orange Pi 5         |
| **Speech-to-Text**   | Whisper.cpp (tiny/base model, RKNN-accelerated)          | Orange Pi 5         |
| **Text-to-Speech**   | Piper TTS (fast, local, voice cloning capable)           | Orange Pi 5         |
| **LLM**              | Ollama running Phi-3-mini-4k or Qwen2-1.5B               | Orange Pi 5         |
| **Object Detection** | YOLOv8-nano (RKNN NPU acceleration via rknn-toolkit2)    | Orange Pi 5         |
| **Motion Planning**  | Custom IK solver (simple 6-DOF) or MoveIt2 Humble bridge | Orange Pi 5         |
| **Arm Interface**    | ros2_control + custom hardware interface                 | Orange Pi 5 ↔ STM32 |

---

## 5. ROS2 Package Structure

```
friday_ws/
├── src/
│   ├── friday_bringup/          # Launch files, configs, URDF
│   │   ├── launch/
│   │   │   ├── friday_full.launch.py
│   │   │   ├── friday_perception.launch.py
│   │   │   ├── friday_cognition.launch.py
│   │   │   └── friday_action.launch.py
│   │   ├── config/
│   │   │   ├── arm_params.yaml
│   │   │   ├── vision_params.yaml
│   │   │   └── llm_params.yaml
│   │   ├── urdf/
│   │   │   └── friday_arm.urdf.xacro
│   │   └── rviz/
│   │       └── friday.rviz
│   │
│   ├── friday_interfaces/       # All custom msgs, srvs, actions
│   │   ├── msg/
│   │   ├── srv/
│   │   └── action/
│   │
│   ├── friday_perception/       # Perception phase nodes
│   │   ├── friday_perception/
│   │   │   ├── audio_input_node.py
│   │   │   ├── wake_word_node.py
│   │   │   ├── stt_node.py
│   │   │   ├── head_vision_node.py
│   │   │   ├── arm_vision_node.py
│   │   │   └── scene_memory_node.py
│   │   └── ...
│   │
│   ├── friday_cognition/        # Cognition phase nodes
│   │   ├── friday_cognition/
│   │   │   ├── intent_classifier_node.py
│   │   │   ├── task_manager_node.py
│   │   │   └── llm_chat_node.py
│   │   └── ...
│   │
│   ├── friday_action/           # Action phase nodes
│   │   ├── friday_action/
│   │   │   ├── motion_planner_node.py
│   │   │   ├── arm_controller_node.py
│   │   │   └── tts_node.py
│   │   └── ...
│   │
│   ├── friday_feedback/         # Feedback phase nodes
│   │   ├── friday_feedback/
│   │   │   ├── execution_monitor_node.py
│   │   │   └── grasp_verify_node.py
│   │   └── ...
│   │
│   └── friday_stm32/           # STM32 firmware (micro-ROS)
│       ├── Core/
│       ├── micro_ros_config/
│       └── README.md
```

---

## 6. ROS2 Nodes (14 Nodes)

### Phase 1: PERCEPTION (6 nodes)

| #   | Node Name           | Package           | Responsibility                                                                                                                                         |
| --- | ------------------- | ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1   | `audio_input_node`  | friday_perception | Captures raw audio from USB mic at 16kHz. Publishes audio chunks. Always running.                                                                      |
| 2   | `wake_word_node`    | friday_perception | Listens to raw audio. Detects "Hey Friday" wake word. Publishes boolean trigger. Triggers the arm's attention pose.                                    |
| 3   | `stt_node`          | friday_perception | Activated after wake word. Records user speech until silence detected. Runs Whisper inference. Publishes transcribed text.                             |
| 4   | `head_vision_node`  | friday_perception | Reads head camera frames. Runs YOLOv8-nano on NPU. Publishes detected objects with bounding boxes. Always running at 5-10 fps.                         |
| 5   | `arm_vision_node`   | friday_perception | Reads arm/wrist camera frames. Runs YOLO on NPU. Publishes close-up detections. Active during manipulation.                                            |
| 6   | `scene_memory_node` | friday_perception | Fuses head + arm camera detections. Maintains a persistent map of objects on the desk with positions (x, y, z estimates). Provides FindObject service. |

### Phase 2: COGNITION (3 nodes)

| #   | Node Name                | Package          | Responsibility                                                                                                                                                             |
| --- | ------------------------ | ---------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 7   | `intent_classifier_node` | friday_cognition | Takes transcribed text. Classifies intent: `CHAT`, `PICK`, `PLACE`, `GIVE`, `FIND`, `MOVE_ARM`, `WAKE_RESPONSE`. Extracts target object name.                              |
| 8   | `task_manager_node`      | friday_cognition | **Central orchestrator.** Receives intents. Routes to LLM (chat) or Motion Planner (manipulation). Manages state machine. Handles retries, clarifications, error recovery. |
| 9   | `llm_chat_node`          | friday_cognition | Wraps Ollama API. Receives chat requests via service. Maintains conversation history. Returns natural language responses.                                                  |

### Phase 3: ACTION (3 nodes)

| #   | Node Name             | Package       | Responsibility                                                                                                                              |
| --- | --------------------- | ------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| 10  | `motion_planner_node` | friday_action | Computes joint trajectories from target poses. Provides action servers for pick, place, hand-over, attention pose, go-home. Uses IK solver. |
| 11  | `arm_controller_node` | friday_action | ros2_control hardware interface. Sends joint commands to STM32 via serial. Reads joint states from encoders. Publishes JointState.          |
| 12  | `tts_node`            | friday_action | Takes text via service. Runs Piper TTS. Plays audio through speaker. Blocks until speech finishes.                                          |

### Phase 4: FEEDBACK (2 nodes)

| #   | Node Name                | Package         | Responsibility                                                                                                  |
| --- | ------------------------ | --------------- | --------------------------------------------------------------------------------------------------------------- |
| 13  | `execution_monitor_node` | friday_feedback | Monitors joint states during motion. Detects stalls, collisions, timeouts. Reports status back to task manager. |
| 14  | `grasp_verify_node`      | friday_feedback | Uses arm camera to verify object is in gripper after grasp attempt. Reports success/failure to task manager.    |

---

## 7. ROS2 Topics

| #   | Topic Name                    | Message Type                                                  | Publisher(s)              | Subscriber(s)                                                  | QoS                       | Rate                 |
| --- | ----------------------------- | ------------------------------------------------------------- | ------------------------- | -------------------------------------------------------------- | ------------------------- | -------------------- |
| 1   | `/friday/audio/raw`           | `audio_msgs/Audio` (or custom `friday_interfaces/AudioChunk`) | audio_input_node          | wake_word_node                                                 | BEST_EFFORT               | 100Hz (10ms chunks)  |
| 2   | `/friday/wake_word/detected`  | `std_msgs/Bool`                                               | wake_word_node            | stt_node, task_manager_node                                    | RELIABLE                  | Event-based          |
| 3   | `/friday/speech/text`         | `std_msgs/String`                                             | stt_node                  | intent_classifier_node                                         | RELIABLE                  | Event-based          |
| 4   | `/friday/intent`              | `friday_interfaces/Intent`                                    | intent_classifier_node    | task_manager_node                                              | RELIABLE                  | Event-based          |
| 5   | `/friday/head_cam/image_raw`  | `sensor_msgs/Image`                                           | head_vision_node (driver) | scene_memory_node                                              | BEST_EFFORT               | 10 fps               |
| 6   | `/friday/head_cam/detections` | `friday_interfaces/DetectionArray`                            | head_vision_node          | scene_memory_node                                              | RELIABLE                  | 5-10 fps             |
| 7   | `/friday/arm_cam/image_raw`   | `sensor_msgs/Image`                                           | arm_vision_node (driver)  | grasp_verify_node                                              | BEST_EFFORT               | 30 fps               |
| 8   | `/friday/arm_cam/detections`  | `friday_interfaces/DetectionArray`                            | arm_vision_node           | scene_memory_node                                              | RELIABLE                  | 15 fps               |
| 9   | `/friday/scene/objects`       | `friday_interfaces/ObjectArray`                               | scene_memory_node         | task_manager_node                                              | RELIABLE, TRANSIENT_LOCAL | 1 Hz (snapshot)      |
| 10  | `/friday/arm/joint_states`    | `sensor_msgs/JointState`                                      | arm_controller_node       | motion_planner_node, execution_monitor_node                    | RELIABLE                  | 50 Hz                |
| 11  | `/friday/arm/joint_commands`  | `trajectory_msgs/JointTrajectory`                             | motion_planner_node       | arm_controller_node                                            | RELIABLE                  | On-demand            |
| 12  | `/friday/status/system`       | `friday_interfaces/SystemStatus`                              | task_manager_node         | (logging / debug)                                              | RELIABLE                  | 1 Hz                 |
| 13  | `/friday/gripper/load`        | `friday_interfaces/LoadCellData`                              | arm_controller_node       | grasp_verify_node, task_manager_node                           | RELIABLE                  | 20 Hz (during grasp) |
| 14  | `/friday/tof/ranges`          | `friday_interfaces/ToFData`                                   | arm_controller_node       | motion_planner_node, scene_memory_node                         | RELIABLE                  | 10 Hz                |
| 15  | `/friday/safety/estop`        | `std_msgs/Bool`                                               | arm_controller_node       | task_manager_node, motion_planner_node, execution_monitor_node | RELIABLE, TRANSIENT_LOCAL | Event-based          |

---

## 8. ROS2 Services

| #   | Service Name                | Service Type                       | Server Node            | Client(s)                              | Purpose                                                                   |
| --- | --------------------------- | ---------------------------------- | ---------------------- | -------------------------------------- | ------------------------------------------------------------------------- |
| 1   | `/friday/llm/chat`          | `friday_interfaces/Chat`           | llm_chat_node          | task_manager_node                      | Send user text, receive LLM response                                      |
| 2   | `/friday/scene/find_object` | `friday_interfaces/FindObject`     | scene_memory_node      | task_manager_node                      | Query: "Is there a notebook on the desk?" → returns position or not_found |
| 3   | `/friday/tts/speak`         | `friday_interfaces/Speak`          | tts_node               | task_manager_node                      | Send text to speak aloud                                                  |
| 4   | `/friday/arm/get_pose`      | `friday_interfaces/GetPose`        | arm_controller_node    | motion_planner_node, task_manager_node | Get current end-effector pose                                             |
| 5   | `/friday/intent/classify`   | `friday_interfaces/ClassifyIntent` | intent_classifier_node | task_manager_node (fallback)           | Directly classify a string (backup path)                                  |
| 6   | `/friday/wake/set_name`     | `friday_interfaces/SetWakeName`    | wake_word_node         | (config tool)                          | Change wake word at runtime                                               |

---

## 9. ROS2 Actions

| #   | Action Name                  | Action Type                       | Server Node         | Client(s)          | Purpose                                                  | Feedback                                                   |
| --- | ---------------------------- | --------------------------------- | ------------------- | ------------------ | -------------------------------------------------------- | ---------------------------------------------------------- |
| 1   | `/friday/arm/pick_object`    | `friday_interfaces/PickObject`    | motion_planner_node | task_manager_node  | Pick an object from desk given name + position           | Progress %, current_phase (approaching, grasping, lifting) |
| 2   | `/friday/arm/place_object`   | `friday_interfaces/PlaceObject`   | motion_planner_node | task_manager_node  | Place held object at target location                     | Progress %, current_phase                                  |
| 3   | `/friday/arm/hand_over`      | `friday_interfaces/HandOver`      | motion_planner_node | task_manager_node  | Move object toward user's hand and release               | Progress %, distance_to_target                             |
| 4   | `/friday/arm/move_to_pose`   | `friday_interfaces/MoveToPose`    | motion_planner_node | task_manager_node  | Move arm to arbitrary pose                               | Progress %, joint_error                                    |
| 5   | `/friday/arm/go_home`        | `friday_interfaces/GoHome`        | motion_planner_node | task_manager_node  | Return arm to home/rest position                         | Progress %                                                 |
| 6   | `/friday/arm/attention_pose` | `friday_interfaces/AttentionPose` | motion_planner_node | task_manager_node  | Orient arm toward user (pet-like attention)              | Progress %                                                 |
| 7   | `/friday/task/execute`       | `friday_interfaces/ExecuteTask`   | task_manager_node   | (top-level / test) | Execute a full macro task (e.g., "give me the notebook") | stage, progress_pct, message                               |

---

## 10. Custom Interface Definitions

### 10.1 Messages (`friday_interfaces/msg/`)

```python
# --- Intent.msg ---
string intent_type          # CHAT | PICK | PLACE | GIVE | FIND | MOVE_ARM | WAKE_RESPONSE
string target_object        # e.g., "notebook", "pen", "" if chat-only
string raw_text             # original user utterance
float32 confidence          # 0.0 to 1.0
```

```python
# --- Detection.msg ---
string class_name           # e.g., "notebook", "cup", "pen"
float32 confidence          # detection confidence
int32 x_min                 # bounding box pixel coords
int32 y_min
int32 x_max
int32 y_max
float32 center_x            # estimated 3D position (meters, in base frame)
float32 center_y
float32 center_z
string camera_source        # "head" | "arm"
```

```python
# --- DetectionArray.msg ---
std_msgs/Header header
Detection[] detections
```

```python
# --- SceneObject.msg ---
string object_name           # class label
float64 x                    # position in base frame (meters)
float64 y
float64 z
float32 confidence
builtin_interfaces/Time last_seen
bool is_reachable            # within arm workspace?
```

```python
# --- ObjectArray.msg ---
std_msgs/Header header
SceneObject[] objects
```

```python
# --- SystemStatus.msg ---
string state                 # IDLE | LISTENING | PROCESSING | MANIPULATING | SPEAKING | ERROR
string active_task           # description of current task
bool arm_busy
bool llm_busy
float32 cpu_temp
float32 cpu_usage_pct
```

```python
# --- AudioChunk.msg ---
std_msgs/Header header
int32 sample_rate            # 16000
int32 channels               # 1
uint8[] data                 # raw PCM bytes
```

### 10.2 Services (`friday_interfaces/srv/`)

```python
# --- Chat.srv ---
# Request
string user_message
string context               # optional context about current scene
---
# Response
string response_text
bool success
```

```python
# --- FindObject.srv ---
# Request
string object_name
---
# Response
bool found
float64 x
float64 y
float64 z
float32 confidence
string suggestion            # "Try looking near the keyboard" or ""
```

```python
# --- Speak.srv ---
# Request
string text
string emotion               # "neutral" | "happy" | "concerned" | "excited"
---
# Response
bool success
float32 duration_sec
```

```python
# --- GetPose.srv ---
# Request  (empty)
---
# Response
geometry_msgs/Pose end_effector_pose
float64[] joint_positions     # array of 6 joint angles
bool gripper_open
```

```python
# --- ClassifyIntent.srv ---
# Request
string text
---
# Response
friday_interfaces/Intent intent
```

```python
# --- SetWakeName.srv ---
# Request
string wake_word              # new wake word
---
# Response
bool success
string message
```

### 10.3 Actions (`friday_interfaces/action/`)

```python
# --- PickObject.action ---
# Goal
string object_name
float64 target_x
float64 target_y
float64 target_z
---
# Result
bool success
string message                # "Picked up notebook" or "Failed: object slipped"
---
# Feedback
string current_phase          # APPROACHING | ALIGNING | GRASPING | LIFTING | DONE
float32 progress_pct          # 0.0 to 100.0
```

```python
# --- PlaceObject.action ---
# Goal
float64 target_x
float64 target_y
float64 target_z
---
# Result
bool success
string message
---
# Feedback
string current_phase          # MOVING | LOWERING | RELEASING | DONE
float32 progress_pct
```

```python
# --- HandOver.action ---
# Goal
string object_name
---
# Result
bool success
string message
---
# Feedback
string current_phase          # LIFTING | EXTENDING | WAITING_FOR_USER | RELEASING | DONE
float32 progress_pct
float32 distance_to_user      # estimated meters
```

```python
# --- MoveToPose.action ---
# Goal
geometry_msgs/Pose target_pose
float32 speed_factor          # 0.1 (slow) to 1.0 (max speed)
---
# Result
bool success
geometry_msgs/Pose final_pose
---
# Feedback
float32 progress_pct
float32 position_error        # meters from target
```

```python
# --- GoHome.action ---
# Goal (empty)
---
# Result
bool success
---
# Feedback
float32 progress_pct
```

```python
# --- AttentionPose.action ---
# Goal
float64 user_direction_yaw    # radians, relative to base frame: where is the user?
---
# Result
bool success
---
# Feedback
float32 progress_pct
```

```python
# --- ExecuteTask.action ---
# Goal
string task_description       # natural language: "give me the notebook"
friday_interfaces/Intent intent
---
# Result
bool success
string final_message          # "Here you go, boss!" or "I couldn't find it"
---
# Feedback
string stage                  # UNDERSTANDING | LOCATING | PLANNING | EXECUTING | VERIFYING | SPEAKING
float32 progress_pct
string message                # human-readable status
```

---

## 11. Behavioral State Machine

```
                          ┌──────────────────────────┐
                          │          IDLE             │
                          │  (cameras always running, │
                          │   scene memory updating)  │
                          └────────────┬─────────────┘
                                       │ Wake word "Hey Friday" detected
                                       ▼
                          ┌──────────────────────────┐
                          │       LISTENING           │
                          │  Arm → attention pose     │
                          │  TTS: "Hello boss, what   │
                          │   can I do for you?"      │
                          │  STT: recording user...   │
                          └────────────┬─────────────┘
                                       │ Speech transcribed
                                       ▼
                          ┌──────────────────────────┐
                          │      PROCESSING           │
                          │  Intent classification    │
                          └───┬──────────┬────────┬──┘
                              │          │        │
                   Intent=CHAT│  Intent= │   Intent=
                              │  PICK/   │   UNCLEAR
                              │  GIVE    │
                              ▼          ▼        ▼
                    ┌──────────┐ ┌────────────┐ ┌──────────┐
                    │  CHAT    │ │ MANIPULATE │ │ CLARIFY  │
                    │ LLM call │ │ Find obj   │ │ Ask user │
                    │ TTS resp │ │ Plan path  │ │ "where?" │
                    └────┬─────┘ │ Execute    │ └────┬─────┘
                         │       │ Verify     │      │
                         │       │ Hand over  │      │
                         │       └──────┬─────┘      │
                         │              │            │
                         ▼              ▼            ▼
                    ┌──────────────────────────────────────┐
                    │           SPEAKING                    │
                    │  TTS: response / "Here you go" /     │
                    │        "I can't see it, where is it?"│
                    └──────────────────┬───────────────────┘
                                       │
                                       ▼
                                    [IDLE]
```

### Key Behaviors

1. **Pet-Like Wake Response**: When "Hey Friday" is detected, the arm physically turns toward the user (attention pose) and verbally greets — mimicking a pet responding to its name.

2. **Conversation vs. Manipulation Split**: The Task Manager node is the decision point:
   - `CHAT` intent → LLM only, no arm movement
   - `PICK/GIVE/PLACE` intent → arm pipeline, with speech feedback

3. **Object Not Found Handling**: If the scene memory doesn't contain the requested object:
   - Friday says: _"I can't see it on the desk. Can you tell me where it is?"_
   - Re-enters LISTENING state for user clarification
   - User might say: _"It's behind the monitor"_
   - Friday tries again with updated search area

4. **Grasp Retry**: Up to 2 retries using arm camera for re-alignment before giving up.

---

## 12. Data Flow Examples

### Example 1: "Hey Friday, tell me the benefits of LTPO display"

```
1. audio_input_node   → publishes /friday/audio/raw
2. wake_word_node     → detects "Hey Friday" → publishes /friday/wake_word/detected = true
3. task_manager_node  → receives wake → calls action /friday/arm/attention_pose
                      → calls service /friday/tts/speak("Hello boss, what can I do for you?")
4. stt_node           → activated → records → Whisper → "tell me the benefits of LTPO display"
                      → publishes /friday/speech/text
5. intent_classifier  → intent_type=CHAT, target_object="" → publishes /friday/intent
6. task_manager_node  → routes to CHAT path
                      → calls service /friday/llm/chat("tell me the benefits of LTPO display")
7. llm_chat_node      → returns LLM response about LTPO
8. task_manager_node  → calls service /friday/tts/speak(response)
9. tts_node           → speaks response → done
10. task_manager_node → returns to IDLE state
    *** NO ARM MOVEMENT beyond initial attention pose ***
```

### Example 2: "Hey Friday, give me the notebook"

```
1. audio_input_node   → publishes /friday/audio/raw
2. wake_word_node     → detects "Hey Friday" → publishes wake = true
3. task_manager_node  → attention pose + greeting
4. stt_node           → "give me the notebook" → publishes /friday/speech/text
5. intent_classifier  → intent_type=GIVE, target_object="notebook" → publishes /friday/intent
6. task_manager_node  → routes to MANIPULATION path
                      → calls service /friday/scene/find_object("notebook")
7. scene_memory_node  → found=true, x=0.3, y=0.2, z=0.05
8. task_manager_node  → calls service /friday/tts/speak("Okay boss, let me get that for you")
9. task_manager_node  → calls action /friday/arm/pick_object(name="notebook", x, y, z)
10. motion_planner    → computes trajectory → sends to arm_controller
11. arm_controller    → executes → feedback: APPROACHING → ALIGNING → GRASPING → LIFTING
12. grasp_verify_node → checks arm camera → gripper has object → success
13. task_manager_node → calls action /friday/arm/hand_over(object_name="notebook")
14. motion_planner    → extends arm toward user → WAITING_FOR_USER
15. (User takes notebook, gripper load drops)
16. task_manager_node → calls service /friday/tts/speak("Here you go, boss!")
17. task_manager_node → calls action /friday/arm/go_home
18. task_manager_node → returns to IDLE state
```

### Example 3: "Hey Friday, give me the stapler" (not found)

```
1-5. Same as above... intent_type=GIVE, target_object="stapler"
6. task_manager_node  → calls service /friday/scene/find_object("stapler")
7. scene_memory_node  → found=false
8. task_manager_node  → calls service /friday/tts/speak(
       "I can't see a stapler on the desk. Can you tell me where it is?")
9. task_manager_node  → re-enters LISTENING state
10. stt_node          → "it's behind the monitor"
11. intent_classifier → intent_type=FIND, target_object="stapler", context="behind monitor"
12. task_manager_node → adjusts search area → tries head camera scan toward monitor area
13. (If found) → continues with pick + handover
    (If still not found) → "Sorry boss, I still can't find it. Can you point to it?"
```

---

## 13. Phase-Based Development Plan

### Phase 1: PERCEPTION (Weeks 1-3)

- [ ] Set up Orange Pi 5 with Ubuntu 24.04 + ROS2 Jazzy
- [ ] audio_input_node: USB mic capture
- [ ] wake_word_node: openWakeWord with custom "Hey Friday" model
- [ ] stt_node: Whisper.cpp integration
- [ ] head_vision_node: USB camera + YOLOv8-nano on NPU
- [ ] scene_memory_node: basic object list (no arm camera yet)

### Phase 2: COGNITION (Weeks 4-5)

- [ ] intent_classifier_node: rule-based first, then LLM-enhanced
- [ ] llm_chat_node: Ollama integration with Phi-3-mini
- [ ] task_manager_node: state machine (CHAT path only first)
- [ ] tts_node: Piper TTS integration

### Phase 3: ACTION (Weeks 6-9)

- [ ] STM32 firmware: micro-ROS agent + PWM servo control
- [ ] arm_controller_node: ros2_control hardware interface
- [ ] motion_planner_node: IK solver + basic trajectories
- [ ] Implement: attention_pose, go_home, pick_object, hand_over actions
- [ ] URDF model of the arm

### Phase 4: FEEDBACK & INTEGRATION (Weeks 10-12)

- [ ] arm_vision_node: wrist camera integration
- [ ] grasp_verify_node: visual grasp confirmation
- [ ] execution_monitor_node: collision/stall detection
- [ ] Full end-to-end testing: wake → understand → pick → handover
- [ ] Clarification dialogue loop ("where is it?")

### Phase 5: POLISH (Weeks 13+)

- [ ] Pet-like personality tuning (LLM prompt engineering)
- [ ] Voice personality (Piper TTS voice training)
- [ ] Multi-object tasks ("give me the pen and notebook")
- [ ] User face tracking for attention pose
- [ ] Power management & auto-sleep

---

## Appendix A: Bill of Materials (Actual)

| #   | Component                   | Model                            | Qty   | Purpose                           |
| --- | --------------------------- | -------------------------------- | ----- | --------------------------------- |
| 1   | SBC (Main Brain)            | Orange Pi 5 Ultra / OPi5 16GB    | 1     | ROS2 Jazzy, all AI inference      |
| 2   | MCU (Motor Control)         | STM32H7 NUCLEO-H753ZI2           | 1     | Servo PWM, sensor I/O, E-stop     |
| 3   | Camera                      | Logitech C920 (1080p)            | 1     | Object detection, scene mapping   |
| 4   | Microphone                  | ReSpeaker 4-Mic Array            | 1     | Wake word, speech capture         |
| 5   | Speaker                     | USB / 3.5mm Speaker              | 1     | TTS audio output                  |
| 6   | Servo (Base/Shoulder/Elbow) | DS3225 (25kg-cm, 270°)           | 3     | High-torque joints                |
| 7   | Servo (Wrist/Gripper)       | DS3218 (20kg-cm, 270°)           | 3     | Medium-torque joints              |
| 8   | Load Cell                   | YZC133 Mini + HX711 ADC          | 1     | Gripper grasp verification        |
| 9   | ToF Sensor                  | ST VL53L5CX (8×8 multi-zone)     | 1     | Approach distance, surface detect |
| 10  | Main PSU                    | Mean Well LRS-350-24 (24V/14.6A) | 1     | Master power supply               |
| 11  | BEC (Orange Pi)             | DROK 24V→5V 5A                   | 1     | Orange Pi power                   |
| 12  | BEC (Sensors/Logic)         | LM2596 24V→5V 2-3A               | 1     | STM32, sensors                    |
| 13  | BEC (Servos)                | XL4015 24V→6V 5A                 | 1     | All 6 servos (set to 6V!)         |
| 14  | E-Stop                      | Schneider XB2BS542               | 1     | Emergency stop (NC contact)       |
| 15  | Frame/Structure             | 3D printed / aluminum brackets   | 1 set | Arm structure, base mount         |
| 16  | USB Hub (optional)          | Powered USB 3.0 hub              | 1     | If OPi5 USB ports insufficient    |
| 17  | Wiring/Connectors           | JST, XT60, Dupont, USB cables    | misc  | Wiring harness                    |

---

## Appendix B: Topic QoS Profiles Summary

| Profile           | Used For                  | Reliability | Durability      | History       |
| ----------------- | ------------------------- | ----------- | --------------- | ------------- |
| **Sensor Stream** | audio/raw, image_raw      | BEST_EFFORT | VOLATILE        | KEEP_LAST(1)  |
| **Detection**     | detections, scene/objects | RELIABLE    | TRANSIENT_LOCAL | KEEP_LAST(5)  |
| **Command**       | joint_commands, intent    | RELIABLE    | VOLATILE        | KEEP_LAST(10) |
| **Status**        | system_status, wake_word  | RELIABLE    | VOLATILE        | KEEP_LAST(1)  |

---

_This document serves as the living architecture reference for the FRIDAY project. Update it as design decisions evolve._
