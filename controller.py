import sys
import time

class BaseController:
    def set_steering(self, value: float): pass
    def set_throttle(self, value: float): pass
    def set_brake(self, value: float): pass
    def update(self, mode: int, fps: int = 0): pass

class ConsoleController(BaseController):
    def __init__(self):
        self.steering = 0.0
        self.throttle = 0.0
        self.brake = 0.0
        print("\n" * 2) # Make some space
        
    def set_steering(self, value: float): self.steering = value
    def set_throttle(self, value: float): self.throttle = value
    def set_brake(self, value: float): self.brake = value
    
    def _draw_bar(self, val: float, length: int = 16, centered: bool = False) -> str:
        if centered:
            # [-1 to +1] range
            mid = length // 2
            bar = ["░"] * length
            if val < 0:
                fill_len = int(abs(val) * mid)
                for i in range(mid - fill_len, mid): bar[i] = "█"
            else:
                fill_len = int(val * mid)
                for i in range(mid, mid + fill_len): bar[i] = "█"
            bar[mid] = "|" if val == 0 else bar[mid]
            return "".join(bar)
        else:
            # [0 to 1] range
            fill_len = int(val * length)
            bar = ["█"] * fill_len + ["░"] * (length - fill_len)
            return "".join(bar)
            
    def update(self, mode: int, fps: int = 0):
        if mode == 0:
            status = "NO HANDS DETECTED    "
        elif mode == 1:
            status = "ONE HAND (FALLBACK)  "
        else:
            status = "TWO HANDS TRACKING   "
            
        s_bar = self._draw_bar(self.steering, 20, True)
        t_bar = self._draw_bar(self.throttle, 15)
        b_bar = self._draw_bar(self.brake, 15)
        
        # \r to overwrite line
        sys.stdout.write(f"\r[{status}] STEER: {s_bar} {self.steering:5.2f} | GAS: {t_bar} {self.throttle:4.2f} | BRK: {b_bar} {self.brake:4.2f} | FPS: {fps:3d}")
        sys.stdout.flush()

class GamepadController(BaseController):
    def __init__(self):
        try:
            # pyrefly: ignore [missing-import]
            import vgamepad as vg
            self.gamepad = vg.VX360Gamepad()
            self.steering = 0.0
            self.throttle = 0.0
            self.brake = 0.0
            print("Virtual Xbox 360 controller initialized (vgamepad).")
        except ImportError:
            print("ERROR: vgamepad not installed. Please install it using `pip install vgamepad`.")
            sys.exit(1)
        except Exception as e:
            print(f"ERROR: Could not initialize vgamepad: {e}")
            sys.exit(1)

    def set_steering(self, value: float):
        self.steering = value
        
    def set_throttle(self, value: float):
        self.throttle = value
        
    def set_brake(self, value: float):
        self.brake = value
        
    def update(self, mode: int, fps: int = 0):
        # Steering mapped to left joystick X axis. Value should be between -1.0 and 1.0.
        self.gamepad.left_joystick_float(x_value_float=self.steering, y_value_float=0.0)
        
        # Throttle and Brake mapped to triggers. Value should be int between 0 and 255.
        self.gamepad.right_trigger(value=int(self.throttle * 255))
        self.gamepad.left_trigger(value=int(self.brake * 255))
        
        self.gamepad.update()

def create_controller(mode: str) -> BaseController:
    if mode == "console":
        return ConsoleController()
    elif mode == "gamepad":
        if sys.platform != "win32":
            print("WARNING: Gamepad mode is intended for Windows. Using it on Linux might not work without extra setup. Use --mode console for dev testing.")
        return GamepadController()
    else:
        raise ValueError(f"Unknown controller mode: {mode}")
