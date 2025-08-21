"""
Example run command:
python -m manual_coordinates.click IMG_0122.jpg

"""

import cv2
import numpy as np
from math import tan, radians, cos, pi
from scipy.spatial.transform import Rotation as R
from util.extract_gps import get_lat_lon_alt, get_exif_data
import csv
import os
import tkinter as tk
from tkinter import simpledialog
import argparse

output_csv = "./files/detections/clicked_coordinates.csv"

# Open CSV file for writing (append mode)
csv_file = open(output_csv, mode="a", newline="")
csv_writer = csv.writer(csv_file)

if os.stat(output_csv).st_size == 0:
    csv_writer.writerow(["ID", "Latitude", "Longitude", "Class"])

# === PARSE ARGUMENTS ===
parser = argparse.ArgumentParser(description="Click to get GPS coordinates from image.")
parser.add_argument('image_name', help="Image filename inside ./files/images/")
args = parser.parse_args()

# Fixed folder path
image_folder = "./files/images/"
image_path = os.path.join(image_folder, args.image_name)

# === SETTINGS ===
#altitude = 20.0
yaw_deg = 0.0
pitch_deg = 0.0
roll_deg = 0.0
hfov_deg = 78
EARTH_RADIUS = 6378137
HOME_ALTITUDE = 72.0  # Home altitude in meters
point_id = 1

# === Load original image ===
original_img = cv2.imread(image_path)
if original_img is None:
    raise FileNotFoundError("Could not load image.")
original_height, original_width = original_img.shape[:2]

# Resize for display
display_width = 1280
scale_factor = display_width / original_width
display_height = int(original_height * scale_factor)
display_img = cv2.resize(original_img, (display_width, display_height))

# === Extract GPS from EXIF ===
exif = get_exif_data(image_path)
if not exif:
    raise ValueError("No EXIF GPS data found.")
drone_lat, drone_lon, alt = start_lat, start_lon, alt = get_lat_lon_alt(exif)

def pixel_to_gps(x, y, image_width, image_height):
    hfov = radians(hfov_deg)
    vfov = hfov * (image_height / image_width)

    fx = image_width / (2 * tan(hfov / 2))
    fy = image_height / (2 * tan(vfov / 2))
    cx = image_width / 2
    cy = image_height / 2

    K = np.array([[fx, 0, cx],
                  [0, fy, cy],
                  [0,  0,  1]])
    K_inv = np.linalg.inv(K)

    pixel = np.array([x, y, 1.0])
    ray = K_inv @ pixel
    ray /= np.linalg.norm(ray)

    R_matrix = R.from_euler('ZYX', [radians(yaw_deg), radians(pitch_deg), radians(roll_deg)]).as_matrix()
    ray[0] = -ray[0]
    ray_world = R_matrix @ ray

    if ray_world[2] == 0:
        return drone_lat, drone_lon

    capture_alt = alt - HOME_ALTITUDE
    scale = -capture_alt / ray_world[2]
    ground_point = ray_world * scale

    offset_east = ground_point[0]
    offset_north = ground_point[1]

    dlat = offset_north / EARTH_RADIUS * (180 / pi)
    dlon = offset_east / (EARTH_RADIUS * cos(pi * drone_lat / 180)) * (180 / pi)

    return drone_lat + dlat, drone_lon + dlon

def on_click(event, x, y, flags, param):
    global point_id

    if event == cv2.EVENT_LBUTTONDOWN:
        orig_x = int(x / scale_factor)
        orig_y = int(y / scale_factor)
        lat, lon = pixel_to_gps(orig_x, orig_y, original_width, original_height)

        print(f"[ID {point_id}] Clicked at ({orig_x}, {orig_y}) => GPS: ({lat:.7f}, {lon:.7f})")

        # Create a simple input box to get the class name
        root = tk.Tk()
        root.withdraw()  # Hide the main Tkinter window
        class_name = simpledialog.askstring(title="Label Input", prompt="Enter class name:")
        root.destroy()

        if class_name is None or class_name.strip() == "":
            class_name = "Unknown"
        else:
            # Save to CSV
            csv_writer.writerow([point_id, lat, lon, class_name])
            csv_file.flush()
            point_id += 1


# === Open window and set mouse callback ===
cv2.namedWindow("Image", cv2.WINDOW_NORMAL)
cv2.imshow("Image", display_img)
cv2.setMouseCallback("Image", on_click)

print("Click on the resized image to get GPS coordinates. Press ESC to exit.")
while True:
    if cv2.waitKey(1) & 0xFF == 27:  # ESC
        break

cv2.destroyAllWindows()
csv_file.close()
