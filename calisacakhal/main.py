import cv2
import argparse
import os
import csv
import time
import asyncio  # MAVSDK için gerekli

# MAVSDK kütüphanesini import et
from mavsdk import System

# Yerel modülleri import et
from video import VideoRetriever
from detectors import TriangleDetector, HexagonDetector
from utils import pixel_to_gps

# Anlık telemetri verilerini saklamak için bir sınıf
class DroneTelemetry:
    def __init__(self):
        self.latitude = None
        self.longitude = None
        self.altitude = None
        self.roll = None
        self.pitch = None
        self.yaw = None
        self.is_ready = False

async def run():
    """
    Ana fonksiyonu çalıştırır ve MAVSDK entegrasyonunu yönetir.
    """
    parser = argparse.ArgumentParser(
        description="Detect colored shapes and calculate GPS coordinates using live drone telemetry.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    # --- Video ve Çıktı Argümanları ---
    parser.add_argument('--video_source', type=str, required=True, help="Path to video file, RTSP stream URL, or 'webcam'")
    parser.add_argument('--output_csv', type=str, default='detections.csv', help="Path for the output CSV file.")
    parser.add_argument('--hfov', type=float, default=78.0, help="Camera's horizontal field of view in degrees.")
    
    # --- MAVLink Bağlantı Argümanı ---
    parser.add_argument(
        '--connect',
        type=str,
        default='serial:///dev/ttyAMA0:921600',
        help="MAVSDK connection string. Default: 'serial:///dev/ttyAMA0:921600' for RPi GPIO."
    )

    args = parser.parse_args()

    # --- Drone Bağlantısı ve Telemetri Akışı ---
    drone = System()
    telemetry_data = DroneTelemetry()

    print(f"Connecting to drone via: {args.connect}")
    await drone.connect(system_address=args.connect)

    print("Waiting for drone to connect...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("Drone connected!")
            break

    # Telemetri görevlerini başlat
    asyncio.create_task(get_position(drone, telemetry_data))
    asyncio.create_task(get_attitude(drone, telemetry_data))

    # Telemetri verisinin gelmesini bekle
    while not telemetry_data.is_ready:
        print("Waiting for first telemetry data...")
        await asyncio.sleep(1)

    # --- Tespit ve Hesaplama Başlatma ---
    await detection_loop(args, telemetry_data)


async def get_position(drone, telemetry):
    """Anlık pozisyon verilerini alır."""
    async for position in drone.telemetry.position():
        telemetry.latitude = position.latitude_deg
        telemetry.longitude = position.longitude_deg
        telemetry.altitude = position.relative_altitude_m  # Yere göre yükseklik
        if telemetry.roll is not None: # Diğer veri de geldiyse hazırız
            telemetry.is_ready = True

async def get_attitude(drone, telemetry):
    """Anlık açı (roll, pitch, yaw) verilerini alır."""
    async for attitude in drone.telemetry.attitude_euler():
        telemetry.roll = attitude.roll_deg
        telemetry.pitch = attitude.pitch_deg
        telemetry.yaw = attitude.yaw_deg

async def detection_loop(args, telemetry):
    """Ana tespit döngüsü."""
    try:
        retriever = VideoRetriever(args.video_source)
    except ValueError as e:
        print(e)
        return

    triangle_detector = TriangleDetector()
    hexagon_detector = HexagonDetector()

    # CSV Kurulumu
    with open(args.output_csv, 'a', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)
        if os.path.getsize(args.output_csv) == 0:
            csv_writer.writerow(['Timestamp', 'Shape', 'Color', 'Latitude', 'Longitude', 'Pixel_X', 'Pixel_Y'])

        print("Starting detection loop... Press 'q' in the display window to quit.")
        
        try:
            for frame in retriever.get_frames():
                h, w, _ = frame.shape
                timestamp = time.time()
                
                detections = {
                    ('triangle', 'red'): triangle_detector.process_frame(frame, 'red'),
                    ('hexagon', 'blue'): hexagon_detector.process_frame(frame, 'blue')
                }

                for (shape, color), centroids in detections.items():
                    for cx, cy in centroids:
                        # ANLIK TELEMETRİ VERİSİNİ KULLAN
                        gps_coords = pixel_to_gps(
                            cx, cy, w, h, 
                            telemetry.latitude, telemetry.longitude, telemetry.altitude, 
                            telemetry.yaw, telemetry.pitch, telemetry.roll, args.hfov
                        )
                        if gps_coords:
                            lat, lon = gps_coords
                            print(f"Detected {color.upper()} {shape.upper()} -> GPS: ({lat:.7f}, {lon:.7f})")
                            csv_writer.writerow([timestamp, shape, color, lat, lon, cx, cy])
                            
                            draw_color = (0, 0, 255) if color == 'red' else (255, 0, 0)
                            cv2.drawMarker(frame, (cx, cy), draw_color, markerType=cv2.MARKER_CROSS, markerSize=20, thickness=2)
                            cv2.putText(frame, f"{color.capitalize()} {shape.capitalize()}", (cx + 15, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.6, draw_color, 2)

                cv2.imshow("Detection Feed", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        
        finally:
            print("\nCleaning up...")
            retriever.release()
            cv2.destroyAllWindows()
            print(f"Processing complete. Detections saved to '{args.output_csv}'")


if __name__ == "__main__":
    # Asenkron döngüyü başlat
    asyncio.run(run())