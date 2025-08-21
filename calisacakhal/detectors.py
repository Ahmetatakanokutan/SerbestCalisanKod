
import cv2
import numpy as np
import math
from typing import List, Tuple
from itertools import combinations

# Import helper functions from the utils module
from .utils import line_intersection, are_endpoints_close, side_length, Line

# =============================================================================
# --- CONSTANTS ---
# =============================================================================

# --- Shape Detection Parameters ---
GAUSSIAN_BLUR = (5, 5)
CANNY_THRESHOLD1 = 50
CANNY_THRESHOLD2 = 150
HOUGH_THRESHOLD = 50
MIN_LINE_LENGTH = 30
MAX_LINE_GAP = 10
TRIANGLE_TOLERANCE = 0.4  # Increased tolerance for real-world conditions
HEXAGON_TOLERANCE = 0.5

# --- Color Detection Parameters (HSV) ---
RED_LOWER1 = np.array([0, 120, 70])
RED_UPPER1 = np.array([10, 255, 255])
RED_LOWER2 = np.array([170, 120, 70])
RED_UPPER2 = np.array([180, 255, 255])
BLUE_LOWER = np.array([90, 80, 50])
BLUE_UPPER = np.array([130, 255, 255])

# =============================================================================
# --- BASE DETECTOR CLASS ---
# =============================================================================

class ShapeDetector:
    """Base class for different shape detectors."""
    def __init__(self, min_line_length=MIN_LINE_LENGTH, max_line_gap=MAX_LINE_GAP):
        self.min_line_length = min_line_length
        self.max_line_gap = max_line_gap

    def _preprocess_frame(self, frame, color: str):
        """Applies color filtering and edge detection."""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        if color == 'red':
            mask1 = cv2.inRange(hsv, RED_LOWER1, RED_UPPER1)
            mask2 = cv2.inRange(hsv, RED_LOWER2, RED_UPPER2)
            mask = cv2.bitwise_or(mask1, mask2)
        elif color == 'blue':
            mask = cv2.inRange(hsv, BLUE_LOWER, BLUE_UPPER)
        else:
            raise ValueError("Unsupported color specified. Use 'red' or 'blue'.")

        # Improve mask quality
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        edges = cv2.Canny(mask, CANNY_THRESHOLD1, CANNY_THRESHOLD2)
        return edges

    def process_frame(self, frame, color: str) -> List[Tuple[int, int]]:
        """This method must be implemented by subclasses."""
        raise NotImplementedError

# =============================================================================
# --- TRIANGLE DETECTOR ---
# =============================================================================

class TriangleDetector(ShapeDetector):
    """Detects triangles of a specific color."""
    def process_frame(self, frame, color: str) -> List[Tuple[int, int]]:
        edges = self._preprocess_frame(frame, color)
        lines = cv2.HoughLinesP(
            edges, 1, np.pi / 180,
            threshold=HOUGH_THRESHOLD,
            minLineLength=self.min_line_length,
            maxLineGap=self.max_line_gap,
        )

        centroids = []
        if lines is not None:
            for line_combo in combinations(lines, 3):
                line_list = [l[0] for l in line_combo]
                if self._forms_triangle(line_list):
                    centroid = self._calculate_triangle_centroid(line_list)
                    if centroid:
                        centroids.append(centroid)
        return centroids

    def _forms_triangle(self, lines: List[Line]) -> bool:
        """Validates if three lines form a plausible triangle."""
        if not are_endpoints_close(lines):
            return False
        
        p1 = line_intersection(lines[0], lines[1])
        p2 = line_intersection(lines[1], lines[2])
        p3 = line_intersection(lines[2], lines[0])
        
        if not all([p1, p2, p3]):
            return False

        side1, side2, side3 = side_length(p1, p2), side_length(p2, p3), side_length(p3, p1)
        if any(s == 0 for s in [side1, side2, side3]): return False
        
        max_side, min_side = max(side1, side2, side3), min(side1, side2, side3)
        if (max_side - min_side) < TRIANGLE_TOLERANCE * max_side:
            return True
        return False

    def _calculate_triangle_centroid(self, lines: List[Line]) -> Tuple[int, int] | None:
        """Calculates the centroid of the triangle's vertices."""
        p1 = line_intersection(lines[0], lines[1])
        p2 = line_intersection(lines[1], lines[2])
        p3 = line_intersection(lines[2], lines[0])
        
        if not all([p1, p2, p3]): return None
        
        cx = int((p1[0] + p2[0] + p3[0]) / 3)
        cy = int((p1[1] + p2[1] + p3[1]) / 3)
        return cx, cy

# =============================================================================
# --- HEXAGON DETECTOR ---
# =============================================================================

class HexagonDetector(ShapeDetector):
    """Detects hexagons of a specific color."""
    def process_frame(self, frame, color: str) -> List[Tuple[int, int]]:
        edges = self._preprocess_frame(frame, color)
        lines = cv2.HoughLinesP(
            edges, 1, np.pi / 180,
            threshold=HOUGH_THRESHOLD,
            minLineLength=self.min_line_length,
            maxLineGap=self.max_line_gap,
        )

        centroids = []
        if lines is not None and len(lines) >= 6:
            for line_combo in combinations(lines, 6):
                line_list = [l[0] for l in line_combo]
                if self._forms_hexagon(line_list):
                    centroid = self._calculate_hexagon_centroid(line_list)
                    if centroid:
                        centroids.append(centroid)
        return centroids

    def _forms_hexagon(self, lines: List[Line]) -> bool:
        """Validates if six lines form a plausible hexagon."""
        if not are_endpoints_close(lines):
            return False
            
        # This is a simplified check. A robust check would involve ordering
        # the lines and checking angles, which is computationally expensive.
        # We rely on endpoint proximity and side length similarity.
        intersections = []
        for i in range(6):
            p = line_intersection(lines[i], lines[(i + 1) % 6])
            if p is None: return False
            intersections.append(p)
            
        sides = [side_length(intersections[i], intersections[(i + 1) % 6]) for i in range(6)]
        if any(s < 10 for s in sides): return False # Avoid degenerate shapes
        
        max_side, min_side = max(sides), min(sides)
        if (max_side - min_side) < HEXAGON_TOLERANCE * max_side:
            return True
        return False

    def _calculate_hexagon_centroid(self, lines: List[Line]) -> Tuple[int, int] | None:
        """Calculates the centroid of the hexagon's vertices."""
        # A simple average of line midpoints can be a stable approximation
        midpoints = [((l[0] + l[2]) / 2, (l[1] + l[3]) / 2) for l in lines]
        cx = int(sum(p[0] for p in midpoints) / 6)
        cy = int(sum(p[1] for p in midpoints) / 6)
        return cx, cy
