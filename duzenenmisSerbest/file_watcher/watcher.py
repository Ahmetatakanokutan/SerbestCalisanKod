# -*- coding: utf-8 -*- 

"""
This module continuously monitors a directory and processes newly added images
in a background thread.
"""

import os
import time
import glob
import queue
import csv
import cv2
import sys

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import WATCH_FOLDER, OUTPUT_CSV, HOME_ALTITUDE
from gps.exif import get_exif_data, get_lat_lon_alt
from gps.calculator import pixel_to_gps
from shape_detector.detector import SekilTespitEdici

# Global variables: a queue for jobs and a set to track processed files
job_queue = queue.Queue()
processed_files = set()

def image_processing_worker():
    """
    Picks up image paths from the queue, performs shape detection and GPS calculation,
    and writes the results to a CSV file. Designed to run in a daemon thread.
    """
    shape_detector = SekilTespitEdici()
    
    while True:
        image_path = job_queue.get()
        if image_path is None:  # Shutdown signal from the main thread
            break

        print(f"\n[PROCESSING] File: {os.path.basename(image_path)}")
        
        try:
            # 1. Read EXIF data and extract GPS info
            exif_data = get_exif_data(image_path)
            if not exif_data:
                print(f"[WARNING] Could not read EXIF data or format not supported: {os.path.basename(image_path)}")
                continue
            
            drone_lat, drone_lon, drone_alt = get_lat_lon_alt(exif_data)
            if drone_lat is None or drone_lon is None or drone_alt is None:
                print(f"[WARNING] GPS data is missing or could not be read: {os.path.basename(image_path)}")
                continue
            
            # Calculate altitude above ground level
            flight_altitude = drone_alt - HOME_ALTITUDE
            print(f"  -> GPS: ({drone_lat:.6f}, {drone_lon:.6f}), Altitude: {flight_altitude:.2f}m")

            # 2. Load the image
            image = cv2.imread(image_path)
            if image is None:
                print(f"[ERROR] Could not load image: {image_path}")
                continue
            
            image_height, image_width, _ = image.shape

            # 3. Detect red triangles and blue hexagons
            red_triangles = shape_detector.kirmizi_ucgenleri_bul(image)
            blue_hexagons = shape_detector.mavi_altigenleri_bul(image)
            all_detections = red_triangles + blue_hexagons
            
            if not all_detections:
                print("  -> No shapes were detected.")
                continue
            
            print(f"  -> Detections: {len(all_detections)} shapes")

            # 4. Write results to the CSV file
            with open(OUTPUT_CSV, "a", newline="", encoding='utf-8') as f:
                writer = csv.writer(f)
                for detection in all_detections:
                    center_x, center_y = detection['merkez']
                    
                    # Calculate GPS coordinate for the center pixel of the detected shape
                    latitude, longitude = pixel_to_gps(
                        center_x, center_y, image_width, image_height,
                        drone_lat, drone_lon, flight_altitude
                    )
                    
                    print(f"    -> {detection['renk'].upper()} {detection['sekil'].upper()} @ ({center_x},{center_y}) -> GPS: ({latitude:.7f}, {longitude:.7f})")
                    
                    # Create and write the CSV row
                    writer.writerow([
                        time.strftime("%Y-%m-%d %H:%M:%S"),
                        os.path.basename(image_path),
                        detection['sekil'],
                        detection['renk'],
                        f"{latitude:.7f}",
                        f"{longitude:.7f}"
                    ])
        
        except Exception as e:
            print(f"[CRITICAL ERROR] An unexpected error occurred while processing {os.path.basename(image_path)}: {e}")
        
        finally:
            # Mark the task in the queue as done
            job_queue.task_done()

def folder_watcher():
    """
    Periodically scans the specified directory for new images and adds them
    to the processing queue.
    """
    print(f"[STARTED] Watching folder: {os.path.abspath(WATCH_FOLDER)}")
    if not os.path.isdir(WATCH_FOLDER):
        print(f"[ERROR] Watch folder not found: {WATCH_FOLDER}")
        print("Please check the WATCH_FOLDER path in the 'config.py' file.")
        return

    while True:
        # Find all image files with supported formats
        image_files = glob.glob(os.path.join(WATCH_FOLDER, "*.jpg")) + \
                      glob.glob(os.path.join(WATCH_FOLDER, "*.jpeg")) + \
                      glob.glob(os.path.join(WATCH_FOLDER, "*.png"))
        
        # Find new images that have not been processed yet
        new_images = [f for f in image_files if f not in processed_files]

        if new_images:
            for image_path in sorted(new_images):
                print(f"[FOUND] Adding new image to queue: {os.path.basename(image_path)}")
                processed_files.add(image_path)
                job_queue.put(image_path)
            
        time.sleep(5) # Check the folder every 5 seconds