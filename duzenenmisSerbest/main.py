# -*- coding: utf-8 -*- 

"""
Red Triangle and Blue Hexagon Detection System - Main Starter

This script is the main entry point that starts the entire system.
It can run in two different modes:
1. 'folder': Monitors a specified directory for new images,
             reads their GPS data, and saves the results to a CSV file.
2. 'webcam': Captures a live video stream from a local camera or an RTSP network stream,
             detects shapes, and displays the results in real-time.

Usage Examples:
# To run in folder monitoring mode:
python main.py --mod folder

# To run with a local camera (e.g., /dev/video0):
python main.py --mod webcam --camera_index 0

# To run with an RTSP network stream:
python main.py --mod webcam --rtsp_url "rtsp://192.168.144.25:8554/main.264"
"""

import os
import sys
import threading
import csv
import argparse

# Add the project root directory to Python's import path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import OUTPUT_CSV, WATCH_FOLDER
from file_watcher.watcher import image_processing_worker, folder_watcher, job_queue
from video_processor import start_video_stream

def prepare_system():
    """
    Prepares the necessary directories and the output CSV file for the program.
    This is especially required for 'folder' mode.
    """
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    os.makedirs(WATCH_FOLDER, exist_ok=True)

    if not os.path.exists(OUTPUT_CSV) or os.stat(OUTPUT_CSV).st_size == 0:
        with open(OUTPUT_CSV, "w", newline="", encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "filename", "type", "color", "latitude", "longitude"])
        print(f"[INFO] Output file created with header: {OUTPUT_CSV}")

def create_gstreamer_pipeline(camera_index=0, width=1280, height=720, framerate=30):
    """
    Creates a GStreamer pipeline string for capturing video from a V4L2 device.
    """
    return (
        f"v4l2src device=/dev/video{camera_index} ! "
        f"video/x-raw, width={width}, height={height}, framerate={framerate}/1 ! "
        "videoconvert ! "
        "video/x-raw, format=BGR ! "
        "appsink"
    )

def create_rtsp_pipeline(url):
    """
    Creates a GStreamer pipeline string for capturing video from an RTSP stream.
    This is based on the user-provided working pipeline.
    """
    return (
        f"rtspsrc location={url} latency=41 udp-reconnect=1 timeout=0 do-retransmission=false ! "
        f"application/x-rtp ! "
        f"decodebin3 ! "
        f"queue max-size-buffers=1 leaky=2 ! "
        f"videoconvert ! "
        f"video/x-raw,format=BGR ! "
        f"appsink sync=false"
    )

def main():
    """
    Main function: Parses command-line arguments and starts the appropriate processors.
    """
    parser = argparse.ArgumentParser(
        description="Red Triangle and Blue Hexagon Detection System."
    )
    parser.add_argument(
        '--mod',
        type=str,
        choices=['folder', 'webcam'],
        required=True,
        help="Choose the operating mode: 'folder' or 'webcam'."
    )
    parser.add_argument(
        '--camera_index',
        type=int,
        default=0,
        help="The camera index for local webcam mode (e.g., 0, 19)."
    )
    parser.add_argument(
        '--rtsp_url',
        type=str,
        default=None,
        help="URL of the RTSP stream to use instead of a local camera."
    )
    args = parser.parse_args()

    print("="*50)
    print(f"Starting System in '{args.mod.upper()}' Mode...")
    print("="*50)
    
    if args.mod == 'folder':
        prepare_system()
        worker_thread = threading.Thread(target=image_processing_worker, daemon=True)
        worker_thread.start()
        print("[INFO] Background image processor (worker) started.")
        try:
            folder_watcher()
        except KeyboardInterrupt:
            print("\n[STOPPING] User interruption detected...")
            job_queue.put(None)
            worker_thread.join(timeout=5)
            print("[SHUTDOWN] Program terminated successfully.")
        
    elif args.mod == 'webcam':
        pipeline = None
        if args.rtsp_url:
            print(f"[INFO] Using RTSP stream: {args.rtsp_url}")
            pipeline = create_rtsp_pipeline(args.rtsp_url)
        else:
            print(f"[INFO] Using local camera index: {args.camera_index}")
            pipeline = create_gstreamer_pipeline(camera_index=args.camera_index)
        
        try:
            start_video_stream(pipeline=pipeline)
        except KeyboardInterrupt:
            print("\n[STOPPING] User interruption detected...")
            print("[SHUTDOWN] Program terminated successfully.")

    print("="*50)

if __name__ == "__main__":
    main()
