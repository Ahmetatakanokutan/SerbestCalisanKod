# -*- coding: utf-8 -*-

"""
Mathematical functions for converting pixel coordinates to GPS coordinates.
"""

import numpy as np
import cv2
from math import tan, radians, cos, pi

# Import necessary constants from the project config file
from config import (
    HFOV_DEGREES, PITCH_DEGREES, ROLL_DEGREES, YAW_DEGREES, EARTH_RADIUS
)

def pixel_to_gps(x, y, image_width, image_height, drone_latitude, drone_longitude, flight_altitude):
    """
    Converts a pixel coordinate within an image to a real-world GPS coordinate.
    
    Args:
        x (int): The x-coordinate of the pixel.
        y (int): The y-coordinate of the pixel.
        image_width (int): The total width of the image.
        image_height (int): The total height of the image.
        drone_latitude (float): The current latitude of the drone in decimal degrees.
        drone_longitude (float): The current longitude of the drone in decimal degrees.
        flight_altitude (float): The drone's altitude above ground level in meters.

    Returns:
        tuple: The calculated (latitude, longitude), or the original drone coordinates on error.
    """
    # Calculate camera intrinsic parameters
    hfov = radians(HFOV_DEGREES)
    vfov = hfov * (image_height / image_width)

    fx = image_width / (2 * tan(hfov / 2))
    fy = image_height / (2 * tan(vfov / 2))
    cx = image_width / 2
    cy = image_height / 2

    # Inverse of the intrinsic parameter matrix (K_inv)
    K_inv = np.linalg.inv(np.array([[fx, 0, cx], [0, fy, cy], [0, 0, 1]]))
    
    # Convert 2D pixel point to a 3D ray
    pixel_vector = np.array([x, y, 1.0])
    ray_in_camera_coords = K_inv @ pixel_vector
    ray_in_camera_coords /= np.linalg.norm(ray_in_camera_coords)

    # Extrinsic parameters: Drone's orientation (Euler angles)
    R_matrix = cv2.Rodrigues(np.array([radians(PITCH_DEGREES), radians(ROLL_DEGREES), radians(YAW_DEGREES)]))[0]
    
    # Convert the ray from camera coordinate system to world coordinate system
    ray_in_world_coords = R_matrix @ ray_in_camera_coords
    
    # Assuming Z-axis points down towards the ground.
    # If the ray points up or is parallel to the ground, there's no intersection.
    if ray_in_world_coords[2] <= 1e-6:
        return drone_latitude, drone_longitude

    # Calculate the intersection of the ray with the ground plane
    scale = flight_altitude / ray_in_world_coords[2]
    ground_point = ray_in_world_coords * scale

    # Calculate offsets in the world coordinate system (north and east)
    offset_north = ground_point[1]
    offset_east = ground_point[0]

    # Convert offsets to latitude and longitude differences
    dlat = offset_north / EARTH_RADIUS * (180 / pi)
    dlon = offset_east / (EARTH_RADIUS * cos(radians(drone_latitude))) * (180 / pi)

    # Calculate the new GPS coordinates
    new_latitude = drone_latitude + dlat
    new_longitude = drone_longitude + dlon

    return new_latitude, new_longitude