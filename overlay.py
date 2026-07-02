# pyrefly: ignore [missing-import]
import cv2
import numpy as np

class DebugOverlay:
    def __init__(self, width: int = 640, height: int = 480):
        self.width = width
        self.height = height

    def draw(self, frame, hands, steering, throttle, brake, mode, fps):
        # Dimensions
        h, w, _ = frame.shape
        
        # 1. Status Text
        if mode == 0:
            status = "NO HANDS DETECTED"
            color = (0, 0, 255)
        elif mode == 1:
            status = "ONE HAND (FALLBACK)"
            color = (0, 165, 255)
        else:
            status = "TWO HANDS TRACKING"
            color = (0, 255, 0)
            
            # Draw line connecting wrists for 2 hands
            if len(hands) >= 2:
                # Find left/right correctly
                h1, h2 = hands[0], hands[1]
                if h1.image_landmarks[0].x < h2.image_landmarks[0].x:
                    left_hand, right_hand = h1, h2
                else:
                    left_hand, right_hand = h2, h1
                
                lw = left_hand.image_landmarks[0]
                rw = right_hand.image_landmarks[0]
                cv2.line(frame, (int(lw.x * w), int(lw.y * h)), (int(rw.x * w), int(rw.y * h)), (0, 255, 255), 2)
            
        cv2.putText(frame, status, (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        cv2.putText(frame, f"FPS: {fps}", (w - 120, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # 2. Steering Gauge (Bottom center)
        center_x = w // 2
        center_y = h - 50
        radius = 100
        
        # Background arc
        cv2.ellipse(frame, (center_x, center_y), (radius, radius), 180, 0, 180, (50, 50, 50), -1)
        cv2.ellipse(frame, (center_x, center_y), (radius, radius), 180, 0, 180, (150, 150, 150), 2)
        
        # Steering indicator
        # Steering is [-1, 1], map to angle [-90, 90] + offset 270 (upwards)
        angle = steering * 90 
        end_x = int(center_x + radius * 0.9 * np.sin(np.radians(angle)))
        end_y = int(center_y - radius * 0.9 * np.cos(np.radians(angle)))
        
        # Color: green in center, red at edges
        ind_color = (0, int(255 * (1 - abs(steering))), int(255 * abs(steering)))
        cv2.line(frame, (center_x, center_y), (end_x, end_y), ind_color, 4)
        cv2.putText(frame, f"Steer: {steering:.2f}", (center_x - 50, center_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        # 3. Throttle Bar (Right)
        bar_w = 20
        bar_h = 200
        tx, ty = w - 40, h - 50 - bar_h
        cv2.rectangle(frame, (tx, ty), (tx + bar_w, ty + bar_h), (50, 50, 50), -1)
        cv2.rectangle(frame, (tx, ty), (tx + bar_w, ty + bar_h), (150, 150, 150), 2)
        
        # Fill
        fill_h = int(throttle * bar_h)
        if fill_h > 0:
            cv2.rectangle(frame, (tx, ty + bar_h - fill_h), (tx + bar_w, ty + bar_h), (0, 255, 0), -1)
        cv2.putText(frame, "GAS", (tx - 5, ty - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        cv2.putText(frame, f"{int(throttle*100)}%", (tx - 10, ty + bar_h + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # 4. Brake Bar (Left)
        bx, by = 20, h - 50 - bar_h
        cv2.rectangle(frame, (bx, by), (bx + bar_w, by + bar_h), (50, 50, 50), -1)
        cv2.rectangle(frame, (bx, by), (bx + bar_w, by + bar_h), (150, 150, 150), 2)
        
        # Fill
        fill_h = int(brake * bar_h)
        if fill_h > 0:
            cv2.rectangle(frame, (bx, by + bar_h - fill_h), (bx + bar_w, by + bar_h), (0, 0, 255), -1)
        cv2.putText(frame, "BRK", (bx - 5, by - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        cv2.putText(frame, f"{int(brake*100)}%", (bx - 10, by + bar_h + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
