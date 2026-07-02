# pyrefly: ignore [missing-import]
import cv2
import json
import os
import time
from typing import Tuple

CALIBRATION_FILE = "calibration.json"

def run_calibration(camera, tracker, overlay) -> Tuple[float, float]:
    print("\n--- Starting Calibration ---")
    print("Hold your hands level (like gripping a steering wheel straight) and wait...")
    
    calibrating = True
    start_time = time.time()
    wait_time = 3.0 # seconds before starting collection
    collection_time = 2.0 # seconds to collect data
    
    steer_samples = []
    depth_samples = []
    
    while calibrating:
        ret, frame = camera.read()
        if not ret: break
        frame = cv2.flip(frame, 1)
        
        hands = tracker.process(frame)
        tracker.draw_landmarks(frame, hands)
        
        elapsed = time.time() - start_time
        
        # We need two hands to calibrate steering properly
        if len(hands) == 2:
            h1, h2 = hands[0], hands[1]
            if h1.image_landmarks[0].x < h2.image_landmarks[0].x:
                left_hand, right_hand = h1, h2
            else:
                left_hand, right_hand = h2, h1
                
            # Draw line between wrists
            lw = left_hand.image_landmarks[0]
            rw = right_hand.image_landmarks[0]
            h, w, _ = frame.shape
            cv2.line(frame, (int(lw.x * w), int(lw.y * h)), (int(rw.x * w), int(rw.y * h)), (0, 255, 255), 2)
            
            if elapsed < wait_time:
                msg = f"Hold level... starting in {wait_time - elapsed:.1f}s"
                color = (0, 165, 255)
            elif elapsed < wait_time + collection_time:
                msg = "Calibrating... hold still!"
                color = (0, 255, 0)
                
                # Collect samples
                # Steering raw
                import math
                angle_rad = math.atan2(rw.y - lw.y, rw.x - lw.x)
                steer_samples.append(math.degrees(angle_rad))
                
                # Depth raw (2D pixel distance between wrists)
                d_img = math.sqrt((rw.x - lw.x)**2 + (rw.y - lw.y)**2)
                depth_samples.append(d_img)
                
            else:
                calibrating = False
                msg = "Done!"
                color = (0, 255, 0)
        else:
            msg = "Show BOTH hands to calibrate"
            color = (0, 0, 255)
            # Reset timer if they drop hands
            if elapsed > wait_time:
                start_time = time.time() - wait_time + 0.5
                
        # Draw status
        cv2.putText(frame, msg, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
        cv2.imshow("Steer_it Setup", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("Calibration cancelled.")
            return 0.0, 0.0
            
    cv2.destroyWindow("Steer_it Setup")
    
    if steer_samples and depth_samples:
        avg_steer = sum(steer_samples) / len(steer_samples)
        avg_depth = sum(depth_samples) / len(depth_samples)
        
        print(f"Calibration successful! Neutral Steering: {avg_steer:.2f}°, Neutral Depth: {avg_depth:.3f}")
        
        # Save
        with open(CALIBRATION_FILE, 'w') as f:
            json.dump({"steering_neutral": avg_steer, "depth_neutral": avg_depth}, f)
            
        return avg_steer, avg_depth
    else:
        print("Failed to collect calibration data. Using defaults (0,0).")
        return 0.0, 0.0

def load_calibration() -> Tuple[float, float]:
    if os.path.exists(CALIBRATION_FILE):
        try:
            with open(CALIBRATION_FILE, 'r') as f:
                data = json.load(f)
                s = data.get("steering_neutral", 0.0)
                d = data.get("depth_neutral", 0.0)
                print(f"Loaded calibration: Steering {s:.2f}°, Depth {d:.3f}")
                return s, d
        except Exception as e:
            print(f"Failed to load {CALIBRATION_FILE}: {e}")
    return 0.0, 0.0
