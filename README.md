# Hand Movement Tracker

A real-time hand tracking and gesture recognition application using MediaPipe and OpenCV. This application uses your webcam to track hand movements and recognize gestures in real-time.

## Features
- Real-time hand tracking with 21 landmarks per hand
- Hand gesture recognition
- Support for multiple hands
- Visual display of hand landmarks and connections
- Real-time gesture classification

## Requirements
- Python 3.7+
- Webcam

## Installation

1. Clone this repository:
```bash
git clone https://github.com/Joel04kayy/HandMovementTracker.git
cd HandMovementTracker
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

## Usage

Run the program:
```bash
python main.py
```

- Press 'q' to quit the application

## Hand Gestures
The application recognizes the following hand gestures:
- Open Hand: All fingers up
- Closed Fist: All fingers down
- Peace Sign: Index and middle fingers up
- Pointing: Only index finger up
- Gun Sign: Thumb and index fingers up
- Four Fingers: All fingers up except thumb
- Thumbs Up: Only thumb up
- Middle Finger: Only middle finger up
- Ring Up: Only ring finger up
- Pinky Up: Only pinky up
- Two Fingers: Various combinations of two fingers
- Three Fingers: Various combinations of three fingers

## How it Works
- Uses MediaPipe for hand tracking and landmark detection
- Tracks 21 different points on each hand
- Calculates finger angles to determine gesture
- Supports tracking of multiple hands simultaneously 