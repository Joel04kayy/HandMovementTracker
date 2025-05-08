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
    print("Press 'q' to quit")

    # Variables for gesture timing
    gesture_start_time = None
    GESTURE_HOLD_TIME = 1.0  # seconds
    gesture_triggered = False

    while True:
        success, frame = cap.read()
        if not success:
            print("Failed to grab frame")
            break

        # Find and draw hands
        frame, hands, boxes = tracker.find_hands(frame)
        
        # Process each detected hand
        for i, hand in enumerate(hands):
            if hand:  # If hand landmarks were detected
                # Get finger states for this hand
                finger_states = tracker.get_finger_state(hand)
                
                # Get gesture for this hand
                gesture = tracker.get_hand_gesture(finger_states, hand)
                
                # Handle peace sign gesture with timing
                if gesture == "Peace Sign":
                    current_time = time.time()
                    
                    # Start timing if this is the first frame with peace sign
                    if gesture_start_time is None:
                        gesture_start_time = current_time
                        gesture_triggered = False
                    
                    # Check if we've held the gesture long enough
                    elif not gesture_triggered and (current_time - gesture_start_time) >= GESTURE_HOLD_TIME:
                        action_handler.lock_computer()
                        gesture_triggered = True
                else:
                    # Reset timing if gesture changes
                    gesture_start_time = None
                    gesture_triggered = False
                
                # Draw gesture text and timer above the hand
                if boxes and i < len(boxes):
                    x_min, y_min, x_max, y_max = boxes[i]
                    text = gesture
                    
                    # Add timer for peace sign
                    if gesture == "Peace Sign" and gesture_start_time is not None:
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