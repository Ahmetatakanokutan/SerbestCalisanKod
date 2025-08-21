from typing import List, Tuple, Any
import cv2
import math
import numpy as np  # Add numpy for center point calculation
from numpy import ndarray

Line = Tuple[int, int, int, int]  # (x1, y1, x2, y2)

ENDPOINT_PROXIMITY_THRESHOLD = 40
GAUSSIAN_BLUR = (5, 5)
CANNY_THRESHOLD1 = 25
CANNY_THRESHOLD2 = 200
TOLERANCE = 0.3
HOUGH_THRESHOLD = 80
MIN_LINE_LENGTH = 40
MAX_LINE_GAP = 10


def calculate_centroid(contour: List[Tuple[int, int]]):
    moments = cv2.moments(contour)
    if moments["m00"] != 0:
        cx = int(moments["m10"] / moments["m00"])
        cy = int(moments["m01"] / moments["m00"])
        return cx, cy
    return None


def line_intersection(line1, line2):
    x1, y1, x2, y2 = line1
    x3, y3, x4, y4 = line2
    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if denom == 0:
        return None  # Lines are parallel
    px = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / denom
    py = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / denom
    return (px, py)


def are_line_endpoints_close(line_a, line_b):
    x1, y1, x2, y2 = line_a
    x3, y3, x4, y4 = line_b
    dist1 = math.sqrt((x1 - x3) ** 2 + (y1 - y3) ** 2)
    dist2 = math.sqrt((x1 - x4) ** 2 + (y1 - y4) ** 2)
    dist3 = math.sqrt((x2 - x3) ** 2 + (y2 - y3) ** 2)
    dist4 = math.sqrt((x2 - x4) ** 2 + (y2 - y4) ** 2)
    return min(dist1, dist2, dist3, dist4) < ENDPOINT_PROXIMITY_THRESHOLD


def are_endpoints_close(lines: List[Line]):
    for i in range(len(lines)):
        for j in range(i + 1, len(lines)):
            if not are_line_endpoints_close(lines[i], lines[j]):
                return False
    return True


def side_length(point1, point2):
    return math.sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2)


class ImageProcessor:
    def __init__(self):
        self.detector = cv2.createBackgroundSubtractorMOG2()

    def process_frame(self, frame):
        frame = cv2.GaussianBlur(frame, (5, 5), 0)  # Apply Gaussian blur
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        mask = self.detector.apply(gray)
        contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            centroid = calculate_centroid(contour)
            if centroid:
                cv2.circle(frame, centroid, 5, (0, 255, 0), -1)
        return frame


