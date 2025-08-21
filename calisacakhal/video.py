
import cv2

class VideoRetriever:
    """Handles video capture from a file or webcam."""
    def __init__(self, source):
        if str(source).lower() == 'webcam':
            # Use 0 for the default webcam
            self.cap = cv2.VideoCapture(0)
        else:
            self.cap = cv2.VideoCapture(source)

        if not self.cap.isOpened():
            raise ValueError(f"Error: Unable to open video source: {source}")
        print(f"Video source '{source}' opened successfully.")

    def get_frames(self):
        """Generator function to yield frames from the video source."""
        while self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                print("End of video stream or cannot read frame.")
                break
            yield frame

    def release(self):
        """Releases the video capture object."""
        self.cap.release()
        print("Video source released.")

