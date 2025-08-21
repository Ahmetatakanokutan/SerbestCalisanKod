
import math
import numpy as np
from math import tan, radians, cos, pi
from scipy.spatial.transform import Rotation as R
from typing import List, Tuple

# =============================================================================
# --- CONSTANTS ---
# =============================================================================
EARTH_RADIUS = 6378137
ENDPOINT_PROXIMITY_THRESHOLD = 40
Line = Tuple[int, int, int, int]

# =============================================================================
# --- GPS CALCULATION ---
# =============================================================================

def pixel_to_gps(x, y, image_width, image_height, drone_lat, drone_lon, drone_alt,
                 yaw_deg, pitch_deg, roll_deg, hfov_deg):
    """
    Calculates the GPS coordinates of a pixel in an image based on drone telemetry.
    """
    hfov = radians(hfov_deg)
    vfov = hfov * (image_height / image_width)

    # Camera intrinsic matrix parameters
    fx = image_width / (2 * tan(hfov / 2))
    fy = image_height / (2 * tan(vfov / 2))
    cx = image_width / 2
    cy = image_height / 2

    K = np.array([[fx, 0, cx], [0, fy, cy], [0, 0, 1]])
    K_inv = np.linalg.inv(K)

    # Ray in camera coordinates
    pixel = np.array([x, y, 1.0])
    ray_cam = K_inv @ pixel
    ray_cam /= np.linalg.norm(ray_cam)

    # Rotation from camera to world frame
    R_matrix = R.from_euler('ZYX', [radians(yaw_deg), radians(pitch_deg), radians(roll_deg)]).as_matrix()
    
    # Transform ray to world coordinates
    ray_world = R_matrix @ ray_cam

    # Check if the ray intersects the ground plane (Z is down)
    if ray_world[2] >= 0:
        return None

    # Calculate intersection point with the ground
    scale = -drone_alt / ray_world[2]
    ground_point = ray_world * scale

    offset_east = ground_point[0]
    offset_north = ground_point[1]

    # Convert offsets to latitude and longitude difference
    dlat = offset_north / EARTH_RADIUS * (180 / pi)
    dlon = offset_east / (EARTH_RADIUS * cos(pi * drone_lat / 180)) * (180 / pi)

    return drone_lat + dlat, drone_lon + dlon

# =============================================================================
# --- GEOMETRIC HELPERS ---
# =============================================================================

def line_intersection(line1: Line, line2: Line) -> Tuple[float, float] | None:
    """Calculates the intersection point of two lines."""
    x1, y1, x2, y2 = line1
    x3, y3, x4, y4 = line2
    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if denom == 0:
        return None  # Parallel lines
    px = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / denom
    py = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / denom
    return (px, py)

def are_line_endpoints_close(line_a: Line, line_b: Line) -> bool:
    """Checks if the endpoints of two lines are close to each other."""
    x1, y1, x2, y2 = line_a
    x3, y3, x4, y4 = line_b
    dist = min(
        math.hypot(x1 - x3, y1 - y3),
        math.hypot(x1 - x4, y1 - y4),
        math.hypot(x2 - x3, y2 - y3),
        math.hypot(x2 - x4, y2 - y4),
    )
    return dist < ENDPOINT_PROXIMITY_THRESHOLD

def are_endpoints_close(lines: List[Line]) -> bool:
    """Checks if endpoints are close for a list of lines."""
    from itertools import combinations
    for line1, line2 in combinations(lines, 2):
        if not are_line_endpoints_close(line1, line2):
            return False
    return True

def side_length(point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
    """Calculates the distance between two points."""
    return math.hypot(point1[0] - point2[0], point1[1] - point2[1])
