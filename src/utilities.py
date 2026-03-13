import json
import os
import threading
import time
import msvcrt
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import pyautogui


TARGET_WINDOW_TITLE = "BlueStacks App Player"


def _log_path() -> Path:
	return Path(__file__).resolve().parent.parent / "debugging" / "game_log.txt"


def initialize_game_log() -> None:
	"""Create a brand new game log for the current run."""
	path = _log_path()
	with path.open("w", encoding="utf-8") as handle:
		handle.write(f"[{datetime.now().isoformat(timespec='seconds')}] New run started.\n")


def write_game_log(message: str) -> None:
	"""Append a timestamped line to game_log.txt."""
	path = _log_path()
	with path.open("a", encoding="utf-8") as handle:
		handle.write(f"[{datetime.now().isoformat(timespec='seconds')}] {message}\n")


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


def _detect_content_bounds_from_mid_strip(bounds: dict[str, int]) -> tuple[int, int]:
	"""Detect non-black content bounds from a 10px strip at 50% window height."""
	strip_height = min(10, bounds["height"])
	if strip_height <= 0:
		raise RuntimeError("Window height is too small for black-band detection.")

	window_top = bounds["y"]
	window_bottom = bounds["y"] + bounds["height"]
	mid_y = bounds["y"] + int(bounds["height"] * 0.5)
	strip_y = max(window_top, min(mid_y - (strip_height // 2), window_bottom - strip_height))

	strip_image = pyautogui.screenshot(
		region=(bounds["x"], strip_y, bounds["width"], strip_height)
	).convert("RGB")
	pixels = strip_image.load()

	# Strict black detection so dark blue game art is not treated as black band.
	black_channel_max = 28
	black_brightness_max = 26
	black_ratio_threshold = 0.9

	column_is_black: list[bool] = []
	for x_index in range(bounds["width"]):
		black_pixel_count = 0
		for y_index in range(strip_height):
			r, g, b = pixels[x_index, y_index]
			avg = (r + g + b) / 3.0
			if r <= black_channel_max and g <= black_channel_max and b <= black_channel_max and avg <= black_brightness_max:
				black_pixel_count += 1
		black_ratio = black_pixel_count / float(strip_height)
		column_is_black.append(black_ratio >= black_ratio_threshold)

	min_run_length = 5
	left_content_x = None
	for x_index in range(0, bounds["width"] - min_run_length + 1):
		if all(not column_is_black[i] for i in range(x_index, x_index + min_run_length)):
			left_content_x = x_index
			break

	right_content_x = None
	for x_index in range(bounds["width"] - 1, min_run_length - 2, -1):
		if all(not column_is_black[i] for i in range(x_index - min_run_length + 1, x_index + 1)):
			right_content_x = x_index
			break

	if left_content_x is None or right_content_x is None or right_content_x <= left_content_x:
		raise RuntimeError("Could not detect portrait content bounds from midpoint strip.")

	write_game_log(
		"Mid-strip content bounds detected: "
		f"strip_y={strip_y}, black_channel_max={black_channel_max}, "
		f"black_brightness_max={black_brightness_max}, black_ratio_threshold={black_ratio_threshold:.2f}, "
		f"left={left_content_x}, right={right_content_x}"
	)
	return left_content_x, right_content_x


def open_and_focus_bluestacks_app_player() -> dict[str, int]:
	"""Focus existing BlueStacks App Player window and store bounds in config.json."""
	write_game_log("Starting BlueStacks App Player open/focus check.")
	window = _find_target_window()

	if window is None:
		write_game_log("BlueStacks App Player window not found.")
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
	time.sleep(10)
	write_game_log("Applied startup settle delay: 10s before location checks.")
	write_game_log(
		"Recorded initial window bounds: "
		f"x={bounds['x']}, y={bounds['y']}, width={bounds['width']}, height={bounds['height']}"
	)

	# Stage 1: Use bs_icon position in the top 5% strip to detect ad-banner state.
	assets_root = Path(__file__).resolve().parent.parent / "assets"
	bs_icon_path = assets_root / "reference" / "bs_icon.png"
	if not bs_icon_path.exists():
		raise FileNotFoundError(f"Reference icon not found: {bs_icon_path}")

	top_strip_height = max(1, int(bounds["height"] * 0.05))
	icon_match = pyautogui.locateOnScreen(
		str(bs_icon_path),
		confidence=0.65,
		region=(bounds["x"], bounds["y"], bounds["width"], top_strip_height),
	)
	if icon_match is None:
		write_game_log("Failed to detect bs_icon.png in top 5% strip.")
		raise RuntimeError("Could not find bs_icon.png in the top 5% of the game window.")

	icon_mid_x = int(icon_match.left + (icon_match.width / 2))
	icon_relative_x = icon_mid_x - bounds["x"]
	has_ad_banner = icon_relative_x > int(bounds["width"] * 0.2)
	write_game_log(f"Ad banner detected: {has_ad_banner}")

	# Stage 2: If banner exists, find the dark->light vertical transition on top 10px.
	if has_ad_banner:
		top_line_height = min(10, bounds["height"])
		top_line_image = pyautogui.screenshot(
			region=(bounds["x"], bounds["y"], bounds["width"], top_line_height)
		).convert("RGB")
		pixels = top_line_image.load()

		column_brightness: list[float] = []
		for x_index in range(bounds["width"]):
			column_sum = 0.0
			for y_index in range(top_line_height):
				r, g, b = pixels[x_index, y_index]
				column_sum += (r + g + b) / 3.0
			column_brightness.append(column_sum / float(top_line_height))

		banner_width = None
		for x_index in range(6, bounds["width"] - 12):
			before = sum(column_brightness[x_index - 6 : x_index]) / 6.0
			after = sum(column_brightness[x_index : x_index + 10]) / 10.0
			if (after - before) >= 12.0:
				banner_width = x_index
				break

		if banner_width is None:
			write_game_log("Failed to detect ad-banner boundary in top 10px color scan.")
			raise RuntimeError("Could not detect ad-banner boundary from top 10px color transition.")

		if banner_width >= bounds["width"]:
			write_game_log(f"Invalid detected ad-banner width: {banner_width}")
			raise RuntimeError("Detected ad-banner width is invalid.")

		old_x = bounds["x"]
		old_width = bounds["width"]
		bounds["x"] += int(banner_width)
		bounds["width"] -= int(banner_width)
		write_game_log(
			"Applied ad-banner adjustment: "
			f"banner_width={banner_width}, x {old_x}->{bounds['x']}, width {old_width}->{bounds['width']}"
		)
	else:
		write_game_log("No ad banner adjustment needed.")

	# Stage 3: Remove left/right black side bands by scanning a 10px strip at 50% height.
	content_left_x, content_right_x = _detect_content_bounds_from_mid_strip(bounds)
	left_black_band_width = int(content_left_x)
	right_black_band_width = int((bounds["width"] - 1) - content_right_x)
	old_x = bounds["x"]
	old_width = bounds["width"]
	bounds["x"] += left_black_band_width
	bounds["width"] = int(content_right_x - content_left_x + 1)
	write_game_log(
		"Applied black-band adjustment: "
		f"left_black={left_black_band_width}, right_black={right_black_band_width}, "
		f"x {old_x}->{bounds['x']}, width {old_width}->{bounds['width']}"
	)

	config = _load_config()
	config["game_window"] = bounds
	_save_config(config)
	write_game_log(
		"Saved final game_window bounds: "
		f"x={bounds['x']}, y={bounds['y']}, width={bounds['width']}, height={bounds['height']}"
	)

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
	search_image = pyautogui.screenshot(region=(region_x1, region_y1, region_width, region_height))
	searches_dir = Path(__file__).resolve().parent.parent / "debugging" / "image_searches"
	searches_dir.mkdir(parents=True, exist_ok=True)
	found = match is not None
	image_stem_for_file = Path(image_name).stem
	image_name_for_file = image_stem_for_file.replace("/", "_").replace("\\", "_")
	region_for_file = f"{region_x1}-{region_y1}-{region_width}-{region_height}"
	search_filename = f"{image_name_for_file}_{region_for_file}_{found}.png"
	search_image.save(searches_dir / search_filename)
	write_game_log(
		"image_search "
		f"image={image_name} "
		f"region=({region_x1},{region_y1},{region_width},{region_height}) "
		f"confidence={confidence} "
		f"found={found}"
	)
	if match is None:
		raise RuntimeError(f"Image not found in game window: {image_name}")

	mid_x = int(match.left + (match.width / 2))
	mid_y = int(match.top + (match.height / 2))
	return mid_x, mid_y
