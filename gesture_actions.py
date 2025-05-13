import pyautogui
import time
from typing import Callable, Dict
import ctypes
from ctypes import wintypes
import keyboard  # Add this import
import numpy as np

# Windows API constants
KEYEVENTF_KEYUP = 0x0002
INPUT_KEYBOARD = 1
VK_F1 = 0x70  # Virtual key code for F1

# Define the Windows API structures
class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))
    ]

class INPUT(ctypes.Structure):
    class _INPUT(ctypes.Union):
        _fields_ = [
            ("ki", KEYBDINPUT),
            ("padding", ctypes.c_byte * 8)
        ]
    _anonymous_ = ("_input",)
    _fields_ = [
        ("type", wintypes.DWORD),
        ("_input", _INPUT)
    ]

class GestureActionHandler:
    def __init__(self):
        self.last_action_time = 0
        self.action_cooldown = 1.0  # seconds
        self.extra = ctypes.pointer(ctypes.c_ulong(0))
        self.last_volume_distance = None
        self.volume_change_threshold = 20  # Reduced threshold for easier activation
        self.volume_cooldown = 0.2  # Reduced cooldown for smoother control
        self.last_volume_change_time = 0
        self.volume_deadzone = 10  # Reduced deadzone
        self.volume_direction = None  # Track the direction of volume change
        self.volume_hold_start = None  # Track when we started holding the gesture
        self.volume_hold_threshold = 0.5  # Time to hold before continuous volume change

    def lock_computer(self) -> None:
        """Lock the computer using Windows API"""
        current_time = time.time()
        
        # Check if enough time has passed since last action
        if current_time - self.last_action_time < self.action_cooldown:
            return
            
        try:
            # Lock the computer using Windows API
            ctypes.windll.user32.LockWorkStation()
            self.last_action_time = current_time
            print("Computer locked successfully")
        except Exception as e:
            print(f"Error locking computer: {e}")

    def control_volume(self, index_tip, thumb_tip) -> None:
        """Control system volume based on distance between index finger and thumb"""
        if index_tip is None or thumb_tip is None:
            self.volume_hold_start = None
            return

        current_time = time.time()
        
        # Calculate distance between index finger and thumb
        current_distance = np.linalg.norm(np.array(index_tip) - np.array(thumb_tip))
        
        # Initialize last_volume_distance if it's None
        if self.last_volume_distance is None:
            self.last_volume_distance = current_distance
            return

        # Calculate distance change
        distance_change = current_distance - self.last_volume_distance
        
        # Check if we're in the deadzone
        if abs(distance_change) < self.volume_deadzone:
            self.volume_hold_start = None
            return

        # Determine direction of change
        new_direction = 1 if distance_change > 0 else -1
        
        # Check if we should start continuous volume change
        if abs(distance_change) > self.volume_change_threshold:
            if self.volume_hold_start is None:
                self.volume_hold_start = current_time
                self.volume_direction = new_direction
                # Initial volume change
                if new_direction > 0:
                    pyautogui.press('volumeup')
                else:
                    pyautogui.press('volumedown')
            elif self.volume_direction == new_direction:
                # Check if we've held long enough for continuous change
                if current_time - self.volume_hold_start >= self.volume_hold_threshold:
                    # Check cooldown for continuous changes
                    if current_time - self.last_volume_change_time >= self.volume_cooldown:
                        if new_direction > 0:
                            pyautogui.press('volumeup')
                        else:
                            pyautogui.press('volumedown')
                        self.last_volume_change_time = current_time
        else:
            # Reset hold if movement is too small
            self.volume_hold_start = None
            self.volume_direction = None

        # Update last distance
        self.last_volume_distance = current_distance

    def open_hand_action(self) -> None:
        """Action for open hand gesture"""
        print("Open Hand detected! 🖐️")

    def closed_fist_action(self) -> None:
        """Action for closed fist gesture"""
        print("Closed Fist detected! ✊")

    def pointing_action(self) -> None:
        """Action for pointing gesture"""
        print("Pointing detected! 👆")

    def gun_sign_action(self) -> None:
        """Action for gun sign gesture"""
        print("Gun Sign detected! 🔫")

    def thumbs_up_action(self) -> None:
        """Action for thumbs up gesture - presses space and types 9004"""
        pyautogui.press('space')
        time.sleep(0.1)  # Small delay after space
        keyboard.write('Password')  # Using keyboard.write instead of pyautogui.write
        print("Thumbs Up detected! 👍 - Space + 9004 pressed") 