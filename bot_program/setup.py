import os
import sys
import atexit

import pyautogui

from utils import (
    align_screen_to_reference_icon,
    get_grid_midpoint,
    log_input_event,
    open_bluestacks,
    save_reference_icon_anchor,
    set_zoom_modifier_key,
    zoom_out_configured_amount,
    zoom_to_max,
)


class _StreamTee:
    def __init__(self, *streams):
        self._streams = streams

    def write(self, data):
        for stream in self._streams:
            stream.write(data)
        return len(data)

    def flush(self):
        for stream in self._streams:
            stream.flush()


def setup_game_log(log_path):
    log_file = open(log_path, 'a', encoding='utf-8', buffering=1)
    sys.stdout = _StreamTee(sys.__stdout__, log_file)
    sys.stderr = _StreamTee(sys.__stderr__, log_file)

    def _close_log_file():
        try:
            log_file.flush()
            log_file.close()
        except OSError:
            pass

    atexit.register(_close_log_file)
    print(f"Logging console output to: {log_path}")


def game_window_setup(base_dir, runtime_config, run_setup=True):
    ref_config_path = runtime_config['ref_config_path']
    grid_target = runtime_config['grid_target']
    currency_region_start_grid = runtime_config['currency_region_start_grid']
    currency_region_end_grid = runtime_config['currency_region_end_grid']
    enable_focus_click = bool(runtime_config.get('enable_focus_click', True))

    set_zoom_modifier_key('ctrl')
    print("Using zoom modifier key: ctrl")

    print(f"Using scroll_start_grid: {grid_target}")
    print(f"Using currency region grid bounds: {currency_region_start_grid} -> {currency_region_end_grid}")

    if run_setup:
        open_bluestacks()

        coords = get_grid_midpoint(grid_target)
        if coords:
            x, y = coords
            try:
                pyautogui.moveTo(x, y, duration=0.2)
                print(f"Moved mouse to {grid_target} (x={x}, y={y})")
                log_input_event('mouse_move', '', '', f'x={x};y={y};phase=pre_zoom_initial_focus')
                if enable_focus_click:
                    pyautogui.click()
                    print("Clicked to focus window before zoom")
                    log_input_event('mouse_click', '', '', f'x={x};y={y};button=left;phase=pre_zoom_initial_focus')
                else:
                    print("Focus click disabled (enable_focus_click=False)")
            except Exception as e:
                print(f"Could not move mouse: {e}")
        else:
            print(f"Could not find grid coordinates for {grid_target}")

        zoom_to_max()

        if not os.path.exists(ref_config_path):
            print("Reference anchor config not found. Detecting ref_icon.png and saving anchor now...")
            anchor_saved = save_reference_icon_anchor(
                template_path='config/ref_icon.png',
                config_path='config/ipm_config.json',
                confidence=0.75,
            )
            if anchor_saved is None:
                print("Warning: could not detect reference icon to save anchor coordinates.")

        alignment_ok = align_screen_to_reference_icon(
            config_path='config/ipm_config.json',
            tolerance_px=30,
            max_attempts=8,
        )
        if not alignment_ok:
            print("Warning: reference alignment did not converge; continuing with current position.")

        coords = get_grid_midpoint(grid_target)
        if coords:
            x, y = coords
            try:
                pyautogui.moveTo(x, y, duration=0.2)
                print(f"Repositioned mouse to {grid_target} before zoom (x={x}, y={y})")
                log_input_event('mouse_move', '', '', f'x={x};y={y};phase=pre_zoom_reposition')
                if enable_focus_click:
                    pyautogui.click()
                    print("Clicked to focus window before zoom (post-alignment)")
                    log_input_event('mouse_click', '', '', f'x={x};y={y};button=left;phase=pre_zoom_reposition')
            except Exception as e:
                print(f"Could not reposition mouse before zoom: {e}")

        zoom_out_configured_amount()
    else:
        print("Skipping game window setup actions (run_window_setup=False)")

    return None
