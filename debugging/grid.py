"""Overlay a labeled 10% grid on top of the configured game window.

Run from repo root:
	python debugging/grid.py

Close the overlay with Esc or by closing the window.
"""

from __future__ import annotations

import ctypes
from datetime import datetime
import json
from pathlib import Path
import tkinter as tk

from PIL import ImageGrab


def load_game_window_bounds(config_path: Path) -> tuple[int, int, int, int]:
	"""Load (x, y, width, height) from src/config.json."""
	with config_path.open("r", encoding="utf-8") as f:
		config = json.load(f)

	window = config["game_window"]
	x = int(window["x"])
	y = int(window["y"])
	width = int(window["width"])
	height = int(window["height"])

	if width <= 0 or height <= 0:
		raise ValueError("game_window width and height must be positive")

	return x, y, width, height


def draw_grid(canvas: tk.Canvas, width: int, height: int) -> None:
	"""Draw 10% grid lines with axis labels on top row and first column."""
	line_color = "#00FF7F"
	text_color = "#FFFFFF"

	# Border
	canvas.create_rectangle(0, 0, width - 1, height - 1, outline=line_color, width=2)

	# Axis lines at 10%, 20%, ..., 100%
	for p in range(10, 101, 10):
		x = round(width * p / 100)
		y = round(height * p / 100)

		if 0 < x < width:
			canvas.create_line(x, 0, x, height, fill=line_color, width=1)

		if 0 < y < height:
			canvas.create_line(0, y, width, y, fill=line_color, width=1)

	# Top-row x-axis labels: x: 0-10%, x: 10-20%, ...
	for col in range(10):
		x0 = round(width * col / 10)
		x1 = round(width * (col + 1) / 10)
		xc = (x0 + x1) // 2
		canvas.create_text(
			xc,
			4,
			text=f"x: {col * 10}-{(col + 1) * 10}%",
			fill=text_color,
			anchor="n",
			font=("Consolas", 6, "bold"),
		)

	# First-column y-axis labels: y: 0-10%, y: 10-20%, ...
	for row in range(10):
		y0 = round(height * row / 10)
		y1 = round(height * (row + 1) / 10)
		yc = (y0 + y1) // 2
		canvas.create_text(
			4,
			yc,
			text=f"y: {row * 10}-{(row + 1) * 10}%",
			fill=text_color,
			anchor="w",
			font=("Consolas", 6, "bold"),
		)


def main() -> None:
	repo_root = Path(__file__).resolve().parents[1]
	config_path = repo_root / "src" / "config.json"
	screenshot_dir = repo_root / "debugging" 
	screenshot_dir.mkdir(parents=True, exist_ok=True)

	config_x, config_y, config_width, config_height = load_game_window_bounds(config_path)
	overlay_x = config_x // 2
	overlay_y = config_y // 2
	width = config_width // 2
	height = config_height // 2

	root = tk.Tk()
	root.overrideredirect(True)
	root.attributes("-topmost", True)
	root.attributes("-alpha", 0.45)
	root.geometry(f"{width}x{height}+{overlay_x}+{overlay_y}")

	canvas = tk.Canvas(root, width=width, height=height, bg="black", highlightthickness=0)
	canvas.pack(fill="both", expand=True)

	draw_grid(canvas, width, height)

	def quit_overlay(_event: tk.Event | None = None) -> None:
		root.destroy()

	def save_overlay_screenshot(_event: tk.Event | None = None) -> None:
		# Capture the configured game-window rectangle including the visible overlay.
		timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
		out_path = screenshot_dir / f"grid_overlay_{timestamp}.png"
		bbox = (overlay_x, overlay_y, overlay_x + width, overlay_y + height)
		image = ImageGrab.grab(bbox=bbox)
		image.save(out_path)
		print(f"Saved overlay screenshot: {out_path}")

	def on_key_press(event: tk.Event) -> None:
		key = (event.keysym or "").lower()
		if key in {"q", "escape"}:
			quit_overlay()
		elif key == "s":
			save_overlay_screenshot()

	# Fallback for borderless windows: poll global key state on Windows.
	vk_escape = 0x1B
	vk_q = 0x51
	vk_s = 0x53
	last_pressed = {vk_escape: False, vk_q: False, vk_s: False}

	def poll_global_keys() -> None:
		for vk in (vk_escape, vk_q, vk_s):
			is_pressed = bool(ctypes.windll.user32.GetAsyncKeyState(vk) & 0x8000)
			if is_pressed and not last_pressed[vk]:
				if vk in (vk_escape, vk_q):
					quit_overlay()
					return
				if vk == vk_s:
					save_overlay_screenshot()
			last_pressed[vk] = is_pressed
		root.after(35, poll_global_keys)

	root.bind_all("<Escape>", quit_overlay)
	root.bind_all("<KeyPress-q>", quit_overlay)
	root.bind_all("<KeyPress-Q>", quit_overlay)
	root.bind_all("<KeyPress-s>", save_overlay_screenshot)
	root.bind_all("<KeyPress-S>", save_overlay_screenshot)
	root.bind("<KeyPress>", on_key_press)
	canvas.bind("<KeyPress>", on_key_press)
	root.bind("<Button-3>", quit_overlay)
	canvas.bind("<Button-3>", quit_overlay)

	# Ensure key bindings work immediately after launch.
	root.after(10, root.focus_force)
	root.after(20, canvas.focus_set)
	poll_global_keys()
	root.mainloop()


if __name__ == "__main__":
	main()
