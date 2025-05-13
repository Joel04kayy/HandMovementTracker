import cv2
import numpy as np
import os
import urllib.request
import time
from datetime import datetime
from hand_tracker import HandTracker

def load_model():
    # Load the pre-trained model and configuration
    model_path = "yolov3.weights"
    config_path = "yolov3.cfg"
    
    # Download the model files if they don't exist
    if not os.path.exists(model_path):
        print("Downloading YOLOv3 weights...")
        # Using a mirror from GitHub
        urllib.request.urlretrieve(
            "https://github.com/AlexeyAB/darknet/releases/download/darknet_yolo_v3_optimal/yolov3.weights",
            model_path
        )
    
    if not os.path.exists(config_path):
        print("Downloading YOLOv3 configuration...")
        # Using the configuration from the darknet repository
        urllib.request.urlretrieve(
            "https://raw.githubusercontent.com/AlexeyAB/darknet/master/cfg/yolov3.cfg",
            config_path
        )
    
    # Load the network
    net = cv2.dnn.readNetFromDarknet(config_path, model_path)
    
    # Load class names
    with open("coco.names", "r") as f:
        classes = [line.strip() for line in f.readlines()]
    
    return net, classes

def process_frame(frame, net, classes, confidence_threshold=0.5):
    height, width, _ = frame.shape
    
    # Create a blob from the frame
    blob = cv2.dnn.blobFromImage(frame, 1/255.0, (416, 416), swapRB=True, crop=False)
    
    # Set the input to the network
    net.setInput(blob)
    
    # Get the output layer names
    layer_names = net.getLayerNames()
    output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]
    
    # Run forward pass
    outputs = net.forward(output_layers)
    
    # Process detections
    boxes = []
    confidences = []
    class_ids = []
    
    for output in outputs:
        for detection in output:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            
            if confidence > confidence_threshold:
                # Object detected
                center_x = int(detection[0] * width)
                center_y = int(detection[1] * height)
                w = int(detection[2] * width)
                h = int(detection[3] * height)
                
                # Rectangle coordinates
                x = int(center_x - w / 2)
                y = int(center_y - h / 2)
                
                boxes.append([x, y, w, h])
                confidences.append(float(confidence))
                class_ids.append(class_id)
    
    # Apply non-maximum suppression
    indices = cv2.dnn.NMSBoxes(boxes, confidences, confidence_threshold, 0.4)
    
    return boxes, confidences, class_ids, indices

def draw_detections(frame, boxes, confidences, class_ids, indices, classes, fps, hand_boxes=None, gesture_texts=None):
    if len(indices) > 0:
        for i in indices.flatten():
            x, y, w, h = boxes[i]
            label = str(classes[class_ids[i]])
            confidence = confidences[i]
            
            # Draw bounding box
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
            # Add label with confidence
            text = f"{label}: {confidence:.2f}"
            cv2.putText(frame, text, (x, y - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    
    # Draw hand boxes and gestures
    if hand_boxes and gesture_texts:
        for box, gesture in zip(hand_boxes, gesture_texts):
            x_min, y_min, x_max, y_max = box
            
            # Draw hand bounding box
            cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (255, 0, 0), 2)
            
            # Add gesture label
            cv2.putText(frame, gesture, (x_min, y_min - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
    
    # Add FPS counter
    cv2.putText(frame, f"FPS: {fps:.1f}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    
    return frame

def save_frame(frame):
    # Create screenshots directory if it doesn't exist
    if not os.path.exists("screenshots"):
        os.makedirs("screenshots")
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"screenshots/screenshot_{timestamp}.jpg"
    
    # Save the frame
    cv2.imwrite(filename, frame)
    print(f"Saved screenshot: {filename}")

def main():
    # Initialize webcam
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Could not open webcam")
        return
    
    print("Loading models...")
    net, classes = load_model()
    hand_tracker = HandTracker()
    print("Models loaded successfully!")
    
    # Initialize variables
    confidence_threshold = 0.5
    frame_count = 0
    start_time = time.time()
    fps = 0
    
    print("\nControls:")
    print("Press 'q' to quit")
    print("Press 's' to save screenshot")
    print("Press 'c' to toggle confidence threshold")
    print("\nHand Gestures:")
    print("- Open Hand: All fingers up")
    print("- Closed Fist: All fingers down")
    print("- Peace Sign: Index and middle fingers up")
    print("- Pointing: Only index finger up")
    print("- Gun Sign: Thumb and index fingers up")
    print("- Four Fingers: All fingers up except thumb")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read frame")
            break
        
        # Calculate FPS
        frame_count += 1
        if frame_count >= 30:  # Update FPS every 30 frames
            end_time = time.time()
            fps = frame_count / (end_time - start_time)
            frame_count = 0
            start_time = time.time()
        
        # Process hand tracking
        frame, hands, hand_boxes = hand_tracker.find_hands(frame)
        gesture_texts = []
        
        if hands:
            # Get finger states and gestures for each detected hand
            for hand in hands:
                finger_states = hand_tracker.get_finger_state(hand)
                gesture = hand_tracker.get_hand_gesture(finger_states)
                gesture_texts.append(gesture)
        
        # Process object detection
        boxes, confidences, class_ids, indices = process_frame(frame, net, classes, confidence_threshold)
        
        # Draw detections
        frame = draw_detections(frame, boxes, confidences, class_ids, indices, classes, fps, hand_boxes, gesture_texts)
        
        # Display the frame
        cv2.imshow('Object Detection with Hand Tracking', frame)
        
        # Handle key presses
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            save_frame(frame)
        elif key == ord('c'):
            confidence_threshold = 0.3 if confidence_threshold > 0.3 else 0.5
            print(f"Confidence threshold: {confidence_threshold}")
    
    # Clean up
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main() 