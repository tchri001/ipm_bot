"""Draw a labeled grid overlay on the screen to identify regions.

This tool captures a static screenshot of the configured screen region,
draws a labeled grid on top, and displays it in a topmost window.

Usage:
    python overlay.py

Controls:
    - Press `q` to exit the overlay (global hotkey, works from any window).
    - Press `s` to save the grid image as `screen_grid.png`.
"""
import string
import os
import tkinter as tk
from PIL import ImageDraw, ImageTk
import pyautogui
import threading
import keyboard


MAIN_REGION = (0, 0, 2880, 1800)
MAIN_X, MAIN_Y, MAIN_WIDTH, MAIN_HEIGHT = MAIN_REGION


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


def create_grid_image(box_size=100):
    """Capture the current screen and draw grid overlay on it."""
    cols = MAIN_WIDTH // box_size
    rows = MAIN_HEIGHT // box_size
    
    # Capture actual screen
    screen = pyautogui.screenshot(region=MAIN_REGION)
    img = screen.convert('RGB')
    draw = ImageDraw.Draw(img)
    
    # Draw grid lines on top
    for r in range(rows):
        for c in range(cols):
            x1 = c * box_size
            y1 = r * box_size
            x2 = x1 + box_size - 1
            y2 = y1 + box_size - 1
            
            # Draw green outline
            draw.rectangle([x1, y1, x2, y2], outline=(0, 255, 0), width=2)
            
            # Label
            label = f"{col_label(c)}{r+1}"
            draw.text((x1 + 5, y1 + 5), label, fill=(255, 255, 255))
    
    return img, cols, rows


def save_grid_coords(box_size=100, filename='screen_grid_coords.txt'):
    """Write grid cell labels and top-left coordinates to a text file."""
    cols = MAIN_WIDTH // box_size
    rows = MAIN_HEIGHT // box_size

    output_path = filename if os.path.isabs(filename) else os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)

    with open(output_path, 'w', encoding='utf-8') as fh:
        for r in range(rows):
            for c in range(cols):
                label = f"{col_label(c)}{r+1}"
                x = MAIN_X + c * box_size
                y = MAIN_Y + r * box_size
                fh.write(f"{label}:x={x},y={y}\n")

    print(f"Saved grid coordinates to '{output_path}' ({cols} cols x {rows} rows)")


def main():
    box_size = 100
    
    # Setup stop event and save event
    stop_event = threading.Event()
    save_event = threading.Event()
    hotkey_q = keyboard.add_hotkey('q', lambda: stop_event.set())
    hotkey_s = keyboard.add_hotkey('s', lambda: save_event.set())
    
    print('Starting in 3 seconds — switch to target app now (press q to cancel)')
    if stop_event.wait(2):
        print('Startup cancelled with q')
        keyboard.remove_hotkey(hotkey_q)
        keyboard.remove_hotkey(hotkey_s)
        return
    
    # Create grid image
    img, cols, rows = create_grid_image(box_size=box_size)
    save_grid_coords(box_size=box_size, filename='screen_grid_coords.txt')
    
    w, h = img.size
    
    # Create tkinter window
    root = tk.Tk()
    root.geometry(f'{w}x{h}+0+0')
    root.overrideredirect(True)  # Remove window decorations (titlebar, borders)
    root.attributes('-topmost', True)  # Always on top
    
    # Convert PIL image to PhotoImage
    photo = ImageTk.PhotoImage(img)
    
    # Create label to display image
    label = tk.Label(root, image=photo)
    label.pack(fill=tk.BOTH, expand=True)
    label.image = photo  # Keep reference
    
    print("\nGrid overlay displayed. Press 'q' to exit, 's' to save screenshot.")
    
    # Main loop
    def check_exit():
        if save_event.is_set():
            output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'screen_grid.png')
            img.save(output_path)
            print(f"Saved screenshot to {output_path}")
            save_event.clear()
        
        if stop_event.is_set():
            root.quit()
        else:
            root.after(100, check_exit)
    
    check_exit()
    
    root.mainloop()
    
    keyboard.remove_hotkey(hotkey_q)
    keyboard.remove_hotkey(hotkey_s)
    print("Grid overlay closed.")


if __name__ == '__main__':
    main()
