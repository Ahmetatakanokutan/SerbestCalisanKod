
# -*- coding: utf-8 -*-

"""
This module contains classes for performing color-based shape detection in images.
- It finds red triangles and blue hexagons.
"""

import cv2
import numpy as np
import sys
import os

# Add the config.py directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the new English variable names from the config file
from config import (
    RED_LOWER_1, RED_UPPER_1, RED_LOWER_2, RED_UPPER_2,
    BLUE_LOWER, BLUE_UPPER, MORPHOLOGICAL_KERNEL,
    MIN_TRIANGLE_AREA, MIN_HEXAGON_AREA,
    TRIANGLE_EPSILON_FACTOR, HEXAGON_EPSILON_FACTOR
)

class SekilTespitEdici:
    """
    Main class containing methods for detecting geometric shapes of specific colors.
    """

    def _create_color_mask(self, image, color):
        """
        Creates a binary mask for the specified color in the HSV space and
        cleans up noise using morphological operations.
        """
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        if color == 'kirmizi':
            mask1 = cv2.inRange(hsv, RED_LOWER_1, RED_UPPER_1)
            mask2 = cv2.inRange(hsv, RED_LOWER_2, RED_UPPER_2)
            mask = cv2.bitwise_or(mask1, mask2)
        elif color == 'mavi':
            mask = cv2.inRange(hsv, BLUE_LOWER, BLUE_UPPER)
        else:
            return np.zeros(image.shape[:2], dtype="uint8")
        
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, MORPHOLOGICAL_KERNEL)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, MORPHOLOGICAL_KERNEL)
        return mask

    def kirmizi_ucgenleri_bul(self, image):
        """
        Detects red triangles in a given image.
        """
        mask = self._create_color_mask(image, 'kirmizi')
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        detected_triangles = []
        for contour in contours:
            if cv2.contourArea(contour) < MIN_TRIANGLE_AREA:
                continue
            
            epsilon = TRIANGLE_EPSILON_FACTOR * cv2.arcLength(contour, True)
            approx_contour = cv2.approxPolyDP(contour, epsilon, True)

            if len(approx_contour) == 3:
                M = cv2.moments(contour)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    detected_triangles.append({
                        'sekil': 'ucgen', 
                        'renk': 'kirmizi', 
                        'merkez': (cx, cy)
                    })
        
        return detected_triangles

    def mavi_altigenleri_bul(self, image):
        """
        Detects blue hexagons in a given image.
        """
        mask = self._create_color_mask(image, 'mavi')
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        detected_hexagons = []
        for contour in contours:
            if cv2.contourArea(contour) < MIN_HEXAGON_AREA:
                continue

            epsilon = HEXAGON_EPSILON_FACTOR * cv2.arcLength(contour, True)
            approx_contour = cv2.approxPolyDP(contour, epsilon, True)

            if len(approx_contour) == 6:
                M = cv2.moments(contour)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    detected_hexagons.append({
                        'sekil': 'altigen', 
                        'renk': 'mavi', 
                        'merkez': (cx, cy)
                    })

        return detected_hexagons
