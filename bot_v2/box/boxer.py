"""Draw a labeled grid overlay on the screen to identify regions.

Usage:
    python boxer.py

Controls:
    - Press `q` or `Esc` to exit the overlay window.
    - Press `s` to save the overlay image as `screen_grid.png` in the current folder.

The script captures the current screen, divides it into 100x100 pixel boxes,
labels columns with letters (A, B, ..., Z, AA, AB, ...) and rows with numbers
(1, 2, 3, ...). It displays a semi-transparent overlay so you can see the
underlying application while identifying grid coordinates.
"""
import string
import cv2
import numpy as np
import pyautogui
import time
import threading
import keyboard


def col_label(idx: int) -> str:
    """Return Excel-style column label for zero-based index (0 -> A, 25 -> Z, 26 -> AA)."""
    label = []
    i = idx
    while True:
        i, rem = divmod(i, 26)
        label.append(string.ascii_uppercase[rem])
        if i == 0:
            break
        i -= 1
    return ''.join(reversed(label))


def build_grid_overlay(box_size=100, alpha=0.35, font_scale=0.7, thickness=2):
    # Capture current screen
    screen = pyautogui.screenshot()
    screen_np = cv2.cvtColor(np.array(screen), cv2.COLOR_RGB2BGR)
    h, w = screen_np.shape[:2]

    cols = w // box_size
    rows = h // box_size

    overlay = screen_np.copy()

    # Draw semi-transparent boxes and labels
    for r in range(rows):
        for c in range(cols):
            x1 = c * box_size
            y1 = r * box_size
            x2 = x1 + box_size - 1
            y2 = y1 + box_size - 1

            # Outline rectangle (no fill)
            color = (0, 255, 0)  # Green
            cv2.rectangle(overlay, (x1, y1), (x2, y2), color, thickness)

            # Label text: columns as letters, rows as numbers
            label = f"{col_label(c)}{r+1}"

            # Calculate text size and position
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
            tx = x1 + 5
            ty = y1 + th + 5

            # Draw background for text for readability
            cv2.rectangle(overlay, (tx - 2, ty - th - 2), (tx + tw + 2, ty + 2), (0, 0, 0), -1)
            cv2.putText(overlay, label, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), thickness)

    # Blend overlay onto screen
    blended = cv2.addWeighted(overlay, alpha, screen_np, 1 - alpha, 0)
    return blended


def save_grid_coords(box_size=100, filename='screen_grid_coords.txt'):
    """Write grid cell labels and top-left coordinates to a text file.

    Format per line: <Label>:x=<x>,y=<y>
    Example: A1:x=0,y=0
    """
    w, h = pyautogui.size()
    cols = w // box_size
    rows = h // box_size

    with open(filename, 'w', encoding='utf-8') as fh:
        for r in range(rows):
            for c in range(cols):
                label = f"{col_label(c)}{r+1}"
                x = c * box_size
                y = r * box_size
                fh.write(f"{label}:x={x},y={y}\n")

    print(f"Saved grid coordinates to '{filename}' ({cols} cols x {rows} rows)")


def main():
    box_size = 100
    alpha = 0.35
    # Allow user time to switch to the target app
    stop_event = threading.Event()
    # Register a global hotkey 'q' to stop from any window
    hotkey_id = keyboard.add_hotkey('q', lambda: stop_event.set())

    print('Starting in 5 seconds — switch to target app now (press q to cancel)')
    # Wait up to 5 seconds, but exit early if 'q' pressed
    if stop_event.wait(5):
        print('Startup cancelled with q')
        keyboard.remove_hotkey(hotkey_id)
        return

    img = build_grid_overlay(box_size=box_size, alpha=alpha)
    # Save coordinate mapping so you can reference labels programmatically
    save_grid_coords(box_size=box_size, filename='screen_grid_coords.txt')

    window_name = 'Screen Grid (press q/Esc to quit, s to save)'
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    # Main display loop — non-blocking wait so we can respond to global hotkey
    while not stop_event.is_set():
        cv2.imshow(window_name, img)
        key = cv2.waitKey(100) & 0xFF
        if key in (ord('q'), 27):  # q or Esc pressed while window focused
            stop_event.set()
            break
        if key == ord('s'):
            cv2.imwrite('screen_grid.png', img)
            print('Saved screen_grid.png')

    keyboard.remove_hotkey(hotkey_id)
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
