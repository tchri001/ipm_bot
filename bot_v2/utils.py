import subprocess
import os
import pygetwindow as gw
import time
import pyautogui


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
