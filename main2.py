import sys
import logging
import threading
from utils import Utils
from overlay import OverlayWindow
from PyQt5.QtWidgets import QApplication

if __name__ == "__main__":
    logging.basicConfig(filename="gc_bot.log", format='%(asctime)s %(message)s', filemode='w', level=logging.DEBUG)
    logger = logging.getLogger()
    utils = Utils(logger)
    exit_program = threading.Thread(target=utils.exit_program, args=())
    exit_program.start()

    print("Starting rectangle")
    app = QApplication(sys.argv)
    overlay = OverlayWindow()
    app.exec_()  # Start the event loop
    print("Done drawing rectangle")

    