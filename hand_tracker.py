import cv2
import mediapipe as mp
import numpy as np

class HandTracker:
    def __init__(self, mode=False, max_hands=2, detection_confidence=0.5, tracking_confidence=0.5):
        self.mode = mode
        self.max_hands = max_hands
        self.detection_confidence = detection_confidence
        self.tracking_confidence = tracking_confidence

        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=self.mode,
            max_num_hands=self.max_hands,
            min_detection_confidence=self.detection_confidence,
            min_tracking_confidence=self.tracking_confidence
        )
        self.mp_draw = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles

    def find_hands(self, frame, draw=True):
        # Convert the BGR image to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process the frame and detect hands
        self.results = self.hands.process(frame_rgb)
        
        # Initialize list to store hand landmarks and bounding boxes
        all_hands = []
        hand_boxes = []
        
        # If hands are detected
        if self.results.multi_hand_landmarks:
            for hand_landmarks in self.results.multi_hand_landmarks:
                if draw:
                    # Draw hand landmarks with custom style
                    self.mp_draw.draw_landmarks(
                        frame,
                        hand_landmarks,
                        self.mp_hands.HAND_CONNECTIONS,
                        self.mp_drawing_styles.get_default_hand_landmarks_style(),
                        self.mp_drawing_styles.get_default_hand_connections_style()
                    )
                
                # Get landmarks for this hand
                hand = []
                x_coords = []
                y_coords = []
                
                for landmark in hand_landmarks.landmark:
                    h, w, c = frame.shape
                    x, y = int(landmark.x * w), int(landmark.y * h)
                    hand.append([x, y])
                    x_coords.append(x)
                    y_coords.append(y)
                
                # Calculate bounding box
                x_min = max(0, min(x_coords) - 20)
                y_min = max(0, min(y_coords) - 20)
                x_max = min(w, max(x_coords) + 20)
                y_max = min(h, max(y_coords) + 20)
                
                all_hands.append(hand)
                hand_boxes.append((x_min, y_min, x_max, y_max))
        
        return frame, all_hands, hand_boxes

    def get_finger_state(self, hand_landmarks):
        """
        Determine which fingers are up based on landmark positions
        Returns a list of 5 boolean values representing thumb, index, middle, ring, and pinky
        """
        if not hand_landmarks:
            return [False] * 5

        # Get coordinates of finger tips and their corresponding PIP joints
        # Thumb
        thumb_tip = hand_landmarks[4]
        thumb_ip = hand_landmarks[3]
        thumb_mcp = hand_landmarks[2]
        
        # Index finger
        index_tip = hand_landmarks[8]
        index_pip = hand_landmarks[6]
        index_mcp = hand_landmarks[5]
        
        # Middle finger
        middle_tip = hand_landmarks[12]
        middle_pip = hand_landmarks[10]
        middle_mcp = hand_landmarks[9]
        
        # Ring finger
        ring_tip = hand_landmarks[16]
        ring_pip = hand_landmarks[14]
        ring_mcp = hand_landmarks[13]
        
        # Pinky
        pinky_tip = hand_landmarks[20]
        pinky_pip = hand_landmarks[18]
        pinky_mcp = hand_landmarks[17]

        # Calculate angles for each finger
        def calculate_angle(p1, p2, p3):
            v1 = np.array([p1[0] - p2[0], p1[1] - p2[1]])
            v2 = np.array([p3[0] - p2[0], p3[1] - p2[1]])
            cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
            angle = np.arccos(np.clip(cos_angle, -1.0, 1.0))
            return np.degrees(angle)

        # Check if fingers are up based on angles and positions
        def is_finger_up(tip, pip, mcp, is_thumb=False):
            angle = calculate_angle(tip, pip, mcp)
            if is_thumb:
                # Thumb has different angle threshold
                return angle > 150  # Thumb is up when angle is large
            return angle > 160  # Other fingers are up when angle is large

        thumb_up = is_finger_up(thumb_tip, thumb_ip, thumb_mcp, True)
        index_up = is_finger_up(index_tip, index_pip, index_mcp)
        middle_up = is_finger_up(middle_tip, middle_pip, middle_mcp)
        ring_up = is_finger_up(ring_tip, ring_pip, ring_mcp)
        pinky_up = is_finger_up(pinky_tip, pinky_pip, pinky_mcp)

        return [thumb_up, index_up, middle_up, ring_up, pinky_up]

    def get_hand_gesture(self, finger_states):
        """
        Determine the gesture based on finger states
        Returns a string describing the gesture
        """
        if not finger_states:
            return "No hand detected"

        thumb, index, middle, ring, pinky = finger_states

        # Count how many fingers are up
        fingers_up = sum(finger_states)

        # Basic gesture recognition with more lenient conditions
        if fingers_up >= 4:
            return "Open Hand"
        elif fingers_up == 0:
            return "Closed Fist"
        elif index and middle and not (ring or pinky):
            return "Peace Sign"
        elif index and not (middle or ring or pinky):
            return "Pointing"
        elif thumb and index and not (middle or ring or pinky):
            return "Gun Sign"
        elif all([index, middle, ring, pinky]) and not thumb:
            return "Four Fingers"
        elif fingers_up == 1:
            if index:
                return "Pointing"
            elif middle:
                return "Middle Finger"
            elif ring:
                return "Ring Up"
            elif pinky:
                return "Pinky Up"
            elif thumb:
                return "Thumbs Up"
        elif fingers_up == 2:
            if index and middle:
                return "Peace Sign"
            elif thumb and index:
                return "Gun Sign"
            elif index and ring:
                return "Two Fingers"
        elif fingers_up == 3:
            if index and middle and ring:
                return "Three Fingers"
            elif index and middle and pinky:
                return "Three Fingers"
            else:
                return "Three Fingers"
        else:
            return f"Custom Gesture ({fingers_up} fingers up)" 