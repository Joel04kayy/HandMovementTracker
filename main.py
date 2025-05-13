import cv2
import time
from hand_tracker import HandTracker
from gesture_actions import GestureActionHandler

def main():
    # Initialize webcam
    cap = cv2.VideoCapture(0)
    tracker = HandTracker()
    action_handler = GestureActionHandler()

    print("Make a peace sign (✌️) to lock your computer")
    print("Hold index and thumb up to control volume")
    print("Hold thumbs up to unlock")
    print("Press 'q' to quit")

    # Variables for gesture timing
    gesture_start_time = None
    GESTURE_HOLD_TIME = 1.0  # seconds
    gesture_triggered = False
    last_gesture = None

    while True:
        success, frame = cap.read()
        if not success:
            print("Failed to grab frame")
            break

        # Find and draw hands
        frame, hands, boxes = tracker.find_hands(frame)
        
        # Process each detected hand
        for i, hand in enumerate(hands):
            if hand:
                # Get finger states for this hand
                finger_states = tracker.get_finger_state(hand)
                
                # Get gesture for this hand
                gesture = tracker.get_hand_gesture(finger_states, hand)
                
                # Handle volume control gesture
                if gesture == "Volume Control":
                    # Get index finger and thumb positions
                    index_tip = hand[8]  # Index finger tip
                    thumb_tip = hand[4]  # Thumb tip
                    action_handler.control_volume(index_tip, thumb_tip)
                    gesture_start_time = None
                    gesture_triggered = False
                
                # Handle peace sign gesture with timing
                elif gesture == "Peace Sign":
                    current_time = time.time()
                    
                    # Start timing if this is the first frame with peace sign
                    if gesture_start_time is None:
                        gesture_start_time = current_time
                        gesture_triggered = False
                    
                    # Check if we've held the gesture long enough
                    elif not gesture_triggered and (current_time - gesture_start_time) >= GESTURE_HOLD_TIME:
                        action_handler.lock_computer()
                        gesture_triggered = True
                
                # Handle thumbs up gesture with timing
                elif gesture == "Thumbs Up":
                    current_time = time.time()
                    
                    # Start timing if this is the first frame with thumbs up
                    if gesture_start_time is None:
                        gesture_start_time = current_time
                        gesture_triggered = False
                    
                    # Check if we've held the gesture long enough
                    elif not gesture_triggered and (current_time - gesture_start_time) >= GESTURE_HOLD_TIME:
                        action_handler.thumbs_up_action()
                        gesture_triggered = True
                else:
                    # Reset timing if gesture changes
                    gesture_start_time = None
                    gesture_triggered = False
                
                # Draw gesture text and timer above the hand
                if boxes and i < len(boxes):
                    x_min, y_min, x_max, y_max = boxes[i]
                    text = gesture
                    
                    # Add timer for timed gestures
                    if gesture in ["Peace Sign", "Thumbs Up"] and gesture_start_time is not None:
                        elapsed = time.time() - gesture_start_time
                        if not gesture_triggered:
                            text += f" ({elapsed:.1f}s)"
                    
                    cv2.putText(frame, text, (x_min, y_min - 10),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

        # Display instructions
        cv2.putText(frame, 'Press q to quit', (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # Show the frame
        cv2.imshow("Hand Tracking", frame)
        
        # Break the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main() 