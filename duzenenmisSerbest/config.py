# -*- coding: utf-8 -*-

"""
All configuration parameters and constants for the project are located in this file.
"""

import numpy as np
import os

# ==== FILE PATHS ====
# Dynamically create paths based on the main project directory
CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(CONFIG_DIR)

WATCH_FOLDER = os.path.join(BASE_DIR, "files", "images")
OUTPUT_CSV = os.path.join(BASE_DIR, "files", "detections", "detections.csv")


# ==== CAMERA AND GPS PARAMETERS ====
HFOV_DEGREES = 78.0      # Horizontal Field of View
HOME_ALTITUDE = 72.0     # Altitude of the drone's home point in meters
YAW_DEGREES = 0.0
PITCH_DEGREES = 0.0
ROLL_DEGREES = 0.0
EARTH_RADIUS = 6378137   # In meters

# ==== COLOR DETECTION PARAMETERS (HSV COLOR SPACE) ====
# Two ranges for red (as it wraps around in HSV) - More restrictive
RED_LOWER_1 = np.array([0, 150, 100])
RED_UPPER_1 = np.array([8, 255, 255])
RED_LOWER_2 = np.array([172, 150, 100])
RED_UPPER_2 = np.array([180, 255, 255])

# Range for blue - More restrictive
BLUE_LOWER = np.array([100, 180, 80])
BLUE_UPPER = np.array([128, 255, 255])

# ==== IMAGE PROCESSING PARAMETERS ====
# Contour area thresholds for shape detection
MIN_TRIANGLE_AREA = 120
MIN_HEXAGON_AREA = 180

# Epsilon factors for contour approximation
TRIANGLE_EPSILON_FACTOR = 0.04
HEXAGON_EPSILON_FACTOR = 0.03

# Kernel size for morphological operations
MORPHOLOGICAL_KERNEL = np.ones((5, 5), np.uint8)

# ==== SHAPE VALIDATION PARAMETERS ====
# Minimum solidity (ratio of contour area to its convex hull area)
MIN_SOLIDITY = 0.90

# Aspect ratio range for the bounding box of the shape
MIN_ASPECT_RATIO = 0.75
MAX_ASPECT_RATIO = 1.25
