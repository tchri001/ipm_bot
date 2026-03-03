import keyboard
import json
import os
import shutil
import time
import sys
import atexit
import pyautogui
from utils import (
    open_bluestacks,
    zoom_to_max,
    zoom_out_configured_amount,
    open_resources_interface,
    find_template_match,
    get_currency_value_with_visualization,
    get_grid_midpoint,
    get_grid_region,
    log_input_event,
    set_zoom_modifier_key,
    save_reference_icon_anchor,
    align_screen_to_reference_icon,
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


def open_resources_tab():
    """Open and verify the resources tab."""
    resources_open = open_resources_interface(
        interface_search_start='M17',
        interface_search_end='V17',
        verify_search_start='S8',
        verify_search_end='V9',
        closed_icon_template='config/icons/tabs/resources_icon_closed.png',
        resource_window_template='config/icons/tabs/resource_window.png',
        click_confidence=0.75,
        verify_confidence=0.75,
        window_height_trim_ratio=0.2,
    )
    if resources_open:
        print("Resources interface check passed")
    else:
        print("Warning: resources interface check failed")
    return resources_open


def unlock_planet(
    start_search_cell,
    end_search_cell,
    planet,
    vertical_trim_ratio=0,
    horizontal_trim_ratio=0,
):
    planet_code = str(planet).strip().lower()
    template_path = f'config/icons/planets/locked/{planet_code}.png'

    search_region = get_grid_region(start_search_cell, end_search_cell)
    if search_region is None:
        print(f"Could not resolve planet search region: {start_search_cell} to {end_search_cell}")
        log_input_event(
            'planet_search',
            '',
            '',
            (
                f'planet={planet_code};template={template_path};region={start_search_cell}-{end_search_cell};'
                'status=region_error'
            )
        )
        return None

    x, y, width, height = search_region
    vertical_percent = max(0.0, min(49.0, float(vertical_trim_ratio)))
    horizontal_percent = max(0.0, min(49.0, float(horizontal_trim_ratio)))

    trim_y = int(height * (vertical_percent / 100.0))
    trim_x = int(width * (horizontal_percent / 100.0))
    trimmed_region = (
        x + trim_x,
        y + trim_y,
        max(1, width - (trim_x * 2)),
        max(1, height - (trim_y * 2)),
    )

    log_input_event(
        'planet_search',
        '',
        '',
        (
            f'planet={planet_code};template={template_path};region={start_search_cell}-{end_search_cell};'
            f'raw_region=x={x};y={y};w={width};h={height};'
            f'trimmed_region=x={trimmed_region[0]};y={trimmed_region[1]};w={trimmed_region[2]};h={trimmed_region[3]};'
            f'vertical_trim_percent={vertical_percent:.2f};horizontal_trim_percent={horizontal_percent:.2f};status=start'
        )
    )
    print(
        f"Searching for {planet_code} in {start_search_cell}-{end_search_cell} "
        f"with trim v={vertical_percent:.2f}% h={horizontal_percent:.2f}%"
    )

    detection = find_template_match(
        template_path=template_path,
        search_region=trimmed_region,
        confidence=0.75,
    )

    if detection is None:
        log_input_event(
            'planet_search',
            '',
            '',
            (
                f'planet={planet_code};template={template_path};region={start_search_cell}-{end_search_cell};'
                'status=not_found'
            )
        )
        print(f"Planet icon not found: {planet_code}")
        return None

    center_x = int(detection['center_x'])
    center_y = int(detection['center_y'])
    log_input_event(
        'planet_search',
        '',
        '',
        (
            f'planet={planet_code};template={template_path};region={start_search_cell}-{end_search_cell};'
            f'status=found;score={float(detection["score"]):.4f};center_x={center_x};center_y={center_y}'
        )
    )

    pyautogui.moveTo(center_x, center_y, duration=0.1)
    log_input_event('mouse_move', '', '', f'x={center_x};y={center_y};target={planet_code};phase=unlock_planet')
    pyautogui.click(center_x, center_y)
    log_input_event('mouse_click', '', '', f'x={center_x};y={center_y};button=left;target={planet_code};phase=unlock_planet')

    unlocked_template_path = f'config/icons/planets/unlocked/{planet_code}.png'
    time.sleep(0.25)
    unlocked_detection = find_template_match(
        template_path=unlocked_template_path,
        search_region=trimmed_region,
        confidence=0.75,
    )

    if unlocked_detection is not None:
        log_input_event(
            'planet_search',
            '',
            '',
            (
                f'planet={planet_code};template={unlocked_template_path};region={start_search_cell}-{end_search_cell};'
                f'status=unlocked_found;score={float(unlocked_detection["score"]):.4f};'
                f'center_x={int(unlocked_detection["center_x"])};center_y={int(unlocked_detection["center_y"])}'
            )
        )
        print(f"Found unlocked planet icon for {planet_code}")

        close_tab_region = get_grid_region('S6', 'V6')
        close_tab_template_path = 'config/icons/planets/stats/planet_tab.png'
        if close_tab_region is None:
            log_input_event(
                'planet_search',
                '',
                '',
                f'planet={planet_code};template={close_tab_template_path};status=close_tab_region_error;region=S6-V6'
            )
            print("Could not resolve close tab region S6-V6")
        else:
            close_tab_detection = find_template_match(
                template_path=close_tab_template_path,
                search_region=close_tab_region,
                confidence=0.75,
            )
            if close_tab_detection is not None:
                close_x = int(close_tab_detection['center_x'])
                close_y = int(close_tab_detection['center_y'])
                pyautogui.moveTo(close_x, close_y, duration=0.1)
                log_input_event('mouse_move', '', '', f'x={close_x};y={close_y};target=planet_tab;phase=unlock_planet_close_tab')
                pyautogui.click(close_x, close_y)
                log_input_event('mouse_click', '', '', f'x={close_x};y={close_y};button=left;target=planet_tab;phase=unlock_planet_close_tab')
                log_input_event(
                    'planet_search',
                    '',
                    '',
                    f'planet={planet_code};template={close_tab_template_path};status=planet_tab_closed;center_x={close_x};center_y={close_y}'
                )
                print(f"Closed planet tab for {planet_code}")
            else:
                log_input_event(
                    'planet_search',
                    '',
                    '',
                    f'planet={planet_code};template={close_tab_template_path};status=planet_tab_not_found;region=S6-V6'
                )
                print(f"Could not find planet tab close icon for {planet_code}")
    else:
        log_input_event(
            'planet_search',
            '',
            '',
            (
                f'planet={planet_code};template={unlocked_template_path};region={start_search_cell}-{end_search_cell};'
                'status=unlocked_not_found'
            )
        )
        print(f"Unlocked planet icon not found for {planet_code}")

    print(f"Clicked locked planet icon for {planet_code} at (x={center_x}, y={center_y})")
    return detection


def sell_ores(ore_name):
    ore_code = str(ore_name).strip().lower()
    template_path = f'config/icons/ores/{ore_code}.png'

    resources_open = open_resources_tab()
    if not resources_open:
        log_input_event(
            'ore_sell',
            '',
            '',
            f'ore={ore_code};template={template_path};status=resources_tab_not_open'
        )
        print(f"Could not open resources tab for ore sell: {ore_code}")
        return None

    ore_search_region = get_grid_region('M10', 'P15')
    if ore_search_region is None:
        log_input_event(
            'ore_sell',
            '',
            '',
            f'ore={ore_code};template={template_path};status=region_error;region=M10-P15'
        )
        print(f"Could not resolve ore search region for {ore_code}")
        return None

    log_input_event(
        'ore_sell',
        '',
        '',
        f'ore={ore_code};template={template_path};status=start;region=M10-P15'
    )
    detection = find_template_match(
        template_path=template_path,
        search_region=ore_search_region,
        confidence=0.75,
    )

    if detection is None:
        log_input_event(
            'ore_sell',
            '',
            '',
            f'ore={ore_code};template={template_path};status=not_found;region=M10-P15'
        )
        print(f"Ore icon not found: {ore_code}")
        return None

    center_x = int(detection['center_x'])
    center_y = int(detection['center_y'])
    pyautogui.moveTo(center_x, center_y, duration=0.1)
    log_input_event('mouse_move', '', '', f'x={center_x};y={center_y};target={ore_code};phase=sell_ores')

    pyautogui.mouseDown(x=center_x, y=center_y, button='left')
    log_input_event('mouse_down', '', '', f'x={center_x};y={center_y};button=left;target={ore_code};phase=sell_ores')
    time.sleep(1.5)
    pyautogui.mouseUp(x=center_x, y=center_y, button='left')
    log_input_event('mouse_up', '', '', f'x={center_x};y={center_y};button=left;target={ore_code};phase=sell_ores')

    autosell_region = get_grid_region('M15', 'P16')
    autosell_template_path = 'config/icons/ores/autosell.png'
    if autosell_region is None:
        log_input_event(
            'ore_sell',
            '',
            '',
            f'ore={ore_code};template={autosell_template_path};status=autosell_region_error;region=M15-P16'
        )
    else:
        autosell_detection = find_template_match(
            template_path=autosell_template_path,
            search_region=autosell_region,
            confidence=0.75,
        )
        if autosell_detection is not None:
            log_input_event(
                'ore_sell',
                '',
                '',
                (
                    f'ore={ore_code};template={autosell_template_path};status=autosell_confirmed;'
                    f'score={float(autosell_detection["score"]):.4f};'
                    f'center_x={int(autosell_detection["center_x"])};center_y={int(autosell_detection["center_y"])}'
                )
            )
            if ore_code == 'copper':
                print("Confirmed copper is autoselling")
            else:
                print(f"Confirmed {ore_code} is autoselling")
        else:
            log_input_event(
                'ore_sell',
                '',
                '',
                f'ore={ore_code};template={autosell_template_path};status=autosell_not_found;region=M15-P16'
            )
            print(f"Autosell icon not found for {ore_code}")

    log_input_event(
        'ore_sell',
        '',
        '',
        (
            f'ore={ore_code};template={template_path};status=hold_click_complete;'
            f'center_x={center_x};center_y={center_y};hold_seconds=1.5'
        )
    )

    close_tab_region = get_grid_region('M17', 'V17')
    close_tab_template_path = 'config/icons/tabs/resources_icon_open.png'
    if close_tab_region is None:
        log_input_event(
            'ore_sell',
            '',
            '',
            f'ore={ore_code};template={close_tab_template_path};status=close_tab_region_error;region=M17-V17'
        )
    else:
        close_tab_detection = find_template_match(
            template_path=close_tab_template_path,
            search_region=close_tab_region,
            confidence=0.75,
        )
        if close_tab_detection is not None:
            close_x = int(close_tab_detection['center_x'])
            close_y = int(close_tab_detection['center_y'])
            pyautogui.moveTo(close_x, close_y, duration=0.1)
            log_input_event('mouse_move', '', '', f'x={close_x};y={close_y};target=resources_icon_open;phase=sell_ores_close_tab')
            pyautogui.click(close_x, close_y)
            log_input_event('mouse_click', '', '', f'x={close_x};y={close_y};button=left;target=resources_icon_open;phase=sell_ores_close_tab')
            log_input_event(
                'ore_sell',
                '',
                '',
                (
                    f'ore={ore_code};template={close_tab_template_path};status=resources_window_closed;'
                    f'center_x={close_x};center_y={close_y}'
                )
            )
            print("Resources window closed")
        else:
            log_input_event(
                'ore_sell',
                '',
                '',
                f'ore={ore_code};template={close_tab_template_path};status=resources_open_icon_not_found;region=M17-V17'
            )
            print("Could not find resources open icon to close tab")

    print(f"Enabled auto-sell hold click for ore: {ore_code}")
    return detection


def stat_upgrade(planet, stat):
    planet_code = str(planet).strip().lower()
    stat_code = str(stat).strip().lower()
    valid_stats = {'mining_rate', 'ship_speed', 'cargo'}

    if stat_code not in valid_stats:
        message = f"invalid stat: {stat_code}"
        print(message)
        log_input_event('stat_upgrade', '', '', message)
        return False

    start_message = f"upgrading planet {planet_code}, stat {stat_code}"
    print(start_message)
    log_input_event('stat_upgrade', '', '', start_message)

    planet_template_path = f'config/icons/planets/unlocked/{planet_code}.png'
    planet_search_message = f"searching for planet {planet_code}"
    print(planet_search_message)
    log_input_event('stat_upgrade', '', '', planet_search_message)
    planet_detection = find_template_match(
        template_path=planet_template_path,
        search_region=None,
        confidence=0.75,
    )
    if planet_detection is None:
        not_found_message = f"planet not found: {planet_code}"
        print(not_found_message)
        log_input_event('stat_upgrade', '', '', not_found_message)
        return False

    found_open_message = f"searching for planet {planet_code}, found planet {planet_code}, opening planet {planet_code}"
    print(found_open_message)
    log_input_event('stat_upgrade', '', '', found_open_message)
    planet_x = int(planet_detection['center_x'])
    planet_y = int(planet_detection['center_y'])
    pyautogui.moveTo(planet_x, planet_y, duration=0.1)
    log_input_event('mouse_move', '', '', f'x={planet_x};y={planet_y};target={planet_code};phase=stat_upgrade_open_planet')
    pyautogui.click(planet_x, planet_y)
    log_input_event('mouse_click', '', '', f'x={planet_x};y={planet_y};button=left;target={planet_code};phase=stat_upgrade_open_planet')
    time.sleep(0.2)

    stat_template_path = f'config/icons/planets/stats/{stat_code}.png'
    stat_region = get_grid_region('N12', 'Q18')
    if stat_region is None:
        region_error_message = "could not resolve stat search region N12-Q18"
        print(region_error_message)
        log_input_event('stat_upgrade', '', '', region_error_message)
        return False

    stat_search_message = f"searching for stat {stat_code}"
    print(stat_search_message)
    log_input_event('stat_upgrade', '', '', stat_search_message)
    stat_detection = find_template_match(
        template_path=stat_template_path,
        search_region=stat_region,
        confidence=0.75,
    )
    if stat_detection is None:
        stat_not_found_message = f"stat not found: {stat_code}"
        print(stat_not_found_message)
        log_input_event('stat_upgrade', '', '', stat_not_found_message)
        return False

    stat_found_move_message = f"searching for stat {stat_code}, found stat {stat_code}, moving right 400px, moving down 100px"
    print(stat_found_move_message)
    log_input_event('stat_upgrade', '', '', stat_found_move_message)
    upgrade_x = int(stat_detection['center_x']) + 400
    upgrade_y = int(stat_detection['center_y']) + 60
    pyautogui.moveTo(upgrade_x, upgrade_y, duration=0.1)
    log_input_event('mouse_move', '', '', f'x={upgrade_x};y={upgrade_y};target={stat_code};phase=stat_upgrade_click_offset')
    pyautogui.click(upgrade_x, upgrade_y)
    log_input_event('mouse_click', '', '', f'x={upgrade_x};y={upgrade_y};button=left;target={stat_code};phase=stat_upgrade_click_offset')

    click_complete_message = "clicking 1 time, upgrade complete"
    print(click_complete_message)
    log_input_event('stat_upgrade', '', '', click_complete_message)

    close_message = "closing planet tab"
    print(close_message)
    log_input_event('stat_upgrade', '', '', close_message)
    close_tab_region = get_grid_region('S6', 'V6')
    close_tab_template_path = 'config/icons/planets/stats/planet_tab.png'
    if close_tab_region is None:
        close_region_error = "could not resolve close tab region S6-V6"
        print(close_region_error)
        log_input_event('stat_upgrade', '', '', close_region_error)
        return False

    close_tab_detection = find_template_match(
        template_path=close_tab_template_path,
        search_region=close_tab_region,
        confidence=0.75,
    )
    if close_tab_detection is None:
        close_not_found = "planet tab close icon not found"
        print(close_not_found)
        log_input_event('stat_upgrade', '', '', close_not_found)
        return False

    close_x = int(close_tab_detection['center_x'])
    close_y = int(close_tab_detection['center_y'])
    pyautogui.moveTo(close_x, close_y, duration=0.1)
    log_input_event('mouse_move', '', '', f'x={close_x};y={close_y};target=planet_tab;phase=stat_upgrade_close_tab')
    pyautogui.click(close_x, close_y)
    log_input_event('mouse_click', '', '', f'x={close_x};y={close_y};button=left;target=planet_tab;phase=stat_upgrade_close_tab')
    return True


def run_gameplay_loop(currency_region, galaxy_value_region, debug_dir_name):
    """
    Gameplay logic starts here.
    Setup/calibration should be completed before calling this function.
    """
    #unlock_planet("Q8","Q9","p1",20,0)
    #sell_ores("copper")
    #unlock_planet("R8","R8","p2",0,0)
    #sell_ores("iron")
    #open_resources_tab()
    #unlock_planet("R10","S11","p3",10,10)
    #unlock_planet("P11","Q11","p4",0,10)
    #sell_ores("lead")

    """
    planets = ["p1", "p2", "p3", "p4"]
    for planet in planets:
        stat_upgrade(planet, "mining_rate")
        stat_upgrade(planet, "ship_speed")
        stat_upgrade(planet, "cargo")
    """

    print(f"\nMonitoring currency every 5 seconds in region: {currency_region}")
    print("Press 'q' to exit.")
    print("Saving OCR crops to bot_v2/search_screenshots")

    next_check = 0.0
    while True:
        if keyboard.is_pressed('q'):
            print("Exiting program...")
            os._exit(0)

        now = time.time()
        if now >= next_check:
            currency = get_currency_value_with_visualization(
                region=currency_region,
                display=False,
                debug_dir=debug_dir_name,
                debug_filename='currency_region_latest.png',
            )
            if currency is not None:
                print(f"Cash: ${currency:,}")
            else:
                print("Cash: not detected")

            galaxy_value = get_currency_value_with_visualization(
                region=galaxy_value_region,
                display=False,
                debug_dir=debug_dir_name,
                debug_filename='galaxy_value_check.png',
            )
            if galaxy_value is not None:
                print(f"Galaxy value: ${galaxy_value:,}")
            else:
                print("Galaxy value: not detected")
            next_check = now + 5

        time.sleep(0.1)

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    game_log_path = os.path.join(base_dir, 'game_log.txt')
    setup_game_log(game_log_path)
    ref_config_path = os.path.join(base_dir, 'config', 'ipm_config.json')
    default_scroll_start_grid = "T9"
    default_currency_region_start_grid = "I1"
    default_currency_region_end_grid = "P2"
    enable_focus_click = True  # Toggle this on/off for pre-zoom focus click

    set_zoom_modifier_key('ctrl')
    print("Using zoom modifier key: ctrl")

    # Open/focus BlueStacks
    open_bluestacks()

    # Load startup grids from config and backfill keys if missing
    grid_target = default_scroll_start_grid
    currency_region_start_grid = default_currency_region_start_grid
    currency_region_end_grid = default_currency_region_end_grid
    try:
        if os.path.exists(ref_config_path):
            with open(ref_config_path, 'r', encoding='utf-8') as config_file:
                config_data = json.load(config_file)

            config_grid = str(config_data.get('scroll_start_grid', '')).strip().upper()
            if config_grid:
                grid_target = config_grid

            config_currency_start = str(config_data.get('currency_region_start_grid', '')).strip().upper()
            if config_currency_start:
                currency_region_start_grid = config_currency_start

            config_currency_end = str(config_data.get('currency_region_end_grid', '')).strip().upper()
            if config_currency_end:
                currency_region_end_grid = config_currency_end

            config_changed = False
            if 'scroll_start_grid' not in config_data:
                config_data['scroll_start_grid'] = default_scroll_start_grid
                config_changed = True
            if 'currency_region_start_grid' not in config_data:
                config_data['currency_region_start_grid'] = default_currency_region_start_grid
                config_changed = True
            if 'currency_region_end_grid' not in config_data:
                config_data['currency_region_end_grid'] = default_currency_region_end_grid
                config_changed = True

            if config_changed:
                with open(ref_config_path, 'w', encoding='utf-8') as config_file:
                    json.dump(config_data, config_file, indent=2)
    except Exception as e:
        print(f"Warning: could not load startup grids from config: {e}")

    print(f"Using scroll_start_grid: {grid_target}")
    print(f"Using currency region grid bounds: {currency_region_start_grid} -> {currency_region_end_grid}")

    # Move mouse to a grid location before any scrolling/zoom occurs
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

    # Zoom in before any reference-image detection/alignment.
    zoom_to_max()

    # Ensure reference icon anchor config exists (one-time calibration)
    if not os.path.exists(ref_config_path):
        print("Reference anchor config not found. Detecting ref_icon.png and saving anchor now...")
        anchor_saved = save_reference_icon_anchor(template_path='config/ref_icon.png', config_path='config/ipm_config.json', confidence=0.75)
        if anchor_saved is None:
            print("Warning: could not detect reference icon to save anchor coordinates.")

    # Startup alignment: drag map until reference icon is near saved coordinates
    alignment_ok = align_screen_to_reference_icon(config_path='config/ipm_config.json', tolerance_px=30, max_attempts=8)
    if not alignment_ok:
        print("Warning: reference alignment did not converge; continuing with current position.")

    # Reposition to grid target after alignment (dragging may move cursor elsewhere)
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

    # After max-zoom alignment, zoom out to the configured working level.
    zoom_out_configured_amount()

    # Currency monitor region from config bounds
    currency_region = get_grid_region(currency_region_start_grid, currency_region_end_grid)
    if currency_region is None:
        currency_region = (800, 0, 800, 200)
        print("Using fallback currency region (800, 0, 800, 200)")

    # Tighten region to focus on currency text only
    # Shrink by 50px on Y sides, keep full X range
    rx, ry, rw, rh = currency_region
    currency_region = (rx, ry + 50, rw, max(1, rh - 100))

    # Galaxy value region from M3-P4, trimmed by 5% left/right, 20% top, and 35% bottom
    galaxy_value_region = get_grid_region('M3', 'P4')
    if galaxy_value_region is None:
        galaxy_value_region = (1200, 200, 400, 200)
        print("Using fallback galaxy value region (1200, 200, 400, 200)")
    gx, gy, gw, gh = galaxy_value_region
    galaxy_trim_x = int(gw * 0.05)
    galaxy_trim_top = int(gh * 0.20)
    galaxy_trim_bottom = int(gh * 0.35)
    galaxy_value_region = (
        gx + galaxy_trim_x,
        gy + galaxy_trim_top,
        max(1, gw - (galaxy_trim_x * 2)),
        max(1, gh - galaxy_trim_top - galaxy_trim_bottom),
    )

    # Ensure debug screenshot folder exists.
    debug_dir_name = 'search_screenshots'
    debug_dir_path = os.path.join(base_dir, debug_dir_name)
    os.makedirs(debug_dir_path, exist_ok=True)

    run_gameplay_loop(
        currency_region=currency_region,
        galaxy_value_region=galaxy_value_region,
        debug_dir_name=debug_dir_name,
    )
