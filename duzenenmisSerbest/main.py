# -*- coding: utf-8 -*- 

"""
Red Triangle and Blue Hexagon Detection System - Main Starter

This script is the main entry point that starts the entire system.
It can run in two different modes:
1. 'folder': Monitors a specified directory for new images,
             reads their GPS data, and saves the results to a CSV file.
2. 'webcam': Captures a live video stream from the default camera,
             detects shapes, and displays the results in real-time.

Usage Examples:
# To run in folder monitoring mode:
python main.py --mod folder

# To run in live webcam mode (default camera 0):
python main.py --mod webcam

# To select a specific camera (e.g., /dev/video19):
python main.py --mod webcam --camera_index 19
"""

import os
import sys
import threading
import csv
import argparse

# Add the project root directory to Python's import path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import CIKTI_CSV, IZLENECEK_KLASOR
from file_watcher.watcher import resim_isleyici_worker, klasor_izleyici, is_kuyrugu
from video_processor import start_video_stream

def prepare_system():
    """
    Prepares the necessary directories and the output CSV file for the program.
    This is especially required for 'folder' mode.
    """
    # Create the directory for the output CSV file
    os.makedirs(os.path.dirname(CIKTI_CSV), exist_ok=True)
    
    # Create the image watch folder
    os.makedirs(IZLENECEK_KLASOR, exist_ok=True)

    # If the CSV file is empty or doesn't exist, write the header row
    if not os.path.exists(CIKTI_CSV) or os.stat(CIKTI_CSV).st_size == 0:
        with open(CIKTI_CSV, "w", newline="", encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "filename", "type", "color", "latitude", "longitude"])
        print(f"[INFO] Output file created with header: {CIKTI_CSV}")

def main():
    """
    Main function: Parses command-line arguments and starts the appropriate processors.
    """
    # Define command-line arguments
    parser = argparse.ArgumentParser(
        description="Red Triangle and Blue Hexagon Detection System."
    )
    parser.add_argument(
        '--mod',
        type=str,
        choices=['folder', 'webcam'],
        required=True,
        help="Choose the operating mode: 'folder' (watch a directory) or 'webcam' (live video)."
    )
    parser.add_argument(
        '--camera_index',
        type=int,
        default=0,
        help="The camera index to be used for webcam mode (e.g., 0, 1, 19)."
    )
    args = parser.parse_args()

    print("="*50)
    print(f"Starting System in '{args.mod.upper()}' Mode...")
    print("="*50)
    
    if args.mod == 'folder':
        # FOLDER WATCHER MODE
        prepare_system()
        
        worker_thread = threading.Thread(target=resim_isleyici_worker, daemon=True)
        worker_thread.start()
        print("[INFO] Background image processor (worker) started.")

        try:
            klasor_izleyici()
        except KeyboardInterrupt:
            print("\n[STOPPING] User interruption detected...")
            is_kuyrugu.put(None)
            worker_thread.join(timeout=5)
            print("[SHUTDOWN] Program terminated successfully.")
        
    elif args.mod == 'webcam':
        # LIVE VIDEO MODE
        print(f"[INFO] Using camera index {args.camera_index}.")
        try:
            # Start the video stream with the selected camera index
            start_video_stream(source=args.camera_index)
        except KeyboardInterrupt:
            print("\n[STOPPING] User interruption detected...")
            print("[SHUTDOWN] Program terminated successfully.")

    print("="*50)

if __name__ == "__main__":
    main()
