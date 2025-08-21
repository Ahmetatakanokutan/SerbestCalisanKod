# -*- coding: utf-8 -*- 

"""
This module handles the live video stream (from a webcam or video file).
It detects red triangles and blue hexagons in each frame and displays
the results in real-time. This version uses GStreamer for more robust
camera handling on Linux systems.
"""

import cv2
import sys
import os
import time

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
        
        draw_color = (255, 0, 0) if color_str == 'mavi' else (0, 0, 255)

        cv2.circle(frame, center, 10, draw_color, 2)
        
        text = f"{color_str.upper()} {shape_str.upper()}"
        cv2.putText(frame, text, (center[0] - 40, center[1] - 15), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, draw_color, 2)
    
    return frame

def start_video_stream(pipeline):
    """
    Initializes and processes the video stream using a provided GStreamer pipeline.
    
    Args:
        pipeline (str): The full GStreamer pipeline string.
    """
    print(f"[INFO] Using GStreamer pipeline: {pipeline}")

    # Use CAP_GSTREAMER to tell OpenCV how to interpret the pipeline string
    cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
    
    if not cap.isOpened():
        print(f"[ERROR] Could not open video source with the provided GStreamer pipeline.")
        print("Please ensure GStreamer plugins are installed and the pipeline is correct.")
        return

    print("[INFO] Video stream started. Press 'q' to exit.")
    
    shape_detector = SekilTespitEdici()

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[WARNING] Failed to grab frame. The stream may have ended or there is a pipeline issue.")
            time.sleep(0.5)
            continue

        # Detect shapes
        red_triangles = shape_detector.kirmizi_ucgenleri_bul(frame)
        blue_hexagons = shape_detector.mavi_altigenleri_bul(frame)
        all_detections = red_triangles + blue_hexagons

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
