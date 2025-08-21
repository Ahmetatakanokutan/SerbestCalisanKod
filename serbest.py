"""
Kırmızı Üçgen ve Mavi Altıgen Tespit Sistemi
GPS koordinatlı görüntülerde kırmızı üçgen ve mavi altıgen tespit eder
ve bunların gerçek dünya GPS koordinatlarını hesaplar.
"""

import cv2
import numpy as np
import os
import time
import csv
import threading
import queue
import glob
import math
import argparse
from math import tan, radians, cos, pi, sin
from scipy.spatial.transform import Rotation as R
from typing import List, Tuple, Any, Optional
from numpy import ndarray

# ==== KONFIGÜRASYON ====
WATCH_FOLDER = "./files/images"
OUTPUT_CSV = "./files/detections/shape_detections.csv"
OUTPUT_DIR = "./files/output_tiles"

# GPS ve Kamera Parametreleri
HFOV_DEG = 78
HOME_ALTITUDE = 72.0
YAW_DEG = 0.0
PITCH_DEG = 0.0
ROLL_DEG = 0.0
EARTH_RADIUS = 6378137

# Şekil Tespit Parametreleri
ENDPOINT_PROXIMITY_THRESHOLD = 40
GAUSSIAN_BLUR = (5, 5)
CANNY_THRESHOLD1 = 25
CANNY_THRESHOLD2 = 200
TOLERANCE = 0.3
HOUGH_THRESHOLD = 80
MIN_LINE_LENGTH = 40
MAX_LINE_GAP = 10

# Renk Tespit Parametreleri (HSV)
# Kırmızı renk için iki aralık (HSV'de kırmızı 0 ve 180 civarında)
RED_LOWER1 = np.array([0, 50, 50])
RED_UPPER1 = np.array([10, 255, 255])
RED_LOWER2 = np.array([170, 50, 50])
RED_UPPER2 = np.array([180, 255, 255])

# Mavi renk için aralık
BLUE_LOWER = np.array([100, 50, 50])
BLUE_UPPER = np.array([130, 255, 255])

# ==== YARDIMCI FONKSİYONLAR ====

def get_exif_data(image_path):
    """Placeholder for EXIF data extraction"""
    # Gerçek uygulamada util.extract_gps modülünden alınacak
    # Şimdilik örnek veri döndürüyoruz
    return {
        'lat': 41.0082,
        'lon': 28.9784,
        'alt': 150.0
    }

def get_lat_lon_alt(exif):
    """EXIF verisinden GPS bilgilerini çıkar"""
    return exif['lat'], exif['lon'], exif['alt']

def pixel_to_gps(x, y, image_width, image_height, drone_lat, drone_lon, capture_alt):
    """Piksel koordinatlarını GPS koordinatlarına çevirir"""
    hfov = radians(HFOV_DEG)
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

    R_matrix = R.from_euler('ZYX', [radians(YAW_DEG), radians(PITCH_DEG), radians(ROLL_DEG)]).as_matrix()
    ray[0] = -ray[0]
    ray_world = R_matrix @ ray

    if ray_world[2] == 0:
        return drone_lat, drone_lon

    scale = -capture_alt / ray_world[2]
    ground_point = ray_world * scale

    offset_east = ground_point[0]
    offset_north = ground_point[1]

    dlat = offset_north / EARTH_RADIUS * (180 / pi)
    dlon = offset_east / (EARTH_RADIUS * cos(pi * drone_lat / 180)) * (180 / pi)

    return drone_lat + dlat, drone_lon + dlon

def line_intersection(line1, line2):
    """İki çizginin kesişim noktasını bulur"""
    x1, y1, x2, y2 = line1
    x3, y3, x4, y4 = line2
    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if denom == 0:
        return None
    px = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / denom
    py = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / denom
    return (px, py)

def side_length(point1, point2):
    """İki nokta arasındaki mesafeyi hesaplar"""
    return math.sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2)

def are_line_endpoints_close(line_a, line_b):
    """İki çizginin uç noktalarının yakın olup olmadığını kontrol eder"""
    x1, y1, x2, y2 = line_a
    x3, y3, x4, y4 = line_b
    dist1 = math.sqrt((x1 - x3) ** 2 + (y1 - y3) ** 2)
    dist2 = math.sqrt((x1 - x4) ** 2 + (y1 - y4) ** 2)
    dist3 = math.sqrt((x2 - x3) ** 2 + (y2 - y3) ** 2)
    dist4 = math.sqrt((x2 - x4) ** 2 + (y2 - y4) ** 2)
    return min(dist1, dist2, dist3, dist4) < ENDPOINT_PROXIMITY_THRESHOLD

