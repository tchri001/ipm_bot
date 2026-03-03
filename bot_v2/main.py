import keyboard
import json
import os
import shutil
import time
from datetime import datetime
import pyautogui
from utils import (
    open_bluestacks,
    zoom_to_max,
    zoom_out_configured_amount,
    open_resources_interface,
    get_currency_value_with_visualization,
    get_grid_midpoint,
    get_grid_region,
    set_input_log_path,
    log_input_event,
    set_zoom_modifier_key,
    save_reference_icon_anchor,
    align_screen_to_reference_icon,
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


def open_resources_tab():
    """Open and verify the resources tab."""
    resources_open = open_resources_interface(
        interface_search_start='M17',
        interface_search_end='V17',
        verify_search_start='S8',
        verify_search_end='V9',
        closed_icon_template='config/icons/tabs/resources_icon_closed.png',
        resource_window_template='config/icons/tabs/resource_window.png',
        click_confidence=0.75,
        verify_confidence=0.75,
        window_height_trim_ratio=0.2,
    )
    if resources_open:
        print("Resources interface check passed")
    else:
        print("Warning: resources interface check failed")
    return resources_open


def run_gameplay_loop(currency_region, debug_dir_name, key_log_hook):
    """
    Gameplay logic starts here.
    Setup/calibration should be completed before calling this function.
    """
    open_resources_tab()

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
                print(f"Cash: ${currency}")
            else:
                print("Cash: not detected")
            next_check = now + 5

        time.sleep(0.1)

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    key_log_path = os.path.join(base_dir, 'key_press_log.txt')
    ref_config_path = os.path.join(base_dir, 'config', 'ipm_config.json')
    default_scroll_start_grid = "T9"
    default_currency_region_start_grid = "I1"
    default_currency_region_end_grid = "P2"
    enable_focus_click = True  # Toggle this on/off for pre-zoom focus click
    set_input_log_path(key_log_path)
    key_log_hook = start_keypress_logger(key_log_path)
    print(f"Logging key events to: {key_log_path}")

    set_zoom_modifier_key('ctrl')
    print("Using zoom modifier key: ctrl")

    # Open/focus BlueStacks
    open_bluestacks()

    # Load startup grids from config and backfill keys if missing
    grid_target = default_scroll_start_grid
    currency_region_start_grid = default_currency_region_start_grid
    currency_region_end_grid = default_currency_region_end_grid
    try:
        if os.path.exists(ref_config_path):
            with open(ref_config_path, 'r', encoding='utf-8') as config_file:
                config_data = json.load(config_file)

            config_grid = str(config_data.get('scroll_start_grid', '')).strip().upper()
            if config_grid:
                grid_target = config_grid

            config_currency_start = str(config_data.get('currency_region_start_grid', '')).strip().upper()
            if config_currency_start:
                currency_region_start_grid = config_currency_start

            config_currency_end = str(config_data.get('currency_region_end_grid', '')).strip().upper()
            if config_currency_end:
                currency_region_end_grid = config_currency_end

            config_changed = False
            if 'scroll_start_grid' not in config_data:
                config_data['scroll_start_grid'] = default_scroll_start_grid
                config_changed = True
            if 'currency_region_start_grid' not in config_data:
                config_data['currency_region_start_grid'] = default_currency_region_start_grid
                config_changed = True
            if 'currency_region_end_grid' not in config_data:
                config_data['currency_region_end_grid'] = default_currency_region_end_grid
                config_changed = True

            if config_changed:
                with open(ref_config_path, 'w', encoding='utf-8') as config_file:
                    json.dump(config_data, config_file, indent=2)
    except Exception as e:
        print(f"Warning: could not load startup grids from config: {e}")

    print(f"Using scroll_start_grid: {grid_target}")
    print(f"Using currency region grid bounds: {currency_region_start_grid} -> {currency_region_end_grid}")

    # Move mouse to a grid location before any scrolling/zoom occurs
    coords = get_grid_midpoint(grid_target)
    if coords:
        x, y = coords
        try:
            pyautogui.moveTo(x, y, duration=0.2)
            print(f"Moved mouse to {grid_target} (x={x}, y={y})")
            log_input_event('mouse_move', '', '', f'x={x};y={y};phase=pre_zoom_initial_focus')
            if enable_focus_click:
                pyautogui.click()
                print("Clicked to focus window before zoom")
                log_input_event('mouse_click', '', '', f'x={x};y={y};button=left;phase=pre_zoom_initial_focus')
            else:
                print("Focus click disabled (enable_focus_click=False)")
        except Exception as e:
            print(f"Could not move mouse: {e}")
    else:
        print(f"Could not find grid coordinates for {grid_target}")

    # Zoom in before any reference-image detection/alignment.
    zoom_to_max()

    # Ensure reference icon anchor config exists (one-time calibration)
    if not os.path.exists(ref_config_path):
        print("Reference anchor config not found. Detecting ref_icon.png and saving anchor now...")
        anchor_saved = save_reference_icon_anchor(template_path='config/ref_icon.png', config_path='config/ipm_config.json', confidence=0.75)
        if anchor_saved is None:
            print("Warning: could not detect reference icon to save anchor coordinates.")

    # Startup alignment: drag map until reference icon is near saved coordinates
    alignment_ok = align_screen_to_reference_icon(config_path='config/ipm_config.json', tolerance_px=30, max_attempts=8)
    if not alignment_ok:
        print("Warning: reference alignment did not converge; continuing with current position.")

    # Reposition to grid target after alignment (dragging may move cursor elsewhere)
    coords = get_grid_midpoint(grid_target)
    if coords:
        x, y = coords
        try:
            pyautogui.moveTo(x, y, duration=0.2)
            print(f"Repositioned mouse to {grid_target} before zoom (x={x}, y={y})")
            log_input_event('mouse_move', '', '', f'x={x};y={y};phase=pre_zoom_reposition')
            if enable_focus_click:
                pyautogui.click()
                print("Clicked to focus window before zoom (post-alignment)")
                log_input_event('mouse_click', '', '', f'x={x};y={y};button=left;phase=pre_zoom_reposition')
        except Exception as e:
            print(f"Could not reposition mouse before zoom: {e}")

    # After max-zoom alignment, zoom out to the configured working level.
    zoom_out_configured_amount()

    # Currency monitor region from config bounds
    currency_region = get_grid_region(currency_region_start_grid, currency_region_end_grid)
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

    run_gameplay_loop(
        currency_region=currency_region,
        debug_dir_name=debug_dir_name,
        key_log_hook=key_log_hook,
    )
