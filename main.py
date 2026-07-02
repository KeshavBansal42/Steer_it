import argparse
# pyrefly: ignore [missing-import]
import cv2
import time
import sys

import config
from hand_tracker import HandTracker
from gesture_processor import GestureProcessor
from controller import create_controller
from calibration import run_calibration, load_calibration
from overlay import DebugOverlay

def main():
    parser = argparse.ArgumentParser(description="Steer_it: Hand Gesture Racing Controller")
    parser.add_argument("--mode", choices=["console", "gamepad", "auto"], default="auto", 
                        help="Output mode. Console for dev, gamepad for playing games.")
    parser.add_argument("--skip-calibration", action="store_true", help="Skip startup calibration and load last saved.")
    parser.add_argument("--no-overlay", action="store_true", help="Disable the OpenCV video preview window.")
    args = parser.parse_args()

    mode = config.DEFAULT_MODE if args.mode == "auto" else args.mode

    # Initialize components
    print(f"Initializing Steer_it (Mode: {mode})...")
    camera = cv2.VideoCapture(config.CAMERA_INDEX)
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAMERA_WIDTH)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAMERA_HEIGHT)
    camera.set(cv2.CAP_PROP_FPS, config.CAMERA_FPS)

    tracker = HandTracker()
    processor = GestureProcessor()
    controller = create_controller(mode)
    overlay = DebugOverlay(config.CAMERA_WIDTH, config.CAMERA_HEIGHT)

    # Calibration
    if args.skip_calibration:
        s_neut, d_neut = load_calibration()
    else:
        s_neut, d_neut = run_calibration(camera, tracker, overlay)
    
    processor.set_calibration(s_neut, d_neut)

    # FPS calculation
    prev_time = time.time()
    fps = 0
    frame_count = 0

    print("\nStarting main loop. Press 'Q' in the video window or Ctrl+C in terminal to quit.")
    
    try:
        while True:
            ret, frame = camera.read()
            if not ret:
                print("Failed to grab frame from camera. Exiting.")
                break
                
            # Flip horizontally for intuitive left/right interaction
            frame = cv2.flip(frame, 1)

            # 1. Track Hands
            hands = tracker.process(frame)

            # 2. Process Gestures to get control values
            steering, throttle, brake, hand_mode = processor.compute(hands)

            # 3. Send inputs to virtual controller
            controller.set_steering(steering)
            controller.set_throttle(throttle)
            controller.set_brake(brake)
            
            # FPS tracking
            curr_time = time.time()
            frame_count += 1
            if curr_time - prev_time >= 1.0:
                fps = frame_count
                frame_count = 0
                prev_time = curr_time

            controller.update(hand_mode, fps)

            # 4. Debug Overlay
            if not args.no_overlay:
                tracker.draw_landmarks(frame, hands)
                overlay.draw(frame, hands, steering, throttle, brake, hand_mode, fps)
                cv2.imshow("Steer_it Preview", frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

    except KeyboardInterrupt:
        print("\nExiting via KeyboardInterrupt.")
    finally:
        print("Cleaning up...")
        camera.release()
        cv2.destroyAllWindows()
        # Reset controller state
        controller.set_steering(0.0)
        controller.set_throttle(0.0)
        controller.set_brake(0.0)
        controller.update(0, 0)
        print("Done.")

if __name__ == "__main__":
    main()