# ==== RENK TESPİT SINIFI ====

class ColorDetector:
    """Renk tespiti için yardımcı sınıf"""
    
    @staticmethod
    def detect_red_regions(image):
        """Görüntüdeki kırmızı bölgeleri tespit eder"""
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Kırmızı için iki maske (HSV'de kırmızı 0 ve 180 civarında)
        mask1 = cv2.inRange(hsv, RED_LOWER1, RED_UPPER1)
        mask2 = cv2.inRange(hsv, RED_LOWER2, RED_UPPER2)
        mask = cv2.bitwise_or(mask1, mask2)
        
        # Gürültüyü azalt
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        
        return mask
    
    @staticmethod
    def detect_blue_regions(image):
        """Görüntüdeki mavi bölgeleri tespit eder"""
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        mask = cv2.inRange(hsv, BLUE_LOWER, BLUE_UPPER)
        
        # Gürültüyü azalt
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        
        return mask

# ==== ŞEKİL TESPİT SINIFLARI ====

class ShapeDetector:
    """Temel şekil tespit sınıfı"""
    
    def __init__(self):
        self.debug_frame = None
        
    def _preprocess_frame(self, frame):
        """Görüntüyü ön işlemeden geçirir"""
        frame = cv2.GaussianBlur(frame, GAUSSIAN_BLUR, 0)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)
        edges = cv2.Canny(gray, CANNY_THRESHOLD1, CANNY_THRESHOLD2)
        return edges

class TriangleDetector(ShapeDetector):
    """Üçgen tespit sınıfı"""
    
    def detect_triangles(self, image, color_mask=None):
        """Görüntüde üçgenleri tespit eder"""
        triangles = []
        
        # Renk maskesi varsa uygula
        if color_mask is not None:
            # Maskelenmiş bölgelerde kenar tespiti yap
            masked_image = cv2.bitwise_and(image, image, mask=color_mask)
            edges = self._preprocess_frame(masked_image)
        else:
            edges = self._preprocess_frame(image)
        
        # Hough çizgi tespiti
        lines = cv2.HoughLinesP(
            edges, 1, math.pi / 180,
            threshold=HOUGH_THRESHOLD,
            minLineLength=MIN_LINE_LENGTH,
            maxLineGap=MAX_LINE_GAP
        )
        
        if lines is None:
            return triangles
        
        # Üçgen kombinasyonlarını kontrol et
        for i in range(len(lines)):
            for j in range(i + 1, len(lines)):
                for k in range(j + 1, len(lines)):
                    line1, line2, line3 = lines[i][0], lines[j][0], lines[k][0]
                    
                    if self._forms_triangle(line1, line2, line3):
                        centroid = self._calculate_triangle_centroid(line1, line2, line3)
                        if centroid:
                            triangles.append({
                                'type': 'triangle',
                                'centroid': centroid,
                                'lines': [line1, line2, line3]
                            })
        
        return triangles
    
    def _forms_triangle(self, line1, line2, line3):
        """Üç çizginin üçgen oluşturup oluşturmadığını kontrol eder"""
        intersection1 = line_intersection(line1, line2)
        intersection2 = line_intersection(line2, line3)
        intersection3 = line_intersection(line3, line1)
        
        if intersection1 is None or intersection2 is None or intersection3 is None:
            return False
        
        # Kesişim noktaları farklı olmalı
        if (intersection1 == intersection2 or 
            intersection2 == intersection3 or 
            intersection3 == intersection1):
            return False
        
        # Kenar uzunluklarını kontrol et
        side1 = side_length(intersection1, intersection2)
        side2 = side_length(intersection2, intersection3)
        side3 = side_length(intersection3, intersection1)
        
        # Minimum kenar uzunluğu kontrolü
        if min(side1, side2, side3) < 20:
            return False
        
        # Yaklaşık eşkenar üçgen kontrolü (opsiyonel)
        max_side = max(side1, side2, side3)
        min_side = min(side1, side2, side3)
        
        return max_side - min_side < TOLERANCE * max_side
    
    def _calculate_triangle_centroid(self, line1, line2, line3):
        """Üçgenin merkez noktasını hesaplar"""
        intersection1 = line_intersection(line1, line2)
        intersection2 = line_intersection(line2, line3)
        intersection3 = line_intersection(line3, line1)
        
        if intersection1 and intersection2 and intersection3:
            cx = (intersection1[0] + intersection2[0] + intersection3[0]) / 3
            cy = (intersection1[1] + intersection2[1] + intersection3[1]) / 3
            return (int(cx), int(cy))
        return None

