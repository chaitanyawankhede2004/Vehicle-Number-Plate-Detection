from PyQt5.QtWidgets import (
    QWidget, QLabel, QTableWidget, QTableWidgetItem, 
    QVBoxLayout, QHBoxLayout, QHeaderView, QAbstractItemView
)
from PyQt5.QtGui import QPixmap, QImage, QPainter
from PyQt5.QtCore import Qt, pyqtSignal

class VideoViewport(QLabel):
    """
    Custom Label to render live video streams and static images nicely.
    Maintains aspect ratio and displays a professional placeholder when idle.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(400, 300)
        self.current_qimage = None
        self.setPlaceholderText("No video source active.\nLoad an Image/Video or Start Webcam to begin.")

    def setPlaceholderText(self, text):
        self.setText(text)
        self.setStyleSheet("""
            color: #6a6a6a;
            font-size: 14px;
            font-weight: 500;
        """)

    def update_frame(self, q_image):
        """
        Updates the displayed image, scaling it to fit the label size while keeping the aspect ratio.
        """
        self.current_qimage = q_image
        self.repaint()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.current_qimage:
            self.repaint()

    def paintEvent(self, event):
        if not self.current_qimage:
            super().paintEvent(event)
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        # Scale the image to fit keeping the aspect ratio
        scaled_pixmap = QPixmap.fromImage(self.current_qimage).scaled(
            self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        
        # Center the scaled image
        x = (self.width() - scaled_pixmap.width()) // 2
        y = (self.height() - scaled_pixmap.height()) // 2
        
        painter.drawPixmap(x, y, scaled_pixmap)


class LogsTable(QTableWidget):
    """
    Custom QTableWidget to display log history of license plate detections.
    Supports displaying thumbnails of license plate crops.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(4)
        self.setHorizontalHeaderLabels(["Timestamp", "Crop", "Plate Number", "Confidence"])
        
        # Layout behaviors
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents) # Crop col
        self.verticalHeader().setDefaultSectionSize(45)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setAlternatingRowColors(True)
        self.setStyleSheet("""
            QTableWidget {
                alternate-background-color: #252525;
            }
        """)

    def add_detection_row(self, timestamp, plate_text, confidence, plate_image_path):
        """
        Appends a row to the log table.
        """
        row = self.rowCount()
        self.insertRow(row)
        
        # Timestamp
        time_item = QTableWidgetItem(timestamp)
        time_item.setTextAlignment(Qt.AlignCenter)
        self.setItem(row, 0, time_item)
        
        # Plate crop image thumbnail
        if plate_image_path and os.path.exists(plate_image_path):
            img_label = QLabel()
            img_label.setAlignment(Qt.AlignCenter)
            pix = QPixmap(plate_image_path)
            # Standard scale for plate display in row
            img_label.setPixmap(pix.scaled(100, 35, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            img_label.setStyleSheet("background-color: transparent; border: none; padding: 2px;")
            self.setCellWidget(row, 1, img_label)
        else:
            empty_item = QTableWidgetItem("N/A")
            empty_item.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 1, empty_item)
            
        # Plate text
        text_item = QTableWidgetItem(plate_text)
        text_item.setTextAlignment(Qt.AlignCenter)
        text_item.setFont(self.font())
        # Highlight plate text in bold uppercase
        font = text_item.font()
        font.setBold(True)
        font.setPointSize(11)
        text_item.setFont(font)
        self.setItem(row, 2, text_item)
        
        # Confidence score
        conf_item = QTableWidgetItem(f"{confidence:.2%}")
        conf_item.setTextAlignment(Qt.AlignCenter)
        self.setItem(row, 3, conf_item)
        
        # Scroll to bottom to show new logs
        self.scrollToBottom()


class StatsBlock(QWidget):
    """
    Custom widget for showing a single stat value with a title (e.g., total plates detected).
    """
    def __init__(self, title, initial_value="0", parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(4)
        
        self.title_label = QLabel(title)
        self.title_label.setObjectName("StatLabel")
        self.title_label.setAlignment(Qt.AlignCenter)
        
        self.value_label = QLabel(initial_value)
        self.value_label.setObjectName("StatValue")
        self.value_label.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(self.value_label)
        layout.addWidget(self.title_label)
        
        self.setStyleSheet("""
            QWidget {
                background-color: #252525;
                border-radius: 6px;
                border: 1px solid #333333;
            }
        """)

    def set_value(self, val):
        self.value_label.setText(str(val))

import os