class TriangleDetector(ImageProcessor):
    def __init__(self, min_line_length=40, max_line_gap=10):
        super().__init__()
        self.min_line_length = min_line_length
        self.max_line_gap = max_line_gap
        self.debug_frame = None

    def _preprocess_frame(self, frame):
        frame = cv2.resize(frame, (640, 480))
        frame = cv2.GaussianBlur(frame, GAUSSIAN_BLUR, 0)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)
        edges = cv2.Canny(gray, CANNY_THRESHOLD1, CANNY_THRESHOLD2)
        # self.debug_frame = edges.copy()
        # self.debug_frame = cv2.resize(edges, (256, 256))
        return edges

    def process_frame(self, frame, debug=True) -> Tuple[int, int] | None:
        # Resize and preprocess the frame
        # self.debug_frame = frame.copy()
        self.debug_frame = np.zeros_like(frame)
        edges = self._preprocess_frame(frame)
        center_point = None
        # Detect lines using Hough Line Transform
        lines: List[List[Line]] = cv2.HoughLinesP(
            edges,
            1,
            math.pi / 180,
            threshold=HOUGH_THRESHOLD,
            minLineLength=MIN_LINE_LENGTH,
            maxLineGap=MAX_LINE_GAP,
        )
        lines: ndarray[(Any, 1, 4), int] = np.array(lines)
        # self.debug_frame = frame.copy()
        if lines is not None:
            triangle_centroids = self._get_triangle_centroids(lines)
        # Calculate and return the center point of the point cloud using NumPy
        if len(triangle_centroids) > 0:
            center_point = np.mean(triangle_centroids, axis=0).astype(int)
            cv2.circle(self.debug_frame, center_point, 5, (0, 255, 0), -1)
        # Show the debug frame
        if debug:
            cv2.imshow("Debug Frame", self.debug_frame)
            cv2.waitKey(1)
        return center_point

    def _get_triangle_centroids(self, lines) -> ndarray[(Any, 2), int]:
        triangle_centroids = []
        # Analyze line intersections to find triangles
        for i in range(len(lines)):
            self.debug_frame = cv2.line(
                self.debug_frame,
                (lines[i][0][0], lines[i][0][1]),
                (lines[i][0][2], lines[i][0][3]),
                (128, 128, 128),
                2,
            )
            for j in range(i + 1, len(lines)):
                for k in range(j + 1, len(lines)):
                    # Extract line endpoints
                    line1, line2, line3 = lines[i][0], lines[j][0], lines[k][0]
                    # Check if the lines form a triangle
                    if not self._forms_triangle(line1, line2, line3):
                        continue
                    # Draw the triangle on the debug frame
                    self.debug_frame = cv2.line(
                        self.debug_frame,
                        (lines[i][0][0], lines[i][0][1]),
                        (lines[i][0][2], lines[i][0][3]),
                        (0, 0, 255),
                        5,
                    )
                    centroid = self._calculate_triangle_centroid(line1, line2, line3)
                    if centroid:
                        triangle_centroids.append(centroid)
        return np.array(triangle_centroids, dtype=float)

    def _forms_triangle(self, line1: Line, line2: Line, line3: Line) -> bool:
        # Find intersections of the three lines
        intersection1 = line_intersection(line1, line2)
        intersection2 = line_intersection(line2, line3)
        intersection3 = line_intersection(line3, line1)
        # Check if all three intersections exist and are distinct
        if intersection1 is None or intersection2 is None or intersection3 is None:
            return False
        if (
            intersection1 == intersection2
            or intersection2 == intersection3
            or intersection3 == intersection1
        ):
            return False
        # Check if line endpoints are close to each other
        if are_endpoints_close([line1, line2, line3]):
            # Check if the triangle has approximately equal sides
            side1 = side_length(intersection1, intersection2)
            side2 = side_length(intersection2, intersection3)
            side3 = side_length(intersection3, intersection1)
            max_side = max(side1, side2, side3)
            min_side = min(side1, side2, side3)
            if max_side - min_side < TOLERANCE * max_side:
                return True
            # print(f"Triangle sides are not equal: {side1}, {side2}, {side3}")
        return False

    def _calculate_triangle_centroid(self, line1, line2, line3) -> Tuple[int, int]:
        def line_midpoint(line):
            x1, y1, x2, y2 = line
            return (x1 + x2) // 2, (y1 + y2) // 2

        # Calculate midpoints of the three lines
        mid1 = line_midpoint(line1)
        mid2 = line_midpoint(line2)
        mid3 = line_midpoint(line3)

        # Calculate the centroid of the triangle
        cx = (mid1[0] + mid2[0] + mid3[0]) // 3
        cy = (mid1[1] + mid2[1] + mid3[1]) // 3
        return cx, cy


class HexagonDetector(TriangleDetector):
    # TODO: Implement hexagon detection
    def __init__(self, min_line_length=40, max_line_gap=10):
        super().__init__(min_line_length, max_line_gap)
        self.tolerance = 0.5

    def _forms_hexagon(
        self, line1: Line, line2: Line, line3: Line, line4: Line, line5: Line, line6: Line
    ) -> bool:
        # Find intersections of the three lines
        intersection1 = line_intersection(line1, line2)
        intersection2 = line_intersection(line2, line3)
        intersection3 = line_intersection(line3, line4)
        intersection4 = line_intersection(line4, line5)
        intersection5 = line_intersection(line5, line6)
        intersection6 = line_intersection(line6, line1)
        # Check if all three intersections exist and are distinct
        if (
            intersection1 is None
            or intersection2 is None
            or intersection3 is None
            or intersection4 is None
            or intersection5 is None
            or intersection6 is None
        ):
            return False
        if (
            intersection1 == intersection2
            or intersection2 == intersection3
            or intersection3 == intersection4
            or intersection4 == intersection5
            or intersection5 == intersection6
            or intersection6 == intersection1
        ):
            return False
        # Check if line endpoints are close to each other
        if are_endpoints_close([line1, line2, line3, line4, line5, line6]):
            # Check if the hexagon has approximately equal sides
            side1 = side_length(intersection1, intersection2)
            side2 = side_length(intersection2, intersection3)
            side3 = side_length(intersection3, intersection4)
            side4 = side_length(intersection4, intersection5)
            side5 = side_length(intersection5, intersection6)
            side6 = side_length(intersection6, intersection1)
            max_side = max(side1, side2, side3, side4, side5, side6)
            min_side = min(side1, side2, side3, side4, side5, side6)
            if max_side - min_side < TOLERANCE * max_side:
                return True
            # print(f"Hexagon sides are not equal: {side1}, {side2}, {side3}, {side4}, {side5}, {side6}")
        return False
