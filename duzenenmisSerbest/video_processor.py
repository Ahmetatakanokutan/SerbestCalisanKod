# -*- coding: utf-8 -*- 

"""
This module handles the live video stream. It detects shapes, calculates
their GPS coordinates using simulated drone telemetry, and saves the results
to a CSV file in real-time.
"""

import cv2
import sys
import os
import time
import csv

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from shape_detector.detector import SekilTespitEdici
from gps.calculator import pixel_to_gps
from config import OUTPUT_CSV, HOME_ALTITUDE

# --- SIMULATED DRONE TELEMETRY ---
# In a real application, this data would come from a MAVLink connection.
SIMULATED_DRONE_LAT = 41.0082  # Example: Istanbul latitude
SIMULATED_DRONE_LON = 28.9784  # Example: Istanbul longitude
SIMULATED_DRONE_ALT = 150.0    # Example: Altitude in meters

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
    Initializes and processes the video stream, performs detection,
    calculates GPS, and saves results.
    """
    print(f"[INFO] Using GStreamer pipeline: {pipeline}")
    cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
    
    if not cap.isOpened():
        print("[ERROR] Could not open video source with the provided GStreamer pipeline.")
        return

    print("[INFO] Video stream started. Press 'q' to exit.")
    
    shape_detector = SekilTespitEdici()
    
    # Open the CSV file for writing
    csv_file = None
    try:
        csv_file = open(OUTPUT_CSV, "a", newline="", encoding='utf-8')
        csv_writer = csv.writer(csv_file)
        
        while True:
            ret, frame = cap.read()
            if not ret:
                print("[WARNING] Failed to grab frame.")
                time.sleep(0.5)
                continue

            image_height, image_width, _ = frame.shape
            
            # Calculate flight altitude relative to home
            flight_altitude = SIMULATED_DRONE_ALT - HOME_ALTITUDE

            # Detect shapes
            red_triangles = shape_detector.kirmizi_ucgenleri_bul(frame)
            blue_hexagons = shape_detector.mavi_altigenleri_bul(frame)
            all_detections = red_triangles + blue_hexagons

            # If shapes are detected, process and save them
            if all_detections:
                for detection in all_detections:
                    center_x, center_y = detection['merkez']
                    
                    # Calculate GPS coordinate for the detected shape
                    latitude, longitude = pixel_to_gps(
                        center_x, center_y, image_width, image_height,
                        SIMULATED_DRONE_LAT, SIMULATED_DRONE_LON, flight_altitude
                    )
                    
                    # Write the result to the CSV file
                    csv_writer.writerow([
                        time.strftime("%Y-%m-%d %H:%M:%S"),
                        "live_video",  # Filename placeholder
                        detection['sekil'],
                        detection['renk'],
                        f"{latitude:.7f}",
                        f"{longitude:.7f}"
                    ])
                
                # Ensure data is written to disk immediately
                csv_file.flush()

            # Visualize the results on the frame
            visualized_frame = visualize_results(frame, all_detections)
            cv2.imshow("Live Detection System", visualized_frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    
finally:
        # Release resources
        if csv_file:
            csv_file.close()
        cap.release()
        cv2.destroyAllWindows()
        print("\n[INFO] Video stream and resources closed.")
