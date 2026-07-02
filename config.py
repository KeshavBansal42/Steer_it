import sys

# Camera
CAMERA_INDEX = 0
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_FPS = 30

# MediaPipe
MP_MODEL_COMPLEXITY = 1        # 0=Lite (faster), 1=Full (more accurate)
MP_MAX_HANDS = 2               # Track both hands
MP_MIN_DETECTION_CONFIDENCE = 0.7
MP_MIN_TRACKING_CONFIDENCE = 0.6

# Steering
STEERING_MAX_ANGLE = 45.0      # Max tilt angle in degrees for full lock
STEERING_DEAD_ZONE = 3.0       # Degrees — ignore small jitter near center
STEERING_SENSITIVITY = 2.0     # Multiplier curve exponent (1.0=linear, 2.0=quadratic)

# Throttle / Brake (Pinch Virtual Triggers)
# Measured as the reduction in normalized pixel distance between Index and Thumb tips.
PINCH_MAX_TRIGGER = 0.10       # 10% frame width reduction = full throttle/brake
PINCH_DEAD_ZONE = 0.02         # 2% deadzone to ignore resting jitter

# One Euro Filter params
FILTER_FREQ = 30.0             # Expected FPS
FILTER_MINCUTOFF = 1.7         # Higher = more jitter removal, more lag
FILTER_BETA = 0.3              # Higher = less lag for fast movements
FILTER_DCUTOFF = 1.0

# Controller
CONTROLLER_UPDATE_RATE = 60    # Hz — how often to push to virtual gamepad

# Output Mode
DEFAULT_MODE = "console" if sys.platform == "linux" else "gamepad"
