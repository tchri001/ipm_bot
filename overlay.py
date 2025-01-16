from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtGui import QPainter, QColor
from PyQt5.QtCore import Qt, QRect

# Screen dimensions (these can be adjusted if necessary)
SCREEN_WIDTH = 2880
SCREEN_HEIGHT = 1800

class OverlayWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.rectangles = []  # Initialize a list to hold rectangle definitions
        self.initUI()

    def initUI(self):
        self.setGeometry(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)  # Fullscreen overlay
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.show()
        print("Initing rectangle overlay")

    def paintEvent(self, event):
        print("Rectangle overlay event started")
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw all rectangles in the list
        self.draw_rectangles(painter)

        painter.end()  # Ensure cleanup
        print("Rectangle overlay event ended")

    def draw_rectangles(self, painter):
        """Draw multiple rectangles based on the self.rectangles list."""
        for rect in self.rectangles:
            # Draw each rectangle
            x, y, width, height = rect
            rectangle = QRect(x, y, width, height)
            painter.setPen(QColor(0, 255, 0, 255))  # Green color for the border
            painter.setBrush(Qt.NoBrush)  # No fill color
            painter.drawRect(rectangle)
    
    def add_rectangle(self, x, y, width, height):
        """Add a rectangle definition to the list."""
        self.rectangles.append((x, y, width, height))
        self.update()  # Trigger a repaint of the window to show the new rectangle

    def clear_rectangles(self):
        """Clear all rectangles from the list."""
        self.rectangles.clear()
        self.update()  # Trigger a repaint of the window to remove the rectangles