class HexagonDetector(ShapeDetector):
    """Altıgen tespit sınıfı"""
    
    def detect_hexagons(self, image, color_mask=None):
        """Görüntüde altıgenleri tespit eder"""
        hexagons = []
        
        # Renk maskesi varsa uygula
        if color_mask is not None:
            masked_image = cv2.bitwise_and(image, image, mask=color_mask)
            edges = self._preprocess_frame(masked_image)
        else:
            edges = self._preprocess_frame(image)
        
        # Hough çizgi tespiti
        lines = cv2.HoughLinesP(
            edges, 1, math.pi / 180,
            threshold=HOUGH_THRESHOLD,
            minLineLength=MIN_LINE_LENGTH,
            maxLineGap=MAX_LINE_GAP
        )
        
        if lines is None or len(lines) < 6:
            return hexagons
        
        # Altıgen kombinasyonlarını kontrol et (basitleştirilmiş versiyon)
        # Gerçek uygulamada daha sofistike bir algoritma gerekir
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            # Konturu yaklaştır
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            
            # 6 köşesi varsa altıgen olabilir
            if len(approx) == 6:
                # Merkez noktayı hesapla
                M = cv2.moments(contour)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    
                    hexagons.append({
                        'type': 'hexagon',
                        'centroid': (cx, cy),
                        'contour': approx
                    })
        
        return hexagons

# ==== ANA İŞLEME SINIFI ====

