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
        self.volume_change_threshold = 10  # Minimum distance change to trigger volume change

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
            return

        # Calculate distance between index finger and thumb
        current_distance = np.linalg.norm(np.array(index_tip) - np.array(thumb_tip))
        
        # Initialize last_volume_distance if it's None
        if self.last_volume_distance is None:
            self.last_volume_distance = current_distance
            return

        # Calculate distance change
        distance_change = current_distance - self.last_volume_distance
        
        # Only change volume if the distance change is significant
        if abs(distance_change) > self.volume_change_threshold:
            if distance_change > 0:
                # Increase volume
                pyautogui.press('volumeup')
                print("Volume increased")
            else:
                # Decrease volume
                pyautogui.press('volumedown')
                print("Volume decreased")
            
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