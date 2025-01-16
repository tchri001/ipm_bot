import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtGui import QPainter, QColor
from PyQt5.QtCore import Qt, QRect
import threading
import logging
from overlay import OverlayWindow
from utils import Utils
import time

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
    thread = threading.Thread(target=background_logic, daemon=True)
    thread.start()

    # Add some rectangles with different coordinates and sizes
    overlay.add_rectangle(100, 100, 200, 150)  # Rectangle 1
    overlay.add_rectangle(400, 300, 300, 200)  # Rectangle 2
    overlay.add_rectangle(800, 600, 150, 100)  # Rectangle 3

    print("Box has been created!")
    sys.exit(app.exec_())