class ShapeProcessor:
    """Kırmızı üçgen ve mavi altıgen tespit eden ana işlemci"""
    
    def __init__(self):
        self.triangle_detector = TriangleDetector()
        self.hexagon_detector = HexagonDetector()
        self.color_detector = ColorDetector()
        self.detections = []
        
    def process_frame(self, frame, drone_lat=None, drone_lon=None, capture_alt=None):
        """Bir görüntü karesini işler"""
        results = []
        h, w = frame.shape[:2]
        
        # Kırmızı bölgeleri tespit et
        red_mask = self.color_detector.detect_red_regions(frame)
        
        # Mavi bölgeleri tespit et
        blue_mask = self.color_detector.detect_blue_regions(frame)
        
        # Kırmızı bölgelerde üçgen ara
        red_triangles = self.triangle_detector.detect_triangles(frame, red_mask)
        for triangle in red_triangles:
            cx, cy = triangle['centroid']
            
            # GPS koordinatlarını hesapla
            if drone_lat and drone_lon and capture_alt:
                lat, lon = pixel_to_gps(cx, cy, w, h, drone_lat, drone_lon, capture_alt)
            else:
                lat, lon = 0.0, 0.0
            
            results.append({
                'type': 'red_triangle',
                'pixel_x': cx,
                'pixel_y': cy,
                'latitude': lat,
                'longitude': lon,
                'confidence': 0.95
            })
        
        # Mavi bölgelerde altıgen ara
        blue_hexagons = self.hexagon_detector.detect_hexagons(frame, blue_mask)
        for hexagon in blue_hexagons:
            cx, cy = hexagon['centroid']
            
            # GPS koordinatlarını hesapla
            if drone_lat and drone_lon and capture_alt:
                lat, lon = pixel_to_gps(cx, cy, w, h, drone_lat, drone_lon, capture_alt)
            else:
                lat, lon = 0.0, 0.0
            
            results.append({
                'type': 'blue_hexagon',
                'pixel_x': cx,
                'pixel_y': cy,
                'latitude': lat,
                'longitude': lon,
                'confidence': 0.90
            })
        
        return results
    
    def visualize_detections(self, frame, detections):
        """Tespit edilen şekilleri görselleştirir"""
        vis_frame = frame.copy()
        
        for detection in detections:
            cx = detection['pixel_x']
            cy = detection['pixel_y']
            
            if detection['type'] == 'red_triangle':
                # Kırmızı üçgen için kırmızı daire
                cv2.circle(vis_frame, (cx, cy), 10, (0, 0, 255), 2)
                cv2.putText(vis_frame, "RED TRI", (cx-25, cy-15), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            elif detection['type'] == 'blue_hexagon':
                # Mavi altıgen için mavi daire
                cv2.circle(vis_frame, (cx, cy), 10, (255, 0, 0), 2)
                cv2.putText(vis_frame, "BLUE HEX", (cx-25, cy-15),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
        
        return vis_frame

# ==== VIDEO İŞLEME ====

class VideoProcessor:
    """Video akışı veya görüntü dosyaları işleyici"""
    
    def __init__(self, source_type='webcam', source_path=None):
        self.source_type = source_type
        self.source_path = source_path
        self.processor = ShapeProcessor()
        self.csv_file = None
        self.csv_writer = None
        self.setup_csv()
        
    def setup_csv(self):
        """CSV dosyasını hazırlar"""
        os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
        
        # CSV başlıklarını yaz
        file_exists = os.path.exists(OUTPUT_CSV)
        self.csv_file = open(OUTPUT_CSV, 'a', newline='')
        self.csv_writer = csv.writer(self.csv_file)
        
        if not file_exists:
            self.csv_writer.writerow([
                'timestamp', 'type', 'pixel_x', 'pixel_y', 
                'latitude', 'longitude', 'confidence'
            ])
    
    def process_video_stream(self):
        """Video akışını işler"""
        if self.source_type == 'webcam':
            cap = cv2.VideoCapture(0)
        elif self.source_type == 'video':
            cap = cv2.VideoCapture(self.source_path)
        else:
            print(f"Geçersiz kaynak tipi: {self.source_type}")
            return
        
        print("Video işleme başladı. Çıkmak için 'q' tuşuna basın.")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Şekilleri tespit et
            detections = self.processor.process_frame(frame)
            
            # Sonuçları CSV'ye kaydet
            for detection in detections:
                self.csv_writer.writerow([
                    time.time(),
                    detection['type'],
                    detection['pixel_x'],
                    detection['pixel_y'],
                    detection['latitude'],
                    detection['longitude'],
                    detection['confidence']
                ])
            
            # Görselleştir
            vis_frame = self.processor.visualize_detections(frame, detections)
            cv2.imshow('Shape Detection', vis_frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()
        self.cleanup()
    
    def process_image_folder(self):
        """Klasördeki görüntüleri işler"""
        print(f"Görüntü klasörü izleniyor: {WATCH_FOLDER}")
        processed_files = set()
        
        try:
            while True:
                # Yeni görüntüleri kontrol et
                all_images = glob.glob(os.path.join(WATCH_FOLDER, "*.jpg"))
                all_images.extend(glob.glob(os.path.join(WATCH_FOLDER, "*.png")))
                
                new_images = [f for f in all_images if f not in processed_files]
                
                for img_path in new_images:
                    print(f"İşleniyor: {img_path}")
                    
                    # Görüntüyü yükle
                    frame = cv2.imread(img_path)
                    if frame is None:
                        continue
                    
                    # EXIF verisini al
                    exif = get_exif_data(img_path)
                    drone_lat, drone_lon, alt = get_lat_lon_alt(exif)
                    capture_alt = alt - HOME_ALTITUDE
                    
                    # Şekilleri tespit et
                    detections = self.processor.process_frame(
                        frame, drone_lat, drone_lon, capture_alt
                    )
                    
                    # Sonuçları CSV'ye kaydet
                    for detection in detections:
                        self.csv_writer.writerow([
                            os.path.basename(img_path),
                            detection['type'],
                            detection['pixel_x'],
                            detection['pixel_y'],
                            detection['latitude'],
                            detection['longitude'],
                            detection['confidence']
                        ])
                    
                    self.csv_file.flush()
                    processed_files.add(img_path)
                    
                    print(f"  - {len(detections)} şekil tespit edildi")
                    
                    # Görselleştir (opsiyonel)
                    if len(detections) > 0:
                        vis_frame = self.processor.visualize_detections(frame, detections)
                        cv2.imshow('Detections', vis_frame)
                        cv2.waitKey(1000)  # 1 saniye göster
                
                time.sleep(2)  # 2 saniyede bir kontrol et
                
        except KeyboardInterrupt:
            print("\nİşlem durduruldu.")
        finally:
            cv2.destroyAllWindows()
            self.cleanup()
    
    def cleanup(self):
        """Kaynakları temizle"""
        if self.csv_file:
            self.csv_file.close()
        print("Temizlik tamamlandı.")

# ==== ANA PROGRAM ====

def main():
    parser = argparse.ArgumentParser(
        description='Kırmızı üçgen ve mavi altıgen tespit sistemi'
    )
    parser.add_argument(
        '--mode', 
        choices=['webcam', 'video', 'folder'],
        default='webcam',
        help='İşlem modu: webcam, video dosyası veya görüntü klasörü'
    )
    parser.add_argument(
        '--source',
        help='Video dosyası yolu (video modu için)'
    )
    
    args = parser.parse_args()
    
    # İşlemciyi başlat
    if args.mode == 'webcam':
        processor = VideoProcessor(source_type='webcam')
        processor.process_video_stream()
    elif args.mode == 'video':
        if not args.source:
            print("Video modu için --source parametresi gerekli!")
            return
        processor = VideoProcessor(source_type='video', source_path=args.source)
        processor.process_video_stream()
    elif args.mode == 'folder':
        processor = VideoProcessor(source_type='folder')
        processor.process_image_folder()

if __name__ == "__main__":
    main()
