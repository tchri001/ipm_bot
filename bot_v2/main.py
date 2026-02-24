import keyboard
import os
import time
from utils import setup_bluestacks

def listen_for_exit():
    """
    Listens for the 'q' key press and kills the program when pressed.
    """
    print("Listening for 'q' key to exit...")
    while True:
        if keyboard.is_pressed('q'):
            print("Exiting program...")
            os._exit(0)
        time.sleep(0.1)  # Small delay to avoid excessive CPU usage

if __name__ == "__main__":
    # Run BlueStacks setup
    setup_bluestacks()
    
    # Listen for exit key in the main thread
    listen_for_exit()
    listen_for_exit()
