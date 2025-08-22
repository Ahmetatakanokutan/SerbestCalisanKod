
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
    TRIANGLE_EPSILON_FACTOR, HEXAGON_EPSILON_FACTOR,
    MIN_SOLIDITY, MIN_ASPECT_RATIO, MAX_ASPECT_RATIO
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
        hsv = cv2.cvtColor(image, cv.COLOR_BGR2HSV)
        
        if color == 'kirmizi':
            mask1 = cv.inRange(hsv, RED_LOWER_1, RED_UPPER_1)
            mask2 = cv.inRange(hsv, RED_LOWER_2, RED_UPPER_2)
            mask = cv.bitwise_or(mask1, mask2)
        elif color == 'mavi':
            mask = cv.inRange(hsv, BLUE_LOWER, BLUE_UPPER)
        else:
            return np.zeros(image.shape[:2], dtype="uint8")
        
        mask = cv.morphologyEx(mask, cv.MORPH_OPEN, MORPHOLOGICAL_KERNEL)
        mask = cv.morphologyEx(mask, cv.MORPH_CLOSE, MORPHOLOGICAL_KERNEL)
        return mask

    def _is_contour_valid(self, contour):
        """
        Checks if a contour is a valid shape based on solidity and aspect ratio.
        """
        # Solidity check
        area = cv.contourArea(contour)
        hull = cv.convexHull(contour)
        if hull is None or cv.contourArea(hull) == 0:
            return False
        solidity = float(area) / cv.contourArea(hull)
        if solidity < MIN_SOLIDITY:
            return False

        # Aspect ratio check
        x, y, w, h = cv.boundingRect(contour)
        if h == 0: return False
        aspect_ratio = float(w) / h
        if not (MIN_ASPECT_RATIO <= aspect_ratio <= MAX_ASPECT_RATIO):
            return False
            
        return True

    def kirmizi_ucgenleri_bul(self, image):
        """
        Detects red triangles in a given image.
        """
        mask = self._create_color_mask(image, 'kirmizi')
        contours, _ = cv.findContours(mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        
        detected_triangles = []
        for contour in contours:
            if cv.contourArea(contour) < MIN_TRIANGLE_AREA:
                continue
            
            if not self._is_contour_valid(contour):
                continue

            epsilon = TRIANGLE_EPSILON_FACTOR * cv.arcLength(contour, True)
            approx_contour = cv.approxPolyDP(contour, epsilon, True)

            if len(approx_contour) == 3 and cv.isContourConvex(approx_contour):
                M = cv.moments(contour)
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
        contours, _ = cv.findContours(mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        
        detected_hexagons = []
        for contour in contours:
            if cv.contourArea(contour) < MIN_HEXAGON_AREA:
                continue

            if not self._is_contour_valid(contour):
                continue

            epsilon = HEXAGON_EPSILON_FACTOR * cv.arcLength(contour, True)
            approx_contour = cv.approxPolyDP(contour, epsilon, True)

            if len(approx_contour) == 6 and cv.isContourConvex(approx_contour):
                M = cv.moments(contour)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    detected_hexagons.append({
                        'sekil': 'altigen', 
                        'renk': 'mavi', 
                        'merkez': (cx, cy)
                    })

        return detected_hexagons
