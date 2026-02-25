"""Draw a labeled grid overlay on the screen to identify regions.

This version uses tkinter to create a true transparent, click-through overlay
that stays on top of other applications (including BlueStacks).

Usage:
    python boxer.py

Controls:
    - Press `q` to exit the overlay (global hotkey, works from any window).
    - Press `s` to save the grid image as `screen_grid.png`.
"""
import string
import tkinter as tk
from PIL import Image, ImageDraw, ImageTk
import pyautogui
import threading
import keyboard
import time
import ctypes


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
    """Create a transparent grid image with labels."""
    w, h = pyautogui.size()
    cols = w // box_size
    rows = h // box_size
    
    # Create transparent image (RGBA with alpha channel)
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw grid
    for r in range(rows):
        for c in range(cols):
            x1 = c * box_size
            y1 = r * box_size
            x2 = x1 + box_size - 1
            y2 = y1 + box_size - 1
            
            # Draw green outline
            draw.rectangle([x1, y1, x2, y2], outline=(0, 255, 0, 200), width=2)
            
            # Label
            label = f"{col_label(c)}{r+1}"
            draw.text((x1 + 5, y1 + 5), label, fill=(255, 255, 255, 255))
    
    return img, cols, rows


def save_grid_coords(box_size=100, filename='screen_grid_coords.txt'):
    """Write grid cell labels and top-left coordinates to a text file."""
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
    
    # Setup stop event
    stop_event = threading.Event()
    hotkey_id = keyboard.add_hotkey('q', lambda: stop_event.set())
    
    print('Starting in 3 seconds — switch to target app now (press q to cancel)')
    if stop_event.wait(3):
        print('Startup cancelled with q')
        keyboard.remove_hotkey(hotkey_id)
        return
    
    # Create grid image
    img, cols, rows = create_grid_image(box_size=box_size)
    save_grid_coords(box_size=box_size, filename='screen_grid_coords.txt')
    
    w, h = pyautogui.size()
    
    # Create tkinter window
    root = tk.Tk()
    root.geometry(f'{w}x{h}+0+0')
    root.overrideredirect(True)  # Remove window decorations (titlebar, borders)
    root.attributes('-topmost', True)  # Always on top
    
    # Convert PIL image to PhotoImage
    photo = ImageTk.PhotoImage(img)
    
    # Create label to display image (simpler than canvas for this use case)
    label = tk.Label(root, image=photo, bg='black')
    label.pack(fill=tk.BOTH, expand=True)
    label.image = photo  # Keep reference
    
    print("\nGrid overlay displayed. Press 'q' to exit.")
    
    # Main loop
    def check_exit():
        if stop_event.is_set():
            root.quit()
        else:
            root.after(100, check_exit)
    
    check_exit()
    
    root.mainloop()
    
    keyboard.remove_hotkey(hotkey_id)
    print("Grid overlay closed.")


if __name__ == '__main__':
    main()
