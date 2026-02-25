import subprocess
import os
import json
import pygetwindow as gw
import time
import pyautogui
import easyocr
import re
import numpy as np
import cv2
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


def _resolve_local_path(path_value):
    """Resolve relative paths against this file's directory."""
    if os.path.isabs(path_value):
        return path_value
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), path_value)


def set_zoom_modifier_key(key_name):
    """Set the key used as zoom modifier for scroll shortcuts (pyautogui key name)."""
    global _ZOOM_MODIFIER_KEY
    if key_name:
        _ZOOM_MODIFIER_KEY = key_name


def _get_zoom_scroll_amounts(config_path='ipm_config.json'):
    """Load zoom scroll amounts from config with safe defaults."""
    scroll_up_amount = 100
    scroll_down_amount = -30
    try:
        config_full_path = _resolve_local_path(config_path)
        if os.path.exists(config_full_path):
            with open(config_full_path, 'r', encoding='utf-8') as config_file:
                config = json.load(config_file)
            scroll_up_amount = int(config.get('scroll_up_amount', scroll_up_amount))
            scroll_down_amount = int(config.get('scroll_down_amount', scroll_down_amount))
    except Exception as e:
        print(f"Warning: could not read zoom scroll amounts from config: {e}")

    return scroll_up_amount, scroll_down_amount


