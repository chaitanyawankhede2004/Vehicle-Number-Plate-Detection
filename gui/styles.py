DARK_STYLE = """
/* General Window Background */
QMainWindow {
    background-color: #121212;
}

/* Base Widget Styling */
QWidget {
    color: #e0e0e0;
    font-family: 'Segoe UI', 'Inter', 'Helvetica Neue', Arial, sans-serif;
    font-size: 13px;
}

/* Sidebar / Card Panels */
QFrame#ControlPanel, QFrame#LogsPanel, QFrame#SettingsPanel {
    background-color: #1e1e1e;
    border-radius: 8px;
    border: 1px solid #2d2d2d;
}

/* Video Canvas Frame */
QFrame#VideoContainer {
    background-color: #151515;
    border-radius: 8px;
    border: 2px dashed #3a3a3a;
}

/* Buttons */
QPushButton {
    background-color: #2e2e2e;
    border: 1px solid #424242;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 600;
    min-height: 20px;
}

QPushButton:hover {
    background-color: #3e3e3e;
    border: 1px solid #5a5a5a;
}

QPushButton:pressed {
    background-color: #1f1f1f;
}

/* Primary Action Buttons */
QPushButton#PrimaryButton {
    background-color: #6200ee;
    color: #ffffff;
    border: none;
}

QPushButton#PrimaryButton:hover {
    background-color: #7c4dff;
}

QPushButton#PrimaryButton:pressed {
    background-color: #3700b3;
}

/* Secondary/Accent Actions (e.g. Stop, Clear) */
QPushButton#DangerButton {
    background-color: #cf6679;
    color: #121212;
    border: none;
}

QPushButton#DangerButton:hover {
    background-color: #ff8a80;
}

QPushButton#DangerButton:pressed {
    background-color: #b00020;
}

/* Input Fields (Text boxes, SpinBoxes, ComboBoxes) */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #2d2d2d;
    border: 1px solid #424242;
    border-radius: 4px;
    padding: 6px;
    color: #ffffff;
}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
    border: 1px solid #6200ee;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;
    border-left: 1px solid #424242;
}

/* Slider Controls */
QSlider::groove:horizontal {
    border: 1px solid #2d2d2d;
    height: 6px;
    background: #2d2d2d;
    border-radius: 3px;
}

QSlider::sub-page:horizontal {
    background: #6200ee;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #bb86fc;
    width: 14px;
    margin-top: -4px;
    margin-bottom: -4px;
    border-radius: 7px;
}

/* Headings and Labels */
QLabel#HeaderLabel {
    font-size: 16px;
    font-weight: bold;
    color: #ffffff;
}

QLabel#TitleLabel {
    font-size: 20px;
    font-weight: bold;
    color: #6200ee;
}

QLabel#StatValue {
    font-size: 24px;
    font-weight: bold;
    color: #03dac6;
}

QLabel#StatLabel {
    font-size: 11px;
    color: #a0a0a0;
    text-transform: uppercase;
}

/* Table Styling */
QTableWidget {
    background-color: #1e1e1e;
    border: 1px solid #2d2d2d;
    gridline-color: #2d2d2d;
    border-radius: 8px;
}

QTableWidget::item {
    padding: 8px;
    border-bottom: 1px solid #2d2d2d;
}

QTableWidget::item:selected {
    background-color: #2e2e2e;
    color: #bb86fc;
}

QHeaderView::section {
    background-color: #2d2d2d;
    color: #a0a0a0;
    padding: 8px;
    border: none;
    font-weight: bold;
}

/* ScrollBars */
QScrollBar:vertical {
    border: none;
    background: #121212;
    width: 10px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #2d2d2d;
    min-height: 20px;
    border-radius: 5px;
}

QScrollBar::handle:vertical:hover {
    background: #424242;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    border: none;
    background: none;
}
"""
