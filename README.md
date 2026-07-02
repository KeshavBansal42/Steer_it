# Steer_it 🏎️

Gesture-Controlled Racing Game Controller. Use your webcam to control any racing game with analog precision!

## How it Works
It uses **MediaPipe** to track your hands and computes steering (wrist roll) and throttle/brake (hand pitch) in real-time. The values are smoothed using an adaptive **One Euro Filter** and fed into a virtual Xbox 360 controller.

## Requirements
- Python 3.10+
- Webcam
- Windows (for game support via `vgamepad`) or Linux (for testing)

## Setup
1. Create a virtual environment: `python3 -m venv venv`
2. Activate it: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
3. Install dependencies: `pip install -r requirements.txt`

## Running
```bash
python3 main.py
```
- Hold your hands out like gripping a steering wheel to calibrate.
- **Steering:** Turn the imaginary wheel.
- **Gas:** Tilt both hands forward.
- **Brake:** Tilt both hands backward.

### Options
- `--mode console`: Force console output (useful on Linux)
- `--mode gamepad`: Force Xbox controller output
- `--skip-calibration`: Load the last calibration instead of calibrating on startup
- `--no-overlay`: Hide the OpenCV camera preview
