import cv2
import threading
import time

class VideoStream:
    """Singleton video stream manager that captures frames from camera."""
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, source=None):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, source=None):
        if self._initialized:
            return
        self._initialized = True
        self.source = source
        self.frame = None
        self.running = False
        self.cap = None
        self.thread = None
        
    def start(self, source=None):
        """Start the video capture thread."""
        if source:
            self.source = source
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()
        print(f"Video stream started from: {self.source}")
        
    def _capture_loop(self):
        """Continuous frame capture loop."""
        import os
        from ai_engine.config import AUTO_FALLBACK, VIDEO_PATH, CONNECTION_TIMEOUT
        
        # Force TCP to avoid frame drops/corruption in H264
        # stimeout is in microseconds (5,000,000 = 5s)
        timeout_us = str(CONNECTION_TIMEOUT * 1000)
        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = f"rtsp_transport;tcp|stimeout;{timeout_us}"
        
        print(f"VIDEO STREAM: Attempting to open {self.source}")
        self.cap = cv2.VideoCapture(self.source)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        retry_count = 0
        max_retries = 3
        
        while self.running:
            if not self.cap.isOpened():
                if AUTO_FALLBACK and retry_count >= max_retries:
                    print(f"VIDEO STREAM: Auto-Fallback triggered. Switching to {VIDEO_PATH}")
                    self.source = VIDEO_PATH
                    if "OPENCV_FFMPEG_CAPTURE_OPTIONS" in os.environ:
                        del os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"]
                    self.cap = cv2.VideoCapture(self.source)
                else:
                    retry_count += 1
                    print(f"Stream connection failed (Attempt {retry_count}/{max_retries}). Retrying...")
                    time.sleep(1)
                    self.cap = cv2.VideoCapture(self.source)
                continue

            success, frame = self.cap.read()
            if success:
                retry_count = 0 # Reset on success
                # Resize to a smaller resolution for the web feed to save CPU/bandwidth
                frame = cv2.resize(frame, (640, 360))
                self.frame = frame
            else:
                retry_count += 1
                print(f"Frame capture failed. Reconnecting ({retry_count})...")
                time.sleep(2)
                self.cap = cv2.VideoCapture(self.source)
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                
        if self.cap:
            self.cap.release()
            
    def get_frame(self):
        """Get the current frame as JPEG bytes."""
        if self.frame is None:
            return None
        _, jpeg = cv2.imencode('.jpg', self.frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        return jpeg.tobytes()
    
    def stop(self):
        """Stop the video capture."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)

# Global instance
video_stream = VideoStream()
