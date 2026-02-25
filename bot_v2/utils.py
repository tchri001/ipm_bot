import subprocess
import os
import pygetwindow as gw
import time
import pyautogui
import easyocr
import re
import numpy as np
from datetime import datetime

_OCR_READER = None
_INPUT_LOG_PATH = None
_ZOOM_MODIFIER_KEY = 'ctrlleft'


def set_input_log_path(log_path):
    """Set shared input log file path for utils-generated input events."""
    global _INPUT_LOG_PATH
    _INPUT_LOG_PATH = log_path


def log_input_event(event_type, key='', scan_code='', details=''):
    """Append a CSV input event row to the shared log file if configured."""
    if not _INPUT_LOG_PATH:
        return
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        safe_details = str(details).replace(',', ';')
        with open(_INPUT_LOG_PATH, 'a', encoding='utf-8') as log_file:
            log_file.write(f"{timestamp},{event_type},{key},{scan_code},{safe_details}\n")
    except OSError:
        pass


def set_zoom_modifier_key(key_name):
    """Set the key used as zoom modifier for scroll shortcuts (pyautogui key name)."""
    global _ZOOM_MODIFIER_KEY
    if key_name:
        _ZOOM_MODIFIER_KEY = key_name


def _get_ocr_reader():
    global _OCR_READER
    if _OCR_READER is None:
        print("Initializing OCR reader (first run may take a moment)...")
        _OCR_READER = easyocr.Reader(['en'])
    return _OCR_READER


def _parse_compact_currency(value_text):
    """
    Parse compact currency strings like:
    - 61.91K
    - 1,234
    - 2.5M
    Returns integer value or None.
    """
    if not value_text:
        return None

    cleaned = value_text.upper().replace(',', '').replace(' ', '')
    match = re.match(r'^(\d+(?:\.\d+)?)([KMBTQ]?)$', cleaned)
    if not match:
        return None

    number = float(match.group(1))
    suffix = match.group(2)

    multiplier = 1
    if suffix == 'K':
        multiplier = 1_000
    elif suffix == 'M':
        multiplier = 1_000_000
    elif suffix == 'B':
        multiplier = 1_000_000_000
    elif suffix == 'T':
        multiplier = 1_000_000_000_000
    elif suffix == 'Q':
        multiplier = 1_000_000_000_000_000

    return int(number * multiplier)


def _extract_currency_from_texts(texts):
    """
    Extract currency from OCR text snippets.
    Prefers '$' anchored matches but has a fallback compact-number match.
    """
    # 1) Strong match: number that follows '$'
    for text in texts:
        text_upper = text.upper()
        anchored = re.search(r'\$\s*([\d][\d,]*(?:\.\d+)?\s*[KMBTQ]?)', text_upper)
        if anchored:
            parsed = _parse_compact_currency(anchored.group(1))
            if parsed is not None:
                return parsed

    # 2) Join all snippets and try again (handles split OCR tokens like '$' + '61.91K')
    joined = ' '.join(t.upper() for t in texts)
    anchored_joined = re.search(r'\$\s*([\d][\d,]*(?:\.\d+)?\s*[KMBTQ]?)', joined)
    if anchored_joined:
        parsed = _parse_compact_currency(anchored_joined.group(1))
        if parsed is not None:
            return parsed

    # 3) Fallback: compact number with suffix even if '$' is missed by OCR
    # Use the largest detected value to avoid tiny noise fragments.
    candidates = re.findall(r'\b([\d][\d,]*(?:\.\d+)?\s*[KMBTQ])\b', joined)
    parsed_candidates = [
        _parse_compact_currency(candidate)
        for candidate in candidates
        if _parse_compact_currency(candidate) is not None
    ]
    if parsed_candidates:
        return max(parsed_candidates)

    return None


