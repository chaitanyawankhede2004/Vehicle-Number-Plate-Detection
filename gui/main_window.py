import os
import cv2
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout, 
    QHBoxLayout, QFileDialog, QSlider, QFormLayout, QFrame, 
    QMessageBox, QStatusBar, QInputDialog
)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QThread, pyqtSignal

from core.detector import LicensePlateDetector
from core.video_processor import VideoProcessorThread
from utils.logger import DetectionLogger
from gui.widgets import VideoViewport, LogsTable, StatsBlock
from gui.styles import DARK_STYLE

class DetectorInitWorker(QThread):
    """
    Worker thread to initialize the LicensePlateDetector (which loads EasyOCR models)
    without freezing the main PyQt GUI thread.
    """
    initialized = pyqtSignal(object)
    error = pyqtSignal(str)

    def run(self):
        try:
            detector = LicensePlateDetector()
            self.initialized.emit(detector)
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Vehicle License Plate Detection & OCR System")
        self.resize(1100, 800)
        self.setStyleSheet(DARK_STYLE)

        # Initialize Logger
        self.logger = DetectionLogger()
        self.detector = None
        self.video_thread = None
        self.current_image_path = None
        
        # UI State Counters
        self.total_detected_count = 0
        self.unique_plates = set()

        # Build UI layout
        self.setup_ui()
        
        # Create Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Async load the plate detector/EasyOCR models
        self.load_detector_async()

    def load_detector_async(self):
        self.status_bar.showMessage("Loading EasyOCR Model weights... Please wait (this can take a moment)...")
        self.set_controls_enabled(False)
        
        self.worker = DetectorInitWorker()
        self.worker.initialized.connect(self.on_detector_ready)
        self.worker.error.connect(self.on_detector_error)
        self.worker.start()

    def on_detector_ready(self, detector):
        self.detector = detector
        self.set_controls_enabled(True)
        self.status_bar.showMessage("EasyOCR initialized and ready.", 5000)

    def on_detector_error(self, err_msg):
        self.status_bar.showMessage(f"Error initializing EasyOCR: {err_msg}")
        QMessageBox.critical(
            self, "Initialization Error", 
            f"Failed to load EasyOCR models. Please check your internet connection or console output.\n\nError: {err_msg}"
        )

    def set_controls_enabled(self, enabled):
        self.btn_load_image.setEnabled(enabled)
        self.btn_load_video.setEnabled(enabled)
        self.btn_start_webcam.setEnabled(enabled)
        self.slider_confidence.setEnabled(enabled)
        self.slider_cooldown.setEnabled(enabled)

    def setup_ui(self):
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # ----------------- LEFT PANEL (Controls & Stats) -----------------
        left_layout = QVBoxLayout()
        left_layout.setSpacing(15)
        
        # Title Card
        title_frame = QFrame()
        title_layout = QVBoxLayout(title_frame)
        title_label = QLabel("ANPR System")
        title_label.setObjectName("TitleLabel")
        title_label.setAlignment(Qt.AlignCenter)
        sub_title = QLabel("Automatic Number Plate Recognition")
        sub_title.setAlignment(Qt.AlignCenter)
        sub_title.setStyleSheet("color: #888888; font-size: 11px;")
        title_layout.addWidget(title_label)
        title_layout.addWidget(sub_title)
        left_layout.addWidget(title_frame)

        # Control Panel
        control_panel = QFrame()
        control_panel.setObjectName("ControlPanel")
        control_layout = QVBoxLayout(control_panel)
        control_layout.setContentsMargins(15, 15, 15, 15)
        control_layout.setSpacing(12)
        
        lbl_controls = QLabel("Media Inputs")
        lbl_controls.setObjectName("HeaderLabel")
        control_layout.addWidget(lbl_controls)

        self.btn_load_image = QPushButton("Analyze Image")
        self.btn_load_image.setObjectName("PrimaryButton")
        self.btn_load_image.clicked.connect(self.load_image)
        
        self.btn_load_video = QPushButton("Analyze Video File")
        self.btn_load_video.clicked.connect(self.load_video)
        
        self.btn_start_webcam = QPushButton("Start Live Webcam")
        self.btn_start_webcam.clicked.connect(self.start_webcam)
        
        # Video controls (Initially hidden/disabled)
        self.video_ctrls_layout = QHBoxLayout()
        self.btn_pause_video = QPushButton("Pause")
        self.btn_pause_video.clicked.connect(self.pause_video)
        self.btn_stop_video = QPushButton("Stop")
        self.btn_stop_video.setObjectName("DangerButton")
        self.btn_stop_video.clicked.connect(self.stop_video)
        self.video_ctrls_layout.addWidget(self.btn_pause_video)
        self.video_ctrls_layout.addWidget(self.btn_stop_video)
        
        self.video_ctrls_widget = QWidget()
        self.video_ctrls_widget.setLayout(self.video_ctrls_layout)
        self.video_ctrls_widget.setVisible(False)

        control_layout.addWidget(self.btn_load_image)
        control_layout.addWidget(self.btn_load_video)
        control_layout.addWidget(self.btn_start_webcam)
        control_layout.addWidget(self.video_ctrls_widget)
        
        left_layout.addWidget(control_panel)

        # Stats Panel
        stats_panel = QFrame()
        stats_panel.setObjectName("ControlPanel")
        stats_layout = QVBoxLayout(stats_panel)
        stats_layout.setContentsMargins(15, 15, 15, 15)
        stats_layout.setSpacing(10)
        
        lbl_stats_hdr = QLabel("Detections Status")
        lbl_stats_hdr.setObjectName("HeaderLabel")
        stats_layout.addWidget(lbl_stats_hdr)
        
        stats_grid = QHBoxLayout()
        self.stat_total = StatsBlock("Total Logs", "0")
        self.stat_unique = StatsBlock("Unique Plates", "0")
        stats_grid.addWidget(self.stat_total)
        stats_grid.addWidget(self.stat_unique)
        stats_layout.addLayout(stats_grid)
        
        left_layout.addWidget(stats_panel)

        # Settings Panel
        settings_panel = QFrame()
        settings_panel.setObjectName("SettingsPanel")
        settings_layout = QVBoxLayout(settings_panel)
        settings_layout.setContentsMargins(15, 15, 15, 15)
        settings_layout.setSpacing(10)
        
        lbl_settings = QLabel("Detection Settings")
        lbl_settings.setObjectName("HeaderLabel")
        settings_layout.addWidget(lbl_settings)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        # Confidence slider
        self.slider_confidence = QSlider(Qt.Horizontal)
        self.slider_confidence.setRange(10, 95)
        self.slider_confidence.setValue(30) # Default 30%
        self.slider_confidence.valueChanged.connect(self.on_settings_changed)
        self.lbl_conf_value = QLabel("30%")
        self.lbl_conf_value.setStyleSheet("font-weight: bold; color: #bb86fc;")
        
        conf_h = QHBoxLayout()
        conf_h.addWidget(self.slider_confidence)
        conf_h.addWidget(self.lbl_conf_value)
        form_layout.addRow("Min OCR Confidence:", conf_h)
        
        # Cooldown slider
        self.slider_cooldown = QSlider(Qt.Horizontal)
        self.slider_cooldown.setRange(1, 120)
        self.slider_cooldown.setValue(10) # Default 10s
        self.slider_cooldown.valueChanged.connect(self.on_settings_changed)
        self.lbl_cooldown_value = QLabel("10s")
        self.lbl_cooldown_value.setStyleSheet("font-weight: bold; color: #bb86fc;")
        
        cool_h = QHBoxLayout()
        cool_h.addWidget(self.slider_cooldown)
        cool_h.addWidget(self.lbl_cooldown_value)
        form_layout.addRow("Duplicate Cooldown:", cool_h)
        
        settings_layout.addLayout(form_layout)
        
        # Clear database/logs action
        btn_clear_logs = QPushButton("Clear Saved Detections")
        btn_clear_logs.setObjectName("DangerButton")
        btn_clear_logs.clicked.connect(self.clear_logs)
        settings_layout.addWidget(btn_clear_logs)

        left_layout.addWidget(settings_panel)
        left_layout.addStretch()

        # ----------------- CENTER & RIGHT PANEL -----------------
        center_layout = QVBoxLayout()
        center_layout.setSpacing(15)

        # Video/Image viewer container
        video_container = QFrame()
        video_container.setObjectName("VideoContainer")
        video_box_layout = QVBoxLayout(video_container)
        video_box_layout.setContentsMargins(5, 5, 5, 5)
        
        self.viewport = VideoViewport()
        video_box_layout.addWidget(self.viewport)
        
        center_layout.addWidget(video_container, stretch=3)

        # Logs & Table Panel
        logs_panel = QFrame()
        logs_panel.setObjectName("LogsPanel")
        logs_layout = QVBoxLayout(logs_panel)
        logs_layout.setContentsMargins(15, 15, 15, 15)
        logs_layout.setSpacing(10)
        
        lbl_logs = QLabel("Real-Time Detections Logs")
        lbl_logs.setObjectName("HeaderLabel")
        logs_layout.addWidget(lbl_logs)
        
        self.logs_table = LogsTable()
        logs_layout.addWidget(self.logs_table)
        
        center_layout.addWidget(logs_panel, stretch=2)

        # Combine Panels
        main_layout.addLayout(left_layout, stretch=1)
        main_layout.addLayout(center_layout, stretch=3)
        
        # Load any existing logs from disk on startup
        self.load_existing_logs()

    def load_existing_logs(self):
        logs = self.logger.get_all_logs()
        self.total_detected_count = len(logs)
        self.stat_total.set_value(self.total_detected_count)
        
        for entry in logs:
            plate = entry["Plate Text"]
            self.unique_plates.add(plate)
            self.logs_table.add_detection_row(
                entry["Timestamp"],
                plate,
                float(entry["Confidence"]),
                entry["Image Path"]
            )
        self.stat_unique.set_value(len(self.unique_plates))

    def on_settings_changed(self):
        # Confidence
        conf_val = self.slider_confidence.value()
        self.lbl_conf_value.setText(f"{conf_val}%")
        if self.detector:
            self.detector.set_confidence_threshold(conf_val / 100.0)
            
        # Cooldown
        cool_val = self.slider_cooldown.value()
        self.lbl_cooldown_value.setText(f"{cool_val}s")
        self.logger.cooldown_seconds = cool_val

    def load_image(self):
        self.stop_video()
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Image File", "", "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if not file_path:
            return
            
        self.current_image_path = file_path
        self.status_bar.showMessage(f"Processing image: {os.path.basename(file_path)}")
        
        # Load and process image
        img = cv2.imread(file_path)
        if img is None:
            QMessageBox.critical(self, "Error", "Failed to load image file.")
            return

        detections = self.detector.detect_plate(img)
        
        # Draw detections on image for display
        display_img = img.copy()
        for det in detections:
            x, y, w, h = det['box']
            text = det['text']
            conf = det['confidence']
            
            # Log the detection
            self.on_plate_detected(text, conf, det['plate_image'])
            
            cv2.rectangle(display_img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(
                display_img, f"{text} ({conf:.2f})", (x, y - 5), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2
            )
            
        # Display the processed image
        rgb_image = cv2.cvtColor(display_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        q_image = QImage(rgb_image.data, w, h, ch * w, QImage.Format_RGB888)
        self.viewport.update_frame(q_image)
        
        self.status_bar.showMessage(f"Image processing completed. Found {len(detections)} plate(s).", 5000)

    def load_video(self):
        self.stop_video()
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Video File", "", "Videos (*.mp4 *.avi *.mkv *.mov)"
        )
        if not file_path:
            return
            
        self.start_video_stream(file_path)

    def start_webcam(self):
        self.stop_video()
        
        # Prompt user for camera index (default 0)
        cam_idx, ok = QInputDialog.getInt(
            self, "Select Camera Source", "Webcam Device Index:", 0, 0, 10, 1
        )
        if ok:
            self.start_video_stream(cam_idx)

    def start_video_stream(self, source):
        self.video_ctrls_widget.setVisible(True)
        self.btn_pause_video.setText("Pause")
        
        # Create and start QThread
        self.video_thread = VideoProcessorThread(source, self.detector)
        self.video_thread.frame_processed.connect(self.on_frame_processed)
        self.video_thread.plate_detected.connect(self.on_plate_detected)
        self.video_thread.error_occurred.connect(self.on_video_error)
        self.video_thread.finished.connect(self.on_video_finished)
        self.video_thread.start()
        
        src_name = f"Camera {source}" if isinstance(source, int) else os.path.basename(source)
        self.status_bar.showMessage(f"Streaming from: {src_name}")

    def on_frame_processed(self, q_image, detections):
        self.viewport.update_frame(q_image)

    def on_plate_detected(self, text, confidence, plate_image):
        # Log via logger (logger handles cooldown-based de-duplication)
        log_entry = self.logger.log_detection(text, confidence, plate_image)
        if log_entry:
            # Update values and display
            self.total_detected_count += 1
            self.stat_total.set_value(self.total_detected_count)
            
            self.unique_plates.add(text)
            self.stat_unique.set_value(len(self.unique_plates))
            
            self.logs_table.add_detection_row(
                log_entry["Timestamp"],
                text,
                confidence,
                log_entry["Image Path"]
            )

    def on_video_error(self, err_msg):
        self.status_bar.showMessage(f"Stream Error: {err_msg}")
        QMessageBox.warning(self, "Stream Error", err_msg)

    def on_video_finished(self):
        self.video_ctrls_widget.setVisible(False)
        self.status_bar.showMessage("Video playback/stream finished.", 5000)

    def pause_video(self):
        if self.video_thread and self.video_thread.isRunning():
            if self.video_thread.paused:
                self.video_thread.resume()
                self.btn_pause_video.setText("Pause")
                self.status_bar.showMessage("Resumed stream playback.")
            else:
                self.video_thread.pause()
                self.btn_pause_video.setText("Resume")
                self.status_bar.showMessage("Paused stream playback.")

    def stop_video(self):
        if self.video_thread:
            self.video_thread.stop()
            self.video_thread = None
        self.video_ctrls_widget.setVisible(False)
        self.viewport.current_qimage = None
        self.viewport.setPlaceholderText("No video source active.\nLoad an Image/Video or Start Webcam to begin.")

    def clear_logs(self):
        confirm = QMessageBox.question(
            self, "Clear Logs", 
            "Are you sure you want to delete all saved plate detections and images?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            self.logger.clear_logs()
            self.total_detected_count = 0
            self.stat_total.set_value(0)
            self.unique_plates.clear()
            self.stat_unique.set_value(0)
            self.logs_table.setRowCount(0)
            self.status_bar.showMessage("Logs and saved detections cleared successfully.", 5000)

    def closeEvent(self, event):
        # Ensure thread stops clean when closing the app window
        self.stop_video()
        event.accept()
