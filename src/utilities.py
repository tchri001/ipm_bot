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
