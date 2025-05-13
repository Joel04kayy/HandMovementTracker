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

    def check_finger_spacing(self, tip1, tip2):
        """Check if two fingers are properly spaced"""
        distance = np.linalg.norm(np.array(tip1) - np.array(tip2))
        return 10 < distance < 150  # Made more lenient for volume control

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
        Determine which fingers are up based on landmark positions and angles
        Returns a list of 5 boolean values representing thumb, index, middle, ring, and pinky
        """
        if not hand_landmarks:
            return [False] * 5

        # Get coordinates of finger tips and their corresponding PIP joints
        # Thumb
        thumb_tip = hand_landmarks[4]
        thumb_ip = hand_landmarks[3]
        thumb_mcp = hand_landmarks[2]
        thumb_cmc = hand_landmarks[1]
        
        # Index finger
        index_tip = hand_landmarks[8]
        index_pip = hand_landmarks[6]
        index_mcp = hand_landmarks[5]
        index_cmc = hand_landmarks[0]
        
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

        def calculate_angle(p1, p2, p3):
            """Calculate angle between three points"""
            v1 = np.array([p1[0] - p2[0], p1[1] - p2[1]])
            v2 = np.array([p3[0] - p2[0], p3[1] - p2[1]])
            
            # Calculate norms
            norm_v1 = np.linalg.norm(v1)
            norm_v2 = np.linalg.norm(v2)
            
            # Check for zero vectors
            if norm_v1 == 0 or norm_v2 == 0:
                return 0
                
            # Calculate cosine of angle
            cos_angle = np.dot(v1, v2) / (norm_v1 * norm_v2)
            # Clamp cos_angle to valid range
            cos_angle = np.clip(cos_angle, -1.0, 1.0)
            
            return np.degrees(np.arccos(cos_angle))

        def is_finger_up(tip, pip, mcp, is_thumb=False):
            """Check if a finger is up based on angles and positions"""
            # Calculate angles
            angle1 = calculate_angle(tip, pip, mcp)
            
            # For thumb, we need additional checks
            if is_thumb:
                # Check angle between thumb tip and index finger base
                angle2 = calculate_angle(tip, mcp, index_cmc)
                # Thumb is up if both angles are large enough
                return angle1 > 150 and angle2 > 120
            
            # For other fingers, check if tip is above PIP joint
            return angle1 > 160 and tip[1] < pip[1]

        def check_finger_alignment(tip, pip, mcp):
            """Check if finger is properly aligned"""
            # Calculate vertical alignment
            vertical_alignment = abs(tip[0] - mcp[0]) < 30
            # Calculate finger length ratio
            finger_length = np.linalg.norm(np.array(tip) - np.array(mcp))
            base_length = np.linalg.norm(np.array(pip) - np.array(mcp))
            length_ratio = finger_length / base_length if base_length > 0 else 0
            
            return vertical_alignment and length_ratio > 1.2

        # Check each finger
        thumb_up = is_finger_up(thumb_tip, thumb_ip, thumb_mcp, True)
        index_up = is_finger_up(index_tip, index_pip, index_mcp) and check_finger_alignment(index_tip, index_pip, index_mcp)
        middle_up = is_finger_up(middle_tip, middle_pip, middle_mcp) and check_finger_alignment(middle_tip, middle_pip, middle_mcp)
        ring_up = is_finger_up(ring_tip, ring_pip, ring_mcp) and check_finger_alignment(ring_tip, ring_pip, ring_mcp)
        pinky_up = is_finger_up(pinky_tip, pinky_pip, pinky_mcp) and check_finger_alignment(pinky_tip, pinky_pip, pinky_mcp)

        return [thumb_up, index_up, middle_up, ring_up, pinky_up]

    def get_hand_gesture(self, finger_states, hand_landmarks):
        """
        Determine the gesture based on finger states
        Returns a string describing the gesture
        """
        if not finger_states or not hand_landmarks:
            return "No hand detected"

        thumb, index, middle, ring, pinky = finger_states

        # Volume control gesture (only index and thumb up, others down)
        if index and thumb and not (middle or ring or pinky):
            # Check if the gesture is held for volume control
            spacing = self.check_finger_spacing(hand_landmarks[4], hand_landmarks[8])  # Check spacing between thumb and index
            print(f"Volume control check - Thumb: {thumb}, Index: {index}, Spacing: {spacing}")
            if spacing:
                return "Volume Control"

        # Peace sign detection (index and middle up, others down)
        if index and middle and not (ring or pinky or thumb):
            # Additional check for peace sign
            if self.check_finger_spacing(hand_landmarks[8], hand_landmarks[12]):  # Check spacing between index and middle tips
                return "Peace Sign"
            
        # Count how many fingers are up
        fingers_up = sum(finger_states)

        # Basic gesture recognition with strict checks
        if fingers_up >= 4:
            # Check if all fingers are properly spread
            if all([index, middle, ring, pinky]):
                return "Open Hand"
        elif fingers_up == 0:
            # Check if all fingers are properly curled
            if not any([index, middle, ring, pinky, thumb]):
                return "Closed Fist"
        elif index and not (middle or ring or pinky):
            # Pointing gesture
            if not thumb:  # Thumb should be down for pointing
                return "Pointing"
        elif thumb and index and not (middle or ring or pinky):
            # Gun sign
            if self.check_finger_spacing(hand_landmarks[4], hand_landmarks[8]):  # Check spacing between thumb and index
                return "Gun Sign"
        elif all([index, middle, ring, pinky]) and not thumb:
            # Four fingers
            if self.check_finger_spacing(hand_landmarks[8], hand_landmarks[20]):  # Check spacing between index and pinky
                return "Four Fingers"
        elif fingers_up == 1:
            if index and not any([middle, ring, pinky, thumb]):
                return "Pointing"
            elif middle and not any([index, ring, pinky, thumb]):
                return "Middle Finger"
            elif ring and not any([index, middle, pinky, thumb]):
                return "Ring Up"
            elif pinky and not any([index, middle, ring, thumb]):
                return "Pinky Up"
            elif thumb and not any([index, middle, ring, pinky]):
                return "Thumbs Up"
        elif fingers_up == 2:
            if index and middle and not (ring or pinky or thumb):
                if self.check_finger_spacing(hand_landmarks[8], hand_landmarks[12]):
                    return "Peace Sign"
            elif thumb and index and not (middle or ring or pinky):
                if self.check_finger_spacing(hand_landmarks[4], hand_landmarks[8]):
                    return "Gun Sign"
            elif index and ring and not (middle or pinky or thumb):
                if self.check_finger_spacing(hand_landmarks[8], hand_landmarks[16]):
                    return "Two Fingers"
        elif fingers_up == 3:
            # Check if the three fingers are properly spread
            if self.check_finger_spacing(hand_landmarks[8], hand_landmarks[20]):
                return "Three Fingers"
        
        return "Unknown Gesture" 