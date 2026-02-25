import subprocess
import os
import pygetwindow as gw
import time
import pyautogui
import easyocr
import re


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


def press_f11():
    """
    Presses the F11 key to enter fullscreen mode in BlueStacks.
    """
    time.sleep(1)  # Wait for BlueStacks to be ready
    pyautogui.press('f11')
    print("F11 pressed")


def zoom_to_max_then_down_one():
    """
    Zooms in to maximum by scrolling up 5 times with Ctrl held,
    then zooms out by 1 level by scrolling down 1 time with Ctrl held.
    """
    time.sleep(5)  # Wait for BlueStacks to be fully loaded after F11
    
    # Zoom in to maximum (scroll up 5 times with Ctrl)
    for i in range(5):
        pyautogui.keyDown('ctrl')
        pyautogui.scroll(150)  # Scroll up (positive value)
        pyautogui.keyUp('ctrl')
        time.sleep(0.2)  # Small delay between scrolls
    print("Zoomed in to maximum")
    
    time.sleep(0.5)
    
    # Zoom out by 1 level (scroll down 1 time with Ctrl)
    for i in range(5):
        pyautogui.keyDown('ctrl')
        pyautogui.scroll(-20)  # Scroll down (negative value)
        pyautogui.keyUp('ctrl')
        time.sleep(0.2)  # Small delay between scrolls
    print("Zoomed out by 1 level")


def setup_bluestacks():
    """
    Complete setup sequence for BlueStacks:
    1. Opens/focuses BlueStacks
    2. Presses F11 for fullscreen
    3. Zooms in to maximum then out by 1 level
    """
    print("Starting BlueStacks setup...")
    open_bluestacks()
    press_f11()
    zoom_to_max_then_down_one()
    print("BlueStacks setup complete!")


def get_currency_value_with_visualization(region=(0, 0, 1920, 150), display=True):
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
        
        # Initialize OCR reader (first use downloads the model ~200MB)
        print("Initializing OCR reader (this may take a moment on first run)...")
        reader = easyocr.Reader(['en'])
        
        # Extract text from screenshot
        text_results = reader.readtext(screenshot)
        
        # Look for $ symbol and extract currency value
        for detection in text_results:
            detected_text = detection[1].upper()
            if '$' in detected_text:
                # Extract number after $
                parts = detected_text.split('$')
                if len(parts) > 1:
                    currency_str = parts[1].strip().replace(',', '')
                    try:
                        # Try to extract just the number part
                        numbers = re.findall(r'\d+', currency_str)
                        if numbers:
                            return int(numbers[0])
                    except:
                        pass
        
        print("Currency value not found in region")
        return None
        
    except Exception as e:
        print(f"Error getting currency value: {e}")
        return None
