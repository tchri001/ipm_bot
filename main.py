import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtGui import QPainter, QColor
from PyQt5.QtCore import Qt, QRect
import threading
import logging
from overlay import OverlayWindow
from utils import Utils
import time

class TransparentOverlay(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setGeometry(0, 0, QApplication.primaryScreen().size().width(),
                         QApplication.primaryScreen().size().height())
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.show()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw the rectangle
        rect = QRect(500, 300, 800, 600)
        painter.setPen(QColor(0, 255, 0, 255))
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(rect)
        painter.end()


def background_logic():
    while True:
        print("Background logic is running!")
        time.sleep(1)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    overlay = OverlayWindow()

    logging.basicConfig(filename="gc_bot.log", format='%(asctime)s %(message)s', filemode='w', level=logging.DEBUG)
    logger = logging.getLogger()
    utils = Utils(logger)
    exit_program = threading.Thread(target=utils.exit_program, args=())
    exit_program.start()

    # Run background logic in a separate thread
    #thread = threading.Thread(target=background_logic, daemon=True)q
    #thread.start()

    # Add some rectangles with different coordinates and sizes
    overlay.add_rectangle(100, 100, 200, 150)  # Rectangle 1
    overlay.add_rectangle(400, 300, 300, 200)  # Rectangle 2
    overlay.add_rectangle(800, 600, 150, 100)  # Rectangle 3

    print("Box has been created!")
    sys.exit(app.exec_())