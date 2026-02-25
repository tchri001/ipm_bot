import keyboard
import os
import time
import pyautogui
from utils import open_bluestacks, zoom_to_max_then_down_one, get_currency_value_with_visualization, get_grid_midpoint

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
    # Open/focus BlueStacks
    open_bluestacks()

    # Move mouse to a grid location before any scrolling/zoom occurs
    grid_target = "O15"  # Change this to your target grid cell
    coords = get_grid_midpoint(grid_target)
    if coords:
        x, y = coords
        try:
            pyautogui.moveTo(x, y, duration=0.2)
            print(f"Moved mouse to {grid_target} (x={x}, y={y})")
        except Exception as e:
            print(f"Could not move mouse: {e}")
    else:
        print(f"Could not find grid coordinates for {grid_target}")

    # Continue with zooming
    zoom_to_max_then_down_one()
    
    # Test currency detection and show visualization
    print("\nCapturing currency region for verification...")
    currency = get_currency_value_with_visualization(region=(0, 0, 1920, 150), display=True)
    if currency:
        print(f"Detected currency value: ${currency}")
    else:
        print("Could not detect currency. Check 'currency_region_check.png' to adjust the region.")
    
    # Listen for exit key in the main thread
    listen_for_exit()
