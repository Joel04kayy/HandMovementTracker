import cv2
from hand_tracker import HandTracker

def main():
    # Initialize webcam
    cap = cv2.VideoCapture(0)
    tracker = HandTracker()

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
                gesture = tracker.get_hand_gesture(finger_states)
                
                # Draw gesture text above the hand
                if boxes and i < len(boxes):
                    x_min, y_min, x_max, y_max = boxes[i]
                    cv2.putText(frame, gesture, (x_min, y_min - 10),
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