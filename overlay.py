from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtGui import QPainter, QColor
from PyQt5.QtCore import Qt, QRect

# Screen dimensions and rectangle coordinates
SCREEN_WIDTH = 2880
SCREEN_HEIGHT = 1800
RECT_START_X = 1235
RECT_START_Y = 70
RECT_END_X = 2155
RECT_END_Y = 1700

class OverlayWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setGeometry(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)  # Fullscreen overlay
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.show()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw the rectangle
        rect = QRect(RECT_START_X, RECT_START_Y, 
                     RECT_END_X - RECT_START_X, 
                     RECT_END_Y - RECT_START_Y)
        painter.setPen(QColor(0, 255, 0, 255))  # Green rectangle
        painter.setBrush(Qt.NoBrush)  # No fill
        painter.drawRect(rect)