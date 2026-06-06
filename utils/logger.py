import os
import cv2
import pandas as pd
from datetime import datetime

class DetectionLogger:
    def __init__(self, output_dir="output", cooldown_seconds=10):
        """
        output_dir: Main output directory where logs and plates will be saved.
        cooldown_seconds: Cooldown period during which the same license plate text
                          won't be logged repeatedly.
        """
        self.output_dir = output_dir
        self.cooldown_seconds = cooldown_seconds
        
        self.logs_dir = os.path.join(output_dir, "logs")
        self.plates_dir = os.path.join(output_dir, "plates")
        self.csv_path = os.path.join(self.logs_dir, "detections.csv")
        
        # Ensure directories exist
        os.makedirs(self.logs_dir, exist_ok=True)
        os.makedirs(self.plates_dir, exist_ok=True)
        
        # Cache for de-duplication: {plate_text: last_logged_datetime}
        self.recent_detections = {}

    def log_detection(self, plate_text, confidence, plate_image):
        """
        Logs plate details to CSV and saves cropped plate image.
        Returns dict containing log entry details if logged, or None if skipped due to cooldown.
        """
        if not plate_text or plate_image is None or plate_image.size == 0:
            return None

        # Clean plate text to be uppercase and alphanumeric
        plate_text = plate_text.strip().upper()
        now = datetime.now()
        
        # Check cooldown de-duplication
        if plate_text in self.recent_detections:
            time_diff = (now - self.recent_detections[plate_text]).total_seconds()
            if time_diff < self.cooldown_seconds:
                # Update timestamp to reset cooldown (keeps tracking active presence)
                self.recent_detections[plate_text] = now
                return None
                
        # Register/update the detection time
        self.recent_detections[plate_text] = now
        
        # Format timestamps
        timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")
        timestamp_safe = now.strftime("%Y%m%d_%H%M%S")
        
        # Save cropped plate image
        filename = f"{plate_text}_{timestamp_safe}.jpg"
        image_path = os.path.join(self.plates_dir, filename)
        # OpenCV image is BGR, save it directly
        cv2.imwrite(image_path, plate_image)
        
        # Relative path for logging
        relative_image_path = os.path.join("output", "plates", filename)
        
        # Append to CSV
        log_entry = {
            "Timestamp": timestamp_str,
            "Plate Text": plate_text,
            "Confidence": round(float(confidence), 2),
            "Image Path": relative_image_path
        }
        
        # Use pandas to append or create new CSV
        df = pd.DataFrame([log_entry])
        if not os.path.exists(self.csv_path):
            df.to_csv(self.csv_path, index=False)
        else:
            df.to_csv(self.csv_path, mode='a', header=False, index=False)
            
        return log_entry

    def get_all_logs(self):
        """
        Reads and returns all logged detections as a list of dicts.
        """
        if not os.path.exists(self.csv_path):
            return []
        try:
            df = pd.read_csv(self.csv_path)
            return df.to_dict(orient="records")
        except Exception as e:
            print(f"Error reading logs CSV: {e}")
            return []
            
    def clear_logs(self):
        """
        Clears the logs CSV file and deletes all plate images.
        """
        if os.path.exists(self.csv_path):
            try:
                os.remove(self.csv_path)
            except Exception as e:
                print(f"Error removing CSV: {e}")
                
        for file in os.listdir(self.plates_dir):
            file_path = os.path.join(self.plates_dir, file)
            if os.path.isfile(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"Error deleting file {file_path}: {e}")
                    
        self.recent_detections.clear()
