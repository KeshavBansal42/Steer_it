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
    right_pinch_samples = []
    left_pinch_samples = []
    
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
                # Steer raw
                import math
                angle_rad = math.atan2(rw.y - lw.y, rw.x - lw.x)
                steer_samples.append(math.degrees(angle_rad))
                
                # Pinch raw (Index Tip = 8, Thumb Tip = 4)
                r_pinch = math.sqrt((right_hand.image_landmarks[8].x - right_hand.image_landmarks[4].x)**2 + 
                                    (right_hand.image_landmarks[8].y - right_hand.image_landmarks[4].y)**2)
                l_pinch = math.sqrt((left_hand.image_landmarks[8].x - left_hand.image_landmarks[4].x)**2 + 
                                    (left_hand.image_landmarks[8].y - left_hand.image_landmarks[4].y)**2)
                
                right_pinch_samples.append(r_pinch)
                left_pinch_samples.append(l_pinch)
                
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
    
    if steer_samples and right_pinch_samples and left_pinch_samples:
        avg_steer = sum(steer_samples) / len(steer_samples)
        avg_r_pinch = sum(right_pinch_samples) / len(right_pinch_samples)
        avg_l_pinch = sum(left_pinch_samples) / len(left_pinch_samples)
        
        print(f"Calibration successful! Neutral Steering: {avg_steer:.2f}°, R-Pinch: {avg_r_pinch:.3f}, L-Pinch: {avg_l_pinch:.3f}")
        
        # Save
        with open(CALIBRATION_FILE, 'w') as f:
            json.dump({
                "steering_neutral": avg_steer, 
                "right_pinch_neutral": avg_r_pinch,
                "left_pinch_neutral": avg_l_pinch
            }, f)
            
        return avg_steer, avg_r_pinch, avg_l_pinch
    else:
        print("Failed to collect calibration data. Using defaults.")
        return 0.0, 0.2, 0.2

def load_calibration() -> Tuple[float, float, float]:
    if os.path.exists(CALIBRATION_FILE):
        try:
            with open(CALIBRATION_FILE, 'r') as f:
                data = json.load(f)
                s = data.get("steering_neutral", 0.0)
                rp = data.get("right_pinch_neutral", 0.2)
                lp = data.get("left_pinch_neutral", 0.2)
                print(f"Loaded calibration: Steering {s:.2f}°, R-Pinch {rp:.3f}, L-Pinch {lp:.3f}")
                return s, rp, lp
        except Exception as e:
            print(f"Failed to load {CALIBRATION_FILE}: {e}")
    return 0.0, 0.2, 0.2
