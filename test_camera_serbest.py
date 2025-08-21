import argparse
from camera import VideoRetriever
from serbest.image_operations import TriangleDetector


def main():
    parser = argparse.ArgumentParser(description="Test camera with triangle detection.")
    parser.add_argument(
        "connection_string",
        type=str,
        help="Connection string for the video stream. Possible values: 'gstreamer:<port>' or 'webcam'",
    )
    args = parser.parse_args()

    retriever = VideoRetriever(args.connection_string)
    processor = TriangleDetector()

    try:
        if not retriever.cap.isOpened():
            print("Error: Unable to open video stream. Please check the connection string.")
            return
        for frame in retriever.get_frames():
            triangle_centroids = processor.process_frame(frame)
            if triangle_centroids is None:
                continue
            print(f"Triangle detected at: {triangle_centroids}")
    finally:
        retriever.release()


if __name__ == "__main__":
    main()
