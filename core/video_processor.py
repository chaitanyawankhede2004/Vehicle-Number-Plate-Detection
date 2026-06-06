import cv2
import time
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QImage

class VideoProcessorThread(QThread):
    # Signal emitted when a new frame is ready to be displayed.
    # Passes: (QImage of the frame, list of current frame's detections)
    frame_processed = pyqtSignal(QImage, list)
    
    # Signal emitted when a new plate text is successfully detected.
    # Passes: (plate_text_str, confidence_float, cropped_plate_image_numpy)
    plate_detected = pyqtSignal(str, float, object)
    
    # Signal emitted if an error occurs (e.g., connection lost, file error)
    error_occurred = pyqtSignal(str)

    def __init__(self, source_path_or_idx, detector, detection_interval_frames=10):
        """
        source_path_or_idx: file path to video or integer index for webcam
        detector: instance of LicensePlateDetector
        detection_interval_frames: run OCR every N frames to maintain real-time performance
        """
        super().__init__()
        self.source = source_path_or_idx
        self.detector = detector
        self.detection_interval_frames = detection_interval_frames
        
        self.running = False
        self.paused = False
        self.cap = None

    def run(self):
        self.running = True
        self.cap = cv2.VideoCapture(self.source)
        
        if not self.cap.isOpened():
            self.error_occurred.emit(f"Failed to open source: {self.source}")
            self.running = False
            return

        frame_count = 0
        last_detections = []
        
        # Calculate target sleep to maintain reasonable frame rate (e.g., 30 FPS)
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0 or fps > 60:
            fps = 30.0
        frame_delay = 1.0 / fps

        while self.running:
            if self.paused:
                time.sleep(0.1)
                continue
            
            start_time = time.time()
            ret, frame = self.cap.read()
            
            if not ret:
                # Video ended or webcam disconnected
                break

            frame_count += 1
            detections = []

            # Perform detection periodically or on the first frame
            if frame_count % self.detection_interval_frames == 0 or frame_count == 1:
                # To prevent detection from blocking the video display loop,
                # we run detection on this frame.
                detections = self.detector.detect_plate(frame)
                last_detections = detections
                
                # Emit plate_detected signal for each distinct plate found
                for det in detections:
                    self.plate_detected.emit(det['text'], det['confidence'], det['plate_image'])
            else:
                # Use cached detections for intermediate frames to draw bounding boxes
                detections = last_detections

            # Draw bounding boxes and text overlays on the frame for display
            display_frame = frame.copy()
            for det in detections:
                x, y, w, h = det['box']
                text = det['text']
                conf = det['confidence']
                
                # Draw rectangular bounding box around the plate
                cv2.rectangle(display_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                
                # Draw label background
                label = f"{text} ({conf:.2f})"
                (label_w, label_h), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                cv2.rectangle(display_frame, (x, y - label_h - 10), (x + label_w, y), (0, 255, 0), cv2.FILLED)
                
                # Draw label text
                cv2.putText(display_frame, label, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

            # Convert frame to QImage for PyQt widget rendering
            rgb_image = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            q_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            
            # Emit processed frame to UI
            self.frame_processed.emit(q_image, detections)
            
            # Control frame rate
            elapsed = time.time() - start_time
            sleep_time = max(0.001, frame_delay - elapsed)
            time.sleep(sleep_time)

        self.cap.release()
        self.running = False

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False

    def stop(self):
        self.running = False
        self.wait() # Wait for thread to finish cleanly
