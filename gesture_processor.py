import math
import time
import config
from hand_tracker import HandData
from typing import List, Tuple
from filters import OneEuroFilter

class GestureProcessor:
    def __init__(self):
        self.steering_neutral = 0.0
        self.depth_neutral = 0.0
        
        t0 = time.time()
        self.steer_filter = OneEuroFilter(t0, 0.0, min_cutoff=config.FILTER_MINCUTOFF, beta=config.FILTER_BETA)
        self.depth_filter = OneEuroFilter(t0, 0.0, min_cutoff=config.FILTER_MINCUTOFF, beta=config.FILTER_BETA)
        
        self.is_calibrated = False

    def set_calibration(self, steering_neutral: float, depth_neutral: float):
        self.steering_neutral = steering_neutral
        self.depth_neutral = depth_neutral
        self.is_calibrated = True

    def compute(self, hands: List[HandData]) -> Tuple[float, float, float, int]:
        """
        Returns: (steering[-1 to 1], throttle[0 to 1], brake[0 to 1], mode)
        mode: 0 = no hands, 1 = one hand, 2 = two hands
        """
        if not hands:
            return 0.0, 0.0, 0.0, 0

        t = time.time()
        
        # Calculate Steering and Depth
        raw_steering = 0.0
        raw_depth = 0.0
        mode = len(hands)

        if mode >= 2:
            # Two hand mode
            h1, h2 = hands[0], hands[1]
            if h1.image_landmarks[0].x < h2.image_landmarks[0].x:
                left_hand, right_hand = h1, h2
            else:
                left_hand, right_hand = h2, h1
                
            # --- Steering (Roll) ---
            l_wrist_img = left_hand.image_landmarks[0]
            r_wrist_img = right_hand.image_landmarks[0]
            angle_rad = math.atan2(r_wrist_img.y - l_wrist_img.y, r_wrist_img.x - l_wrist_img.x)
            raw_steering = math.degrees(angle_rad)
            
            # --- Depth (Throttle / Brake) ---
            # Yoke Push/Pull method: tracking the pixel distance between wrists
            raw_depth = math.sqrt((r_wrist_img.x - l_wrist_img.x)**2 + (r_wrist_img.y - l_wrist_img.y)**2)
            
        else:
            # One hand fallback mode
            wrist = hands[0].image_landmarks[0]
            mcp = hands[0].image_landmarks[9]
            
            # Steering
            angle_rad = math.atan2(wrist.y - mcp.y, wrist.x - mcp.x)
            raw_steering = math.degrees(angle_rad) - 90.0
            
            # Depth (distance from wrist to knuckles in image space)
            raw_depth = math.sqrt((mcp.x - wrist.x)**2 + (mcp.y - wrist.y)**2)

        # Adjust for calibration
        raw_steering -= self.steering_neutral
        
        # For depth, we want the difference from neutral
        depth_diff = raw_depth - self.depth_neutral

        # 3. Filter Signals
        filtered_steering = self.steer_filter(t, raw_steering)
        filtered_depth = self.depth_filter(t, depth_diff)

        # 4. Map to Output Ranges
        # Steering mapping
        steering_val = self._map_with_deadzone(
            filtered_steering, 
            config.STEERING_DEAD_ZONE, 
            config.STEERING_MAX_ANGLE
        )
        steering_val = self._apply_curve(steering_val, config.STEERING_SENSITIVITY)
        steering_val = max(-1.0, min(1.0, steering_val)) # clamp
        
        # Throttle / Brake mapping (depth)
        throttle_val = 0.0
        brake_val = 0.0
        
        # Pushed forward (depth increases, positive difference) = throttle
        if filtered_depth > config.DEPTH_DEAD_ZONE:
            t_val = (filtered_depth - config.DEPTH_DEAD_ZONE) / (config.DEPTH_MAX_THROTTLE - config.DEPTH_DEAD_ZONE)
            throttle_val = max(0.0, min(1.0, t_val))
            
        # Pulled back (depth decreases, negative difference) = brake
        elif filtered_depth < -config.DEPTH_DEAD_ZONE:
            b_val = (abs(filtered_depth) - config.DEPTH_DEAD_ZONE) / (config.DEPTH_MAX_BRAKE - config.DEPTH_DEAD_ZONE)
            brake_val = max(0.0, min(1.0, b_val))
            
        return steering_val, throttle_val, brake_val, mode

    def _map_with_deadzone(self, value: float, dead_zone: float, max_val: float) -> float:
        """Map value to [-1, 1] considering dead zone and max limit."""
        if abs(value) <= dead_zone:
            return 0.0
        
        sign = 1 if value >= 0 else -1
        magnitude = abs(value) - dead_zone
        range_max = max_val - dead_zone
        
        if range_max <= 0: return 0.0 # prevent div by zero
        
        normalized = magnitude / range_max
        return sign * normalized

    def _apply_curve(self, value: float, exponent: float) -> float:
        """Apply response curve to normalized value [-1, 1]."""
        sign = 1 if value >= 0 else -1
        return sign * (abs(value) ** exponent)
