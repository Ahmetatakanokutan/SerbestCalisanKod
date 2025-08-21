# -*- coding: utf-8 -*-

"""
This module handles the live video stream (from a webcam or video file).
It detects red triangles and blue hexagons in each frame and displays
the results in real-time.
"""

import cv2
import sys
import os

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shape_detector.detector import SekilTespitEdici

def visualize_results(frame, detections):
    """
    Draws the detected shapes onto the video frame.
    """
    if not detections:
        return frame

    for detection in detections:
        center = detection['merkez']
        color_str = detection['renk']
        shape_str = detection['sekil']
        
        # Determine drawing color based on detected color (BGR format)
        draw_color = (255, 0, 0) if color_str == 'mavi' else (0, 0, 255)

        # Draw a circle at the center of the shape
        cv2.circle(frame, center, 10, draw_color, 2)
        
        # Add an info text
        text = f"{color_str.upper()} {shape_str.upper()}"
        cv2.putText(frame, text, (center[0] - 40, center[1] - 15), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, draw_color, 2)
    
    return frame

def start_video_stream(source=0):
    """
    Initializes and processes the video stream from the specified source.
    
    Args:
        source (int or str): The camera index (e.g., 0) or the path to a video file.
    """
    # Explicitly specify the V4L2 backend for better stability on Linux
    cap = cv2.VideoCapture(source, cv2.CAP_V4L2)
    
    if not cap.isOpened():
        print(f"[ERROR] Could not open video source: {source}")
        print("Please check your camera connection or the file path.")
        return

    print("[INFO] Video stream started. Press 'q' to exit.")
    
    shape_detector = SekilTespitEdici()

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[INFO] Video stream ended.")
            break

        # Detect shapes
        red_triangles = shape_detector.kirmizi_ucgenleri_bul(frame)
        blue_hexagons = shape_detector.mavi_altigenleri_bul(frame)
        all_detections = red_triangles + blue_hexagons

        # Print info to console (optional)
        if all_detections:
            print(f"\rDetections: {len(all_detections)}", end="")

        # Visualize the results
        visualized_frame = visualize_results(frame, all_detections)

        # Display the processed frame
        cv2.imshow("Live Detection System", visualized_frame)

        # Exit the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release resources
    cap.release()
    cv2.destroyAllWindows()
    print("\n[INFO] Video stream closed.")