def _save_currency_debug_screenshot(screenshot, region, debug_dir):
    """Save the OCR crop image for debugging where currency detection is looking."""
    if not debug_dir:
        return None

    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = debug_dir if os.path.isabs(debug_dir) else os.path.join(base_dir, debug_dir)
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    x, y, width, height = region
    filename = f"currency_region_{timestamp}_x{x}_y{y}_w{width}_h{height}.png"
    output_path = os.path.join(output_dir, filename)
    screenshot.save(output_path)

    # Keep only the newest 20 debug screenshots
    max_debug_files = 20
    debug_files = []
    for entry in os.scandir(output_dir):
        if entry.is_file() and entry.name.startswith("currency_region_") and entry.name.endswith(".png"):
            debug_files.append((entry.path, entry.stat().st_mtime))

    if len(debug_files) > max_debug_files:
        debug_files.sort(key=lambda item: item[1])
        files_to_remove = debug_files[: len(debug_files) - max_debug_files]
        for file_path, _ in files_to_remove:
            try:
                os.remove(file_path)
            except OSError:
                pass

    return output_path


def get_grid_midpoint(grid_code, coords_file='screen_grid_coords.txt', box_size=100):
    """
    Read a grid code (e.g., 'O15') and return the midpoint coordinates of that cell.
    
    Args:
        grid_code: Grid cell code (e.g., 'O15')
        coords_file: Path to screen_grid_coords.txt
        box_size: Size of each grid cell in pixels (default 100)
    
    Returns:
        Tuple (x, y) of the cell midpoint, or None if not found
    """
    try:
        # Ensure grid code is uppercase
        grid_code = grid_code.upper().strip()

        if not os.path.isabs(coords_file):
            local_candidate = os.path.join(os.path.dirname(os.path.abspath(__file__)), coords_file)
            if os.path.exists(local_candidate):
                coords_file = local_candidate
        
        # Read the coordinates file
        with open(coords_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith(grid_code + ':'):
                    # Parse line like "O15:x=1400,y=1400"
                    parts = line.strip().split(':')
                    if len(parts) == 2:
                        coords = parts[1]  # "x=1400,y=1400"
                        x_str = coords.split(',')[0].split('=')[1]  # Extract 1400 from x=1400
                        y_str = coords.split(',')[1].split('=')[1]  # Extract 1400 from y=1400
                        
                        x = int(x_str)
                        y = int(y_str)
                        
                        # Return midpoint (add half of box_size to get center)
                        midpoint_x = x + (box_size // 2)
                        midpoint_y = y + (box_size // 2)
                        
                        return (midpoint_x, midpoint_y)
        
        print(f"Grid code '{grid_code}' not found in {coords_file}")
        return None
        
    except FileNotFoundError:
        print(f"Coordinates file '{coords_file}' not found")
        return None
    except Exception as e:
        print(f"Error reading grid coordinates: {e}")
        return None


def get_grid_region(top_left_code, bottom_right_code, coords_file='screen_grid_coords.txt', box_size=100):
    """
    Return a screenshot region tuple (x, y, width, height) bounded by two grid cells.

    Example: J1 to L2 with box_size=100 -> (900, 0, 300, 200)
    """
    try:
        if not os.path.isabs(coords_file):
            local_candidate = os.path.join(os.path.dirname(os.path.abspath(__file__)), coords_file)
            if os.path.exists(local_candidate):
                coords_file = local_candidate

        lookup = {}
        with open(coords_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or ':' not in line:
                    continue
                label, raw_coords = line.split(':', 1)
                parts = raw_coords.split(',')
                if len(parts) != 2:
                    continue
                x = int(parts[0].split('=')[1])
                y = int(parts[1].split('=')[1])
                lookup[label.upper()] = (x, y)

        start = lookup.get(top_left_code.upper())
        end = lookup.get(bottom_right_code.upper())
        if not start or not end:
            print(f"Could not find grid bounds: {top_left_code} to {bottom_right_code}")
            return None

        x1, y1 = start
        x2, y2 = end
        width = (x2 - x1) + box_size
        height = (y2 - y1) + box_size
        return (x1, y1, width, height)
    except Exception as e:
        print(f"Error building grid region: {e}")
        return None


def open_bluestacks():
    """
    Opens BlueStacks App Player or brings it to focus if already running.
    If minimized, it will be restored and brought to the foreground.
    """
    try:
        # Try to find the BlueStacks window
        windows = gw.getWindowsWithTitle('BlueStacks')
        
        if windows:
            # BlueStacks is already running, bring it to focus
            bluestacks_window = windows[0]
            bluestacks_window.activate()
            print("BlueStacks brought to focus")
        else:
            # BlueStacks is not running, launch it
            # Try common installation paths
            possible_paths = [
                r"C:\Program Files\BlueStacks\BlueStacks.exe",
                r"C:\Program Files (x86)\BlueStacks\BlueStacks.exe",
                r"C:\Program Files\BlueStacks_nxt\BlueStacks.exe",
            ]
            
            launched = False
            for path in possible_paths:
                if os.path.exists(path):
                    subprocess.Popen(path)
                    print(f"BlueStacks launched from {path}")
                    launched = True
                    time.sleep(2)  # Wait for BlueStacks to start
                    break
            
            if not launched:
                print("Could not find BlueStacks installation")
                
    except Exception as e:
        print(f"Error opening BlueStacks: {e}")


def zoom_to_max_then_down_one(scroll_anchor=None):
    """
    Zoom sequence:
    1) Hold modifier and scroll up 5 times
    2) Hold modifier and scroll down 5 times

    Args:
        scroll_anchor: Optional tuple (x, y). If provided, mouse is moved to this
            safe point before and during scrolling to avoid hovering interactive UI.
    """
    time.sleep(2)  # Wait for BlueStacks to be ready before zoom input

    def _move_to_anchor():
        if scroll_anchor is None:
            return
        try:
            anchor_x, anchor_y = scroll_anchor
            pyautogui.moveTo(anchor_x, anchor_y, duration=0.05)
            log_input_event('mouse_move', '', '', f'x={anchor_x};y={anchor_y};phase=zoom_anchor')
        except Exception:
            pass
    
    # Zoom in to maximum (hold Ctrl, scroll up 5 times, then release Ctrl)
    _move_to_anchor()
    pyautogui.keyDown(_ZOOM_MODIFIER_KEY)
    time.sleep(0.4)
    for i in range(5):
        _move_to_anchor()
        pyautogui.scroll(100)  # Scroll up (positive value)
        log_input_event('mouse_scroll', '', '', f'amount=100;zoom_in_iter={i+1}')
        time.sleep(0.1)
    pyautogui.keyUp(_ZOOM_MODIFIER_KEY)
    time.sleep(0.4)
    print("Zoomed in to maximum")
    
    time.sleep(0.5)
    
    # Zoom out by a set amount (hold Ctrl, scroll down 5 times, then release Ctrl)
    _move_to_anchor()
    pyautogui.keyDown(_ZOOM_MODIFIER_KEY)
    time.sleep(0.4)
    for i in range(5):
        _move_to_anchor()
        pyautogui.scroll(-40)  # Scroll down (negative value)
        log_input_event('mouse_scroll', '', '', f'amount=-40;zoom_out_iter={i+1}')
        time.sleep(0.1)
    pyautogui.keyUp(_ZOOM_MODIFIER_KEY)
    time.sleep(0.4)
    print("Zoomed out by configured amount")


def get_currency_value_with_visualization(region=(0, 0, 1920, 150), display=True, debug_dir=None):
    """
    Captures currency value from the game window using OCR.
    
    Args:
        region: Tuple (x, y, width, height) for the screenshot region
        display: (Kept for compatibility, not used currently)
    
    Returns:
        Integer value of the currency, or None if not found
    """
    try:
        # Take screenshot of the specified region
        screenshot = pyautogui.screenshot(region=region)

        # Save OCR target crop for debugging if requested
        saved_path = _save_currency_debug_screenshot(screenshot, region, debug_dir)
        if saved_path:
            print(f"Saved OCR crop: {saved_path}")

        # Reuse OCR reader for faster repeated polling
        reader = _get_ocr_reader()
        
        # Extract text from screenshot
        screenshot_np = np.array(screenshot)
        text_results = reader.readtext(screenshot_np)
        detected_texts = [item[1] for item in text_results if len(item) > 1]

        currency_value = _extract_currency_from_texts(detected_texts)
        if currency_value is not None:
            return currency_value
        
        print(f"Currency value not found in region. OCR saw: {detected_texts}")
        return None
        
    except Exception as e:
        print(f"Error getting currency value: {e}")
        return None
