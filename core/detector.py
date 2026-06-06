import cv2
import numpy as np
import easyocr
import re
import os

class LicensePlateDetector:
    def __init__(self, languages=['en'], confidence_threshold=0.3):
        """
        Initializes the license plate detector with EasyOCR reader.
        """
        self.confidence_threshold = confidence_threshold
        # EasyOCR reader initialization (can take a few seconds on first run)
        self.reader = easyocr.Reader(languages, gpu=True) # Will automatically fall back to CPU if GPU is not available

    def set_confidence_threshold(self, threshold):
        self.confidence_threshold = threshold

    def preprocess_image(self, image):
        """
        Preprocesses the image to make contours more visible.
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Bilateral filter to preserve edges while removing noise
        filtered = cv2.bilateralFilter(gray, 11, 17, 17)
        
        # Canny edge detection
        edged = cv2.Canny(filtered, 30, 200)
        
        return gray, edged

    def find_plate_candidates(self, image, edged):
        """
        Finds contours in the edged image and filters them to identify potential number plates.
        Returns a list of tuples: (cropped_plate_image, bounding_box_coords)
        where bounding_box_coords is (x, y, w, h).
        """
        contours, _ = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:30]
        
        candidates = []
        
        for c in contours:
            # Approximate the contour
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.018 * peri, True)
            
            # Look for 4-cornered contours (likely rectangular)
            x, y, w, h = cv2.boundingRect(c)
            aspect_ratio = float(w) / h
            
            # Standard license plate aspect ratio is wide (usually 2.0 to 5.5)
            # Area must be reasonable to filter out tiny noise or huge objects
            area = cv2.contourArea(c)
            
            if 1000 < area < 100000:
                # Accept both 4-point contours and contours that fit plate aspect ratios closely
                if len(approx) == 4 or (2.0 <= aspect_ratio <= 5.5):
                    # Crop the candidate region with a tiny margin
                    margin_w = int(w * 0.05)
                    margin_h = int(h * 0.05)
                    
                    x1 = max(0, x - margin_w)
                    y1 = max(0, y - margin_h)
                    x2 = min(image.shape[1], x + w + margin_w)
                    y2 = min(image.shape[0], y + h + margin_h)
                    
                    cropped = image[y1:y2, x1:x2]
                    candidates.append((cropped, (x, y, w, h)))
                    
        return candidates

    def clean_text(self, text):
        """
        Cleans the detected text to conform to typical license plate formats (letters and numbers).
        """
        # Remove common OCR misread punctuation and strip spaces
        cleaned = re.sub(r'[^A-Z0-9]', '', text.upper())
        return cleaned

    def detect_plate(self, image):
        """
        Processes an image/frame, localizes the license plate, reads the characters,
        and returns details of the detection.
        Returns:
            list of dicts containing:
                - 'plate_image': cropped plate image (numpy array)
                - 'text': recognized license plate number
                - 'confidence': EasyOCR confidence score
                - 'box': (x, y, w, h) of detection in main image
        """
        if image is None:
            return []

        gray, edged = self.preprocess_image(image)
        candidates = self.find_plate_candidates(image, edged)
        
        results = []
        
        # 1. Try to read text from candidates first (highly optimized local detection)
        for cropped, box in candidates:
            if cropped.size == 0:
                continue
            
            # Run OCR on the candidate image
            ocr_results = self.reader.readtext(cropped)
            for (bbox, text, prob) in ocr_results:
                cleaned = self.clean_text(text)
                # Plate text length is usually between 4 and 12 characters
                if prob >= self.confidence_threshold and 4 <= len(cleaned) <= 12:
                    results.append({
                        'plate_image': cropped,
                        'text': cleaned,
                        'confidence': prob,
                        'box': box
                    })
                    # Found a valid plate, stop after the best candidate to avoid duplicate entries
                    break
            
            if results:
                break
                
        # 2. Fallback: If no candidate contour OCR succeeded, use EasyOCR on the entire image
        # which uses its internal CRAFT text detector. We filter for horizontal text chunks.
        if not results:
            h, w, _ = image.shape
            ocr_results = self.reader.readtext(image)
            for (bbox, text, prob) in ocr_results:
                cleaned = self.clean_text(text)
                if prob >= self.confidence_threshold and 4 <= len(cleaned) <= 12:
                    # Calculate bounding box from bbox coordinates: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
                    xs = [pt[0] for pt in bbox]
                    ys = [pt[1] for pt in bbox]
                    bx, by, bw, bh = int(min(xs)), int(min(ys)), int(max(xs) - min(xs)), int(max(ys) - min(ys))
                    
                    # Crop the plate
                    cropped = image[max(0, by):min(h, by+bh), max(0, bx):min(w, bx+bw)]
                    results.append({
                        'plate_image': cropped,
                        'text': cleaned,
                        'confidence': prob,
                        'box': (bx, by, bw, bh)
                    })
                    break # Return first matching plate
                    
        return results
