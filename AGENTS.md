# Repository Guidelines

## Project Overview

Single-file Python application controlling a UGOT robotic arm via hand gestures. Uses OpenCV for camera capture, MediaPipe for hand landmark detection, and the UGOT SDK for servo/clamp control. Target runtime: Linux with webcam and network access to a UGOT robot at `192.168.1.2`.

## Architecture & Data Flow

```
Camera (OpenCV) → MediaPipe → Main Loop → robot_worker Thread → UGOT Robot
                                    │
                                    ├─ Right hand → Servo 51 (Pan), Servo 52 (Tilt), Clamp
                                    └─ Left hand  → Servo 53 (Extra)
```

**Key design pattern**: Single-threaded robot communication. The `robot_worker` thread is the **only** thread allowed to call `got.*()` methods. The main loop only updates shared state under a `threading.Lock`. This prevents socket corruption from concurrent SDK calls.

**Data flow**:
1. Frame captured via `cv2.VideoCapture(0)`
2. MediaPipe detects up to 2 hands, returns landmarks + handedness
3. For each hand, compute pinch ratio (thumb-to-index distance / hand size) and midpoint
4. Right hand: smooth position → servo 51/52 angle updates; pinch ratio → clamp state
5. Left hand: vertical position → servo 53 angle updates
6. All robot commands are queued via `target_servo` / `target_clamp` dicts
7. `robot_worker` polls these dicts every 80ms, sends only changed commands

## Key Directories

Only one source file exists: `ugot-hand.py` (607 lines). No subdirectories, no test suite, no build system.

## Development Commands

**Run:**
```bash
python ugot-hand.py
```

**Dependencies** (declared in-code comment):
```bash
pip install ugot opencv-python mediapipe protobuf==3.20.3
```

**No build step, no test command, no linter configured.**

## Code Conventions & Common Patterns

### Naming
- **Constants**: `UPPER_CASE` for config values (e.g., `SERVO_PAN_ID`, `PINCH_CLOSE_RATIO`)
- **Variables**: `lower_case` for mutable state (e.g., `servo51`, `smooth_x`)
- **Servo IDs**: Defined once at top (`SERVO_PAN_ID`, `SERVO_TILT_ID`, `SERVO_EXTRA_ID`); all other code references these constants, never magic numbers
- **Hand labels**: MediaPipe returns `"Right"` / `"Left"` strings

### Threading Model
- **Single worker thread** (`robot_worker`) owns all `got.*()` calls
- **Shared state** (`target_servo`, `target_clamp`) protected by `robot_lock`
- **Throttle**: `SERVO_SEND_INTERVAL = 0.08` prevents flooding the robot
- **Daemon thread** so program can exit without joining

### Smoothing (Exponential Moving Average)
```python
smooth_x = int(alpha * new_x + (1 - alpha) * smooth_x)
```
- Position smoothing: `alpha = 0.7`
- Pinch ratio smoothing: `pinch_alpha = 0.5`

### Hysteresis + Debounce (for clamp)
- **Hysteresis**: `PINCH_CLOSE_RATIO = 0.35`, `PINCH_OPEN_RATIO = 0.55` — gap prevents flip-flop
- **Debounce**: `PINCH_CONFIRM_FRAMES = 4` — state change requires 4 consecutive frames
- Counters reset when hand disappears or ratio enters dead zone

### Error Handling
- Broad `except Exception` around robot commands, prints warning, continues
- No crash recovery; daemon thread means program exits on main loop break
- `hand_size < 1` guard prevents division by zero

### Servo Angle Clamping
```python
servo51 = max(SERVO51_MIN, min(SERVO51_MAX, servo51))
```
Always clamp before sending. Servo 53 uses a "rubber band" model: `-44 + (error * 0.25)`.

## Important Files

| File | Purpose |
|------|---------|
| `ugot-hand.py` | Single entry point — all logic in one file |
| `README.md` | Project documentation |

## Runtime/Tooling Preferences

- **Python 3** (version unspecified, uses f-strings)
- **Package manager**: pip
- **External dependencies**: `ugot` SDK, `opencv-python`, `mediapipe`, `protobuf==3.20.3`
- **Hardware**: Webcam (default `/dev/video0`), UGOT robot on `192.168.1.2`
- **No virtual environment management** (no `.venv` or `requirements.txt`)

## Testing & QA

**No tests exist.** The project is a real-time robotics application where unit testing is impractical without hardware mocking. Manual verification is the only current approach. The `README.md` documents expected behavior for users.