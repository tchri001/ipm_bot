import json
import os
import threading
import time
import msvcrt
from pathlib import Path
from typing import Any, Optional

import pyautogui


TARGET_WINDOW_TITLE = "BlueStacks App Player"


def _quit_on_q_loop() -> None:
	while True:
		if msvcrt.kbhit():
			key = msvcrt.getwch()
			if key.lower() == "q":
				os._exit(0)
		time.sleep(0.1)


def start_quit_listener_thread() -> threading.Thread:
	"""Start a background listener that terminates the program when q is pressed."""
	listener_thread = threading.Thread(target=_quit_on_q_loop, daemon=True)
	listener_thread.start()
	return listener_thread


def _config_path() -> Path:
	return Path(__file__).with_name("config.json")


def _load_config() -> dict[str, Any]:
	path = _config_path()
	if not path.exists():
		return {}

	try:
		with path.open("r", encoding="utf-8") as handle:
			loaded = json.load(handle)
		return loaded if isinstance(loaded, dict) else {}
	except (OSError, json.JSONDecodeError):
		return {}


def _save_config(config: dict[str, Any]) -> None:
	path = _config_path()
	with path.open("w", encoding="utf-8") as handle:
		json.dump(config, handle, indent=2)


def _find_target_window() -> Optional[Any]:
	windows = pyautogui.getWindowsWithTitle(TARGET_WINDOW_TITLE)
	return windows[0] if windows else None


def open_and_focus_bluestacks_app_player() -> dict[str, int]:
	"""Focus existing BlueStacks App Player window and store bounds in config.json."""
	window = _find_target_window()

	if window is None:
		raise RuntimeError("BlueStacks App Player window was not found.")

	try:
		if getattr(window, "isMinimized", False):
			window.restore()
		window.activate()
	except Exception:
		# Continue even if focus call is blocked by OS windowing rules.
		pass

	bounds = {
		"x": int(window.left),
		"y": int(window.top),
		"width": int(window.width),
		"height": int(window.height),
	}

	config = _load_config()
	config["game_window"] = bounds
	_save_config(config)

	return bounds


def find_image_in_game_window(
	image_name: str,
	confidence: float = 0.75,
	x_start: float = 0,
	x_end: float = 100,
	y_start: float = 0,
	y_end: float = 100,
) -> tuple[int, int]:
	"""Find an image within the configured game window and return image midpoint coordinates."""
	for value_name, value in {
		"x_start": x_start,
		"x_end": x_end,
		"y_start": y_start,
		"y_end": y_end,
	}.items():
		if value < 0 or value > 100:
			raise ValueError(f"{value_name} must be between 0 and 100.")

	if x_start >= x_end:
		raise ValueError("x_start must be less than x_end.")
	if y_start >= y_end:
		raise ValueError("y_start must be less than y_end.")

	config = _load_config()
	window = config.get("game_window")
	if not isinstance(window, dict):
		raise RuntimeError("game_window is missing from config.json.")

	try:
		window_x = int(window["x"])
		window_y = int(window["y"])
		window_width = int(window["width"])
		window_height = int(window["height"])
	except (KeyError, TypeError, ValueError) as exc:
		raise RuntimeError("game_window values are missing or invalid in config.json.") from exc

	region_x1 = window_x + int(window_width * (x_start / 100.0))
	region_x2 = window_x + int(window_width * (x_end / 100.0))
	region_y1 = window_y + int(window_height * (y_start / 100.0))
	region_y2 = window_y + int(window_height * (y_end / 100.0))

	region_width = region_x2 - region_x1
	region_height = region_y2 - region_y1
	if region_width <= 0 or region_height <= 0:
		raise ValueError("Calculated search region is empty.")

	assets_root = Path(__file__).resolve().parent.parent / "assets"
	image_path = assets_root / image_name
	if not image_path.exists():
		raise FileNotFoundError(f"Image not found: {image_path}")

	match = pyautogui.locateOnScreen(
		str(image_path),
		confidence=confidence,
		region=(region_x1, region_y1, region_width, region_height),
	)
	if match is None:
		raise RuntimeError(f"Image not found in game window: {image_name}")

	mid_x = int(match.left + (match.width / 2))
	mid_y = int(match.top + (match.height / 2))
	return mid_x, mid_y
