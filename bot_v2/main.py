import keyboard
import os
import shutil
import time
import pyautogui
from utils import (
    open_bluestacks,
    zoom_to_max_then_down_one,
    get_currency_value_with_visualization,
    get_grid_midpoint,
    get_grid_region,
)

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

    # Currency monitor region bounded by J1..L2 (includes J1,K1,L1 and J2,K2,L2)
    currency_region = get_grid_region("J1", "L2")
    if currency_region is None:
        currency_region = (900, 0, 300, 200)
        print("Using fallback currency region (900, 0, 300, 200)")

    # Tighten region to focus on currency text only
    # Shrink by 20px on X sides and 50px on Y sides
    rx, ry, rw, rh = currency_region
    currency_region = (rx + 20, ry + 50, max(1, rw - 40), max(1, rh - 100))

    # Clear debug screenshot folder at startup (safer on Windows/OneDrive)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    debug_dir_name = 'currency_screenshots'
    debug_dir_path = os.path.join(base_dir, debug_dir_name)
    os.makedirs(debug_dir_path, exist_ok=True)

    for entry in os.scandir(debug_dir_path):
        try:
            if entry.is_file():
                os.remove(entry.path)
            elif entry.is_dir():
                shutil.rmtree(entry.path, ignore_errors=True)
        except OSError as e:
            print(f"Warning: could not remove {entry.path}: {e}")

    print(f"\nMonitoring currency every 5 seconds in region: {currency_region}")
    print("Press 'q' to exit.")
    print("Saving OCR crops to bot_v2/currency_screenshots")

    next_check = 0.0
    while True:
        if keyboard.is_pressed('q'):
            print("Exiting program...")
            os._exit(0)

        now = time.time()
        if now >= next_check:
            currency = get_currency_value_with_visualization(
                region=currency_region,
                display=False,
                debug_dir=debug_dir_name,
            )
            if currency is not None:
                print(f"Current currency: ${currency}")
            else:
                print("Current currency: not detected")
            next_check = now + 5

        time.sleep(0.1)
