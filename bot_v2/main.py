import keyboard
import os
import shutil
import time
from datetime import datetime
import pyautogui
from utils import (
    open_bluestacks,
    zoom_to_max_then_down_one,
    get_currency_value_with_visualization,
    get_grid_midpoint,
    get_grid_region,
    set_input_log_path,
    log_input_event,
    set_zoom_modifier_key,
)


def start_keypress_logger(log_path):
    """
    Log all keyboard events (down/up) to help debug unexpected input behavior.
    """
    with open(log_path, 'w', encoding='utf-8') as log_file:
        log_file.write("timestamp,event,key,scan_code,details\n")

    def _on_key_event(event):
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            with open(log_path, 'a', encoding='utf-8') as log_file:
                log_file.write(f"{timestamp},{event.event_type},{event.name},{event.scan_code},keyboard_hook\n")
        except OSError:
            pass

    return keyboard.hook(_on_key_event)

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    key_log_path = os.path.join(base_dir, 'key_press_log.txt')
    enable_focus_click = False  # Toggle this on/off for pre-zoom focus click
    set_input_log_path(key_log_path)
    key_log_hook = start_keypress_logger(key_log_path)
    print(f"Logging key events to: {key_log_path}")

    set_zoom_modifier_key('ctrl')
    print("Using zoom modifier key: ctrl")

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
            log_input_event('mouse_move', '', '', f'x={x};y={y}')
            if enable_focus_click:
                pyautogui.click()
                print("Clicked to focus window before zoom")
                log_input_event('mouse_click', '', '', f'x={x};y={y};button=left')
            else:
                print("Focus click disabled (enable_focus_click=False)")
        except Exception as e:
            print(f"Could not move mouse: {e}")
    else:
        print(f"Could not find grid coordinates for {grid_target}")

    # Continue with zooming
    zoom_to_max_then_down_one()

    # Currency monitor region bounded by I1..P2
    currency_region = get_grid_region("I1", "P2")
    if currency_region is None:
        currency_region = (800, 0, 800, 200)
        print("Using fallback currency region (800, 0, 800, 200)")

    # Tighten region to focus on currency text only
    # Shrink by 50px on Y sides, keep full X range
    rx, ry, rw, rh = currency_region
    currency_region = (rx, ry + 50, rw, max(1, rh - 100))

    # Clear debug screenshot folder at startup (safer on Windows/OneDrive)
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
            keyboard.unhook(key_log_hook)
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