def find_reference_icon(template_path='ref_icon.png', search_region=None, confidence=0.75):
    """
    Find the reference icon on screen using template matching.

    Returns dict with center and match score, or None if not found.
    """
    try:
        template_full_path = _resolve_local_path(template_path)
        template_img = cv2.imread(template_full_path, cv2.IMREAD_GRAYSCALE)
        if template_img is None:
            print(f"Reference icon not found or unreadable: {template_full_path}")
            return None

        screenshot = pyautogui.screenshot(region=search_region)
        screenshot_np = np.array(screenshot)
        screenshot_gray = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2GRAY)

        result = cv2.matchTemplate(screenshot_gray, template_img, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        if max_val < confidence:
            return None

        template_h, template_w = template_img.shape
        center_x = max_loc[0] + (template_w // 2)
        center_y = max_loc[1] + (template_h // 2)

        if search_region is not None:
            region_x, region_y, _, _ = search_region
            center_x += region_x
            center_y += region_y

        return {
            'center_x': int(center_x),
            'center_y': int(center_y),
            'score': float(max_val),
            'template_w': int(template_w),
            'template_h': int(template_h),
        }
    except Exception as e:
        print(f"Error finding reference icon: {e}")
        return None


def save_reference_icon_anchor(template_path='ref_icon.png', config_path='ipm_config.json', confidence=0.75):
    """
    Detect current reference icon position and save as startup anchor coordinates.
    """
    detection = find_reference_icon(template_path=template_path, confidence=confidence)
    if not detection:
        return None

    config_full_path = _resolve_local_path(config_path)
    existing_scroll_start_grid = 'T9'
    existing_currency_region_start_grid = 'I1'
    existing_currency_region_end_grid = 'P2'
    existing_scroll_up_amount = 100
    existing_scroll_down_amount = -30
    if os.path.exists(config_full_path):
        try:
            with open(config_full_path, 'r', encoding='utf-8') as existing_config_file:
                existing_config = json.load(existing_config_file)
            existing_scroll_start_grid = str(existing_config.get('scroll_start_grid', 'T9')).strip().upper() or 'T9'
            existing_currency_region_start_grid = str(existing_config.get('currency_region_start_grid', 'I1')).strip().upper() or 'I1'
            existing_currency_region_end_grid = str(existing_config.get('currency_region_end_grid', 'P2')).strip().upper() or 'P2'
            existing_scroll_up_amount = int(existing_config.get('scroll_up_amount', 100))
            existing_scroll_down_amount = int(existing_config.get('scroll_down_amount', -30))
        except Exception:
            existing_scroll_start_grid = 'T9'
            existing_currency_region_start_grid = 'I1'
            existing_currency_region_end_grid = 'P2'
            existing_scroll_up_amount = 100
            existing_scroll_down_amount = -30

    payload = {
        'template_path': template_path,
        'target_x': detection['center_x'],
        'target_y': detection['center_y'],
        'scroll_start_grid': existing_scroll_start_grid,
        'currency_region_start_grid': existing_currency_region_start_grid,
        'currency_region_end_grid': existing_currency_region_end_grid,
        'scroll_up_amount': existing_scroll_up_amount,
        'scroll_down_amount': existing_scroll_down_amount,
        'tolerance_px': 30,
        'confidence': confidence,
        'saved_at': datetime.now().isoformat(),
    }
    with open(config_full_path, 'w', encoding='utf-8') as config_file:
        json.dump(payload, config_file, indent=2)

    print(f"Saved reference icon anchor: ({payload['target_x']}, {payload['target_y']}) -> {config_full_path}")
    return payload


def align_screen_to_reference_icon(config_path='ipm_config.json', tolerance_px=30, max_attempts=8):
    """
    Align the map by dragging until the reference icon is within tolerance.
    """
    try:
        config_full_path = _resolve_local_path(config_path)
        if not os.path.exists(config_full_path):
            print(f"Reference config not found: {config_full_path}")
            return False

        with open(config_full_path, 'r', encoding='utf-8') as config_file:
            config = json.load(config_file)

        template_path = config.get('template_path', 'ref_icon.png')
        target_x = int(config['target_x'])
        target_y = int(config['target_y'])

        for attempt in range(1, max_attempts + 1):
            detection = find_reference_icon(template_path=template_path, confidence=float(config.get('confidence', 0.75)))
            if not detection:
                print(f"Reference icon not found on attempt {attempt}/{max_attempts}")
                return False

            current_x = detection['center_x']
            current_y = detection['center_y']
            dx = target_x - current_x
            dy = target_y - current_y

            if abs(dx) <= tolerance_px and abs(dy) <= tolerance_px:
                print(f"Reference aligned within tolerance ({tolerance_px}px): dx={dx}, dy={dy}")
                return True

            # Use slow, small drags to avoid BlueStacks momentum after release.
            # Apply only a fraction of the remaining offset each attempt.
            step_dx = int(max(-80, min(80, dx * 0.5)))
            step_dy = int(max(-60, min(60, dy * 0.5)))

            # Ensure we still move when non-zero offset exists
            if step_dx == 0 and dx != 0:
                step_dx = 1 if dx > 0 else -1
            if step_dy == 0 and dy != 0:
                step_dy = 1 if dy > 0 else -1

            pyautogui.moveTo(current_x, current_y, duration=0.12)

            # Break movement into tiny chunks to minimize inertia.
            chunk_count = max(1, max(abs(step_dx) // 20, abs(step_dy) // 20))
            chunk_dx = step_dx / chunk_count
            chunk_dy = step_dy / chunk_count

            # Explicitly hold mouse during drag to avoid intermittent release.
            pyautogui.mouseDown(button='left')
            log_input_event('mouse_down', '', '', f'x={current_x};y={current_y};attempt={attempt}')
            try:
                for chunk_index in range(chunk_count):
                    this_dx = int(round(chunk_dx))
                    this_dy = int(round(chunk_dy))
                    if this_dx == 0 and step_dx != 0:
                        this_dx = 1 if step_dx > 0 else -1
                    if this_dy == 0 and step_dy != 0:
                        this_dy = 1 if step_dy > 0 else -1

                    pyautogui.moveRel(this_dx, this_dy, duration=0.18)
                    log_input_event(
                        'mouse_drag',
                        '',
                        '',
                        f'start_x={current_x};start_y={current_y};dx={this_dx};dy={this_dy};attempt={attempt};chunk={chunk_index+1}/{chunk_count}'
                    )
                    time.sleep(0.08)
            finally:
                pyautogui.mouseUp(button='left')
                log_input_event('mouse_up', '', '', f'attempt={attempt}')

            # Allow post-drag momentum to settle before re-detection.
            time.sleep(0.45)

        print(f"Could not align within {max_attempts} attempts")
        return False
    except Exception as e:
        print(f"Error aligning to reference icon: {e}")
        return False


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


def get_grid_midpoint(grid_code, coords_file='grid/screen_grid_coords.txt', box_size=100):
    """
    Read a grid code (e.g., 'O15') and return the midpoint coordinates of that cell.
    
    Args:
        grid_code: Grid cell code (e.g., 'O15')
        coords_file: Path to grid/screen_grid_coords.txt
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


def get_grid_region(top_left_code, bottom_right_code, coords_file='grid/screen_grid_coords.txt', box_size=100):
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


def zoom_to_max_then_down_one():
    """
    Zoom sequence:
    1) Hold modifier and scroll up 5 times
    2) Hold modifier and scroll down 5 times
    """
    scroll_up_amount, scroll_down_amount = _get_zoom_scroll_amounts(config_path='ipm_config.json')
    time.sleep(2)  # Wait for BlueStacks to be ready before zoom input
    
    # Zoom in to maximum (hold Ctrl, scroll up 5 times, then release Ctrl)
    pyautogui.keyDown(_ZOOM_MODIFIER_KEY)
    time.sleep(0.4)
    for i in range(5):
        pyautogui.scroll(scroll_up_amount)
        log_input_event('mouse_scroll', '', '', f'amount={scroll_up_amount};zoom_in_iter={i+1}')
        time.sleep(0.1)
    pyautogui.keyUp(_ZOOM_MODIFIER_KEY)
    time.sleep(0.4)
    print("Zoomed in to maximum")
    
    time.sleep(0.5)
    
    # Zoom out by a set amount (hold Ctrl, scroll down 5 times, then release Ctrl)
    pyautogui.keyDown(_ZOOM_MODIFIER_KEY)
    time.sleep(0.4)
    for i in range(5):
        pyautogui.scroll(scroll_down_amount)
        log_input_event('mouse_scroll', '', '', f'amount={scroll_down_amount};zoom_out_iter={i+1}')
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
