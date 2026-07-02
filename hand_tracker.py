# pyrefly: ignore [missing-import]
import cv2
# pyrefly: ignore [missing-import]
import mediapipe as mp
import time
# pyrefly: ignore [missing-import]
from mediapipe.tasks import python
# pyrefly: ignore [missing-import]
from mediapipe.tasks.python import vision
from dataclasses import dataclass
from typing import List
import config
import urllib.request
import os

@dataclass
class HandData:
    world_landmarks: any
    image_landmarks: any
    handedness: str
    confidence: float

class HandTracker:
    def __init__(self):
        model_path = 'hand_landmarker.task'
        if not os.path.exists(model_path):
            print("Downloading hand_landmarker.task model...")
            url = 'https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task'
            urllib.request.urlretrieve(url, model_path)
            
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            num_hands=config.MP_MAX_HANDS,
            min_hand_detection_confidence=config.MP_MIN_DETECTION_CONFIDENCE,
            min_hand_presence_confidence=config.MP_MIN_TRACKING_CONFIDENCE,
            running_mode=vision.RunningMode.VIDEO
        )
        self.landmarker = vision.HandLandmarker.create_from_options(options)
        self.start_time = time.time()
        
        # Standard hand connections for drawing
        self.HAND_CONNECTIONS = [
            (0, 1), (1, 2), (2, 3), (3, 4),           # Thumb
            (0, 5), (5, 6), (6, 7), (7, 8),           # Index finger
            (5, 9), (9, 10), (10, 11), (11, 12),      # Middle finger
            (9, 13), (13, 14), (14, 15), (15, 16),    # Ring finger
            (13, 17), (0, 17), (17, 18), (18, 19), (19, 20) # Pinky
        ]

    def process(self, frame) -> List[HandData]:
        # Convert the frame to MediaPipe Image format
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
        
        # Calculate timestamp in ms
        timestamp_ms = int((time.time() - self.start_time) * 1000)
        
        # Perform hand landmark detection with temporal tracking
        detection_result = self.landmarker.detect_for_video(mp_image, timestamp_ms)
        
        hand_data_list = []
        if detection_result.hand_landmarks and detection_result.hand_world_landmarks:
            for idx in range(len(detection_result.hand_landmarks)):
                img_lm = detection_result.hand_landmarks[idx]
                world_lm = detection_result.hand_world_landmarks[idx]
                handedness_cat = detection_result.handedness[idx][0]
                
                label = handedness_cat.category_name
                score = handedness_cat.score
                
                hand_data_list.append(HandData(
                    world_landmarks=world_lm,
                    image_landmarks=img_lm,
                    handedness=label,
                    confidence=score
                ))
                
        return hand_data_list

    def draw_landmarks(self, frame, hand_data_list: List[HandData]):
        h, w, _ = frame.shape
        for hand_data in hand_data_list:
            # Draw connections (lines)
            for conn in self.HAND_CONNECTIONS:
                idx1, idx2 = conn
                lm1 = hand_data.image_landmarks[idx1]
                lm2 = hand_data.image_landmarks[idx2]
                pt1 = (int(lm1.x * w), int(lm1.y * h))
                pt2 = (int(lm2.x * w), int(lm2.y * h))
                cv2.line(frame, pt1, pt2, (0, 255, 0), 2)
            
            # Draw landmarks (points)
            for lm in hand_data.image_landmarks:
                pt = (int(lm.x * w), int(lm.y * h))
                cv2.circle(frame, pt, 4, (0, 0, 255), -1)
