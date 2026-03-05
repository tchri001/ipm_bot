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
    find_template_match_brightness,
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


def open_resources_tab(interface_search_start, interface_search_end):
    """Open and verify the resources tab."""
    resources_open = open_resources_interface(
        interface_search_start=interface_search_start,
        interface_search_end=interface_search_end,
        verify_search_start='S8',
        verify_search_end='V9',
        closed_icon_template='config/icons/tabs/closed/resources_icon_closed.png',
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


def close_projects_tab():
    projects_tab_close_template_path = 'config/icons/projects/projects_tab.png'
    projects_tab_close_region = get_grid_region('S8', 'U8')

    if projects_tab_close_region is None:
        log_input_event(
            'research_project',
            '',
            '',
            'status=projects_tab_close_region_error;region=S8-U8'
        )
        print("Could not resolve projects tab close region S8-U8")
        return None

    projects_tab_close_detection = find_template_match(
        template_path=projects_tab_close_template_path,
        search_region=projects_tab_close_region,
        confidence=0.75,
    )
    if projects_tab_close_detection is None:
        log_input_event(
            'research_project',
            '',
            '',
            (
                'status=projects_tab_close_not_found;'
                f'template={projects_tab_close_template_path};region=S8-U8'
            )
        )
        print("Could not find projects tab close icon")
        return None

    close_x = int(projects_tab_close_detection['center_x'])
    close_y = int(projects_tab_close_detection['center_y'])
    pyautogui.moveTo(close_x, close_y, duration=0.1)
    log_input_event('mouse_move', '', '', f'x={close_x};y={close_y};target=projects_tab;phase=close_projects_tab')
    pyautogui.click(close_x, close_y)
    log_input_event('mouse_click', '', '', f'x={close_x};y={close_y};button=left;target=projects_tab;phase=close_projects_tab')
    print("Projects tab closed")
    log_input_event('research_project', '', '', 'status=projects_tab_closed')
    return projects_tab_close_detection


def research_project(project_name, taskbar_search_start_grid, taskbar_search_end_grid):
    project_code = str(project_name).strip().lower()
    project_template_path = f'config/icons/projects/project_icons/{project_code}.png'
    projects_tab_template_path = 'config/icons/tabs/closed/projects_icon_closed.png'
    project_available_template_path = 'config/icons/projects/research_project.png'
    project_unavailable_template_path = 'config/icons/projects/project_cost_unmet.png'
    close_project_template_path = 'config/icons/projects/close_project.png'

    print(f"Unlock project: {project_code}")
    log_input_event('research_project', '', '', f'project={project_code};status=start')

    print("Opening project tab")
    projects_tab_region = get_grid_region(taskbar_search_start_grid, taskbar_search_end_grid)
    if projects_tab_region is None:
        log_input_event(
            'research_project',
            '',
            '',
            (
                f'project={project_code};status=projects_tab_region_error;'
                f'region={taskbar_search_start_grid}-{taskbar_search_end_grid}'
            )
        )
        print("Could not resolve projects tab search region")
        return None

    projects_tab_detection = find_template_match(
        template_path=projects_tab_template_path,
        search_region=projects_tab_region,
        confidence=0.75,
    )
    if projects_tab_detection is None:
        log_input_event(
            'research_project',
            '',
            '',
            (
                f'project={project_code};status=projects_tab_not_found;template={projects_tab_template_path};'
                f'region={taskbar_search_start_grid}-{taskbar_search_end_grid}'
            )
        )
        print("Projects tab icon (closed) not found")
        return None

    projects_tab_x = int(projects_tab_detection['center_x'])
    projects_tab_y = int(projects_tab_detection['center_y'])
    pyautogui.moveTo(projects_tab_x, projects_tab_y, duration=0.1)
    log_input_event('mouse_move', '', '', f'x={projects_tab_x};y={projects_tab_y};target=projects_icon_closed;phase=research_project_open_tab')
    pyautogui.click(projects_tab_x, projects_tab_y)
    log_input_event('mouse_click', '', '', f'x={projects_tab_x};y={projects_tab_y};button=left;target=projects_icon_closed;phase=research_project_open_tab')
    time.sleep(0.5)

    project_icon_region = get_grid_region('M9', 'V16')
    if project_icon_region is None:
        log_input_event(
            'research_project',
            '',
            '',
            f'project={project_code};status=project_icon_region_error;region=M9-V16'
        )
        print("Could not resolve project icon search region M9-V16")
        return None

    project_detection = find_template_match(
        template_path=project_template_path,
        search_region=project_icon_region,
        confidence=0.75,
    )
    if project_detection is None:
        log_input_event(
            'research_project',
            '',
            '',
            (
                f'project={project_code};status=project_icon_not_found;template={project_template_path};'
                'region=M9-V16'
            )
        )
        print(f"Project icon not found: {project_code}")
        return None

    project_x = int(project_detection['center_x'])
    project_y = int(project_detection['center_y'])
    pyautogui.moveTo(project_x, project_y, duration=0.1)
    log_input_event('mouse_move', '', '', f'x={project_x};y={project_y};target={project_code};phase=research_project_select_project')
    pyautogui.click(project_x, project_y)
    log_input_event('mouse_click', '', '', f'x={project_x};y={project_y};button=left;target={project_code};phase=research_project_select_project')
    time.sleep(0.5)

    print("Checking project availability")
    availability_region = get_grid_region('P12', 'S14')
    if availability_region is None:
        log_input_event(
            'research_project',
            '',
            '',
            f'project={project_code};status=availability_region_error;region=P12-S14'
        )
        print("Could not resolve project availability region P12-S14")
        return None

    ax, ay, aw, ah = availability_region
    trim_y = int(ah * 0.20)
    availability_region_trimmed = (
        ax,
        ay + trim_y,
        aw,
        max(1, ah - (trim_y * 2)),
    )

    availability_confidence = 0.60
    availability_score_margin = 0.03

    available_detection = find_template_match_brightness(
        template_path=project_available_template_path,
        search_region=availability_region_trimmed,
        confidence=availability_confidence,
    )
    unavailable_detection = find_template_match_brightness(
        template_path=project_unavailable_template_path,
        search_region=availability_region_trimmed,
        confidence=availability_confidence,
    )

    available_score = float(available_detection['score']) if available_detection is not None else -1.0
    unavailable_score = float(unavailable_detection['score']) if unavailable_detection is not None else -1.0
    log_input_event(
        'research_project',
        '',
        '',
        (
            f'project={project_code};status=availability_scores;'
            f'available_score={available_score:.4f};unavailable_score={unavailable_score:.4f};'
            f'confidence={availability_confidence:.2f};margin={availability_score_margin:.2f}'
        )
    )
    print(
        "Availability scores -> "
        f"available={available_score:.4f}, "
        f"cost_unmet={unavailable_score:.4f}, "
        f"confidence={availability_confidence:.2f}, "
        f"margin={availability_score_margin:.2f}"
    )

    available_wins = (
        available_detection is not None
        and (unavailable_detection is None or available_score >= (unavailable_score + availability_score_margin))
    )
    unavailable_wins = (
        unavailable_detection is not None
        and (available_detection is None or unavailable_score >= (available_score - availability_score_margin))
    )
    print(
        "Availability decision flags -> "
        f"available_wins={available_wins}, "
        f"unavailable_wins={unavailable_wins}"
    )

    if available_wins:
        print("Project available")
        available_x = int(available_detection['center_x'])
        available_y = int(available_detection['center_y'])
        pyautogui.moveTo(available_x, available_y, duration=0.1)
        log_input_event('mouse_move', '', '', f'x={available_x};y={available_y};target=project_available;phase=research_project_unlock')
        pyautogui.click(available_x, available_y)
        log_input_event('mouse_click', '', '', f'x={available_x};y={available_y};button=left;target=project_available;phase=research_project_unlock')
        log_input_event('research_project', '', '', f'project={project_code};status=unlocked')
        print(f"Project unlocked: {project_code}")

        close_projects_tab()
        return available_detection

    if unavailable_wins:
        print("Project unavailable")
        log_input_event('research_project', '', '', f'project={project_code};status=unavailable')

        close_project_region = get_grid_region('Q15', 'R16')
        if close_project_region is None:
            log_input_event(
                'research_project',
                '',
                '',
                f'project={project_code};status=close_project_region_error;region=Q15-R16'
            )
            print("Could not resolve close project region Q15-R16")
        else:
            close_project_detection = find_template_match(
                template_path=close_project_template_path,
                search_region=close_project_region,
                confidence=0.75,
            )
            if close_project_detection is not None:
                close_project_x = int(close_project_detection['center_x'])
                close_project_y = int(close_project_detection['center_y'])
                pyautogui.moveTo(close_project_x, close_project_y, duration=0.1)
                log_input_event('mouse_move', '', '', f'x={close_project_x};y={close_project_y};target=close_project;phase=research_project_close_project_window')
                pyautogui.click(close_project_x, close_project_y)
                log_input_event('mouse_click', '', '', f'x={close_project_x};y={close_project_y};button=left;target=close_project;phase=research_project_close_project_window')
                print("Closed individual project window")
            else:
                log_input_event(
                    'research_project',
                    '',
                    '',
                    (
                        f'project={project_code};status=close_project_not_found;'
                        f'template={close_project_template_path};region=Q15-R16'
                    )
                )
                print("Could not find close_project icon")

        close_projects_tab()
        return unavailable_detection

    print("Could not determine project availability state")
    log_input_event('research_project', '', '', f'project={project_code};status=availability_state_unknown')
    return None


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
        screenshot_label=f'planet_{planet_code}',
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
        screenshot_label=f'planet_{planet_code}',
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
        close_tab_template_path = 'config/icons/planets/planet_tab.png'
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
                screenshot_label=f'planet_{planet_code}',
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


def sell_ores(ore_name, taskbar_search_start_grid, taskbar_search_end_grid):
    ore_code = str(ore_name).strip().lower()
    template_path = f'config/icons/ores/{ore_code}.png'

    resources_open = open_resources_tab(
        interface_search_start=taskbar_search_start_grid,
        interface_search_end=taskbar_search_end_grid,
    )
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

    close_tab_region = get_grid_region('S8', 'V9')
    close_tab_template_path = 'config/icons/tabs/resource_window.png'
    if close_tab_region is None:
        log_input_event(
            'ore_sell',
            '',
            '',
            (
                f'ore={ore_code};template={close_tab_template_path};status=close_tab_region_error;'
                'region=S8-V9'
            )
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
                (
                    f'ore={ore_code};template={close_tab_template_path};status=resources_open_icon_not_found;'
                    'region=S8-V9'
                )
            )
            print("Could not find resource window icon to close tab")

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
    close_tab_template_path = 'config/icons/planets/planet_tab.png'
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


def _apply_value_stability_guard(metric_name, observed_value, stability_state, jump_factor=10.0):
    if observed_value is None:
        return None

    last_value = stability_state.get('last')
    pending_value = stability_state.get('pending')

    if last_value is None:
        stability_state['last'] = int(observed_value)
        stability_state['pending'] = None
        return int(observed_value)

    smaller = max(1, min(int(last_value), int(observed_value)))
    larger = max(int(last_value), int(observed_value))
    ratio = float(larger) / float(smaller)

    if ratio <= float(jump_factor):
        stability_state['last'] = int(observed_value)
        stability_state['pending'] = None
        return int(observed_value)

    if pending_value is not None and int(pending_value) == int(observed_value):
        stability_state['last'] = int(observed_value)
        stability_state['pending'] = None
        print(
            f"{metric_name} stability guard: accepted confirmed jump "
            f"from ${int(last_value):,} to ${int(observed_value):,}"
        )
        log_input_event(
            'value_guard',
            '',
            '',
            (
                f'metric={metric_name};status=accepted_confirmed_jump;'
                f'from={int(last_value)};to={int(observed_value)};ratio={ratio:.2f}'
            )
        )
        return int(observed_value)

    stability_state['pending'] = int(observed_value)
    print(
        f"{metric_name} stability guard: held suspicious jump "
        f"from ${int(last_value):,} to ${int(observed_value):,}; waiting for confirmation"
    )
    log_input_event(
        'value_guard',
        '',
        '',
        (
            f'metric={metric_name};status=held_suspicious_jump;'
            f'from={int(last_value)};to={int(observed_value)};ratio={ratio:.2f}'
        )
    )
    return int(last_value)


def value_checker(currency_region, galaxy_value_region, debug_dir_name, value_stability_state):
    currency = get_currency_value_with_visualization(
        region=currency_region,
        display=False,
        debug_dir=debug_dir_name,
        debug_filename='currency_region_latest.png',
    )
    currency = _apply_value_stability_guard(
        metric_name='cash',
        observed_value=currency,
        stability_state=value_stability_state['cash'],
        jump_factor=10.0,
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
    galaxy_value = _apply_value_stability_guard(
        metric_name='galaxy_value',
        observed_value=galaxy_value,
        stability_state=value_stability_state['galaxy_value'],
        jump_factor=10.0,
    )
    if galaxy_value is not None:
        print(f"Galaxy value: ${galaxy_value:,}")
    else:
        print("Galaxy value: not detected")


def load_runtime_config(base_dir):
    ref_config_path = os.path.join(base_dir, 'config', 'ipm_config.json')
    default_scroll_start_grid = "T9"
    default_currency_region_start_grid = "I1"
    default_currency_region_end_grid = "P2"
    default_galaxy_value_region_start_grid = "M3"
    default_galaxy_value_region_end_grid = "P4"
    default_taskbar_search_start_grid = "M17"
    default_taskbar_search_end_grid = "V17"
    enable_focus_click = True  # Toggle this on/off for pre-zoom focus click
    run_window_setup = True

    grid_target = default_scroll_start_grid
    currency_region_start_grid = default_currency_region_start_grid
    currency_region_end_grid = default_currency_region_end_grid
    galaxy_value_region_start_grid = default_galaxy_value_region_start_grid
    galaxy_value_region_end_grid = default_galaxy_value_region_end_grid
    taskbar_search_start_grid = default_taskbar_search_start_grid
    taskbar_search_end_grid = default_taskbar_search_end_grid

    config_changed = False
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

            config_galaxy_value_start = str(config_data.get('galaxy_value_region_start_grid', '')).strip().upper()
            if config_galaxy_value_start:
                galaxy_value_region_start_grid = config_galaxy_value_start

            config_galaxy_value_end = str(config_data.get('galaxy_value_region_end_grid', '')).strip().upper()
            if config_galaxy_value_end:
                galaxy_value_region_end_grid = config_galaxy_value_end

            config_taskbar_start = str(config_data.get('taskbar_search_start_grid', '')).strip().upper()
            if config_taskbar_start:
                taskbar_search_start_grid = config_taskbar_start

            config_taskbar_end = str(config_data.get('taskbar_search_end_grid', '')).strip().upper()
            if config_taskbar_end:
                taskbar_search_end_grid = config_taskbar_end

            if 'enable_focus_click' in config_data:
                enable_focus_click = bool(config_data.get('enable_focus_click'))

            if 'run_window_setup' in config_data:
                run_window_setup = bool(config_data.get('run_window_setup'))

            if 'scroll_start_grid' not in config_data:
                config_data['scroll_start_grid'] = default_scroll_start_grid
                config_changed = True
            if 'currency_region_start_grid' not in config_data:
                config_data['currency_region_start_grid'] = default_currency_region_start_grid
                config_changed = True
            if 'currency_region_end_grid' not in config_data:
                config_data['currency_region_end_grid'] = default_currency_region_end_grid
                config_changed = True
            if 'galaxy_value_region_start_grid' not in config_data:
                config_data['galaxy_value_region_start_grid'] = default_galaxy_value_region_start_grid
                config_changed = True
            if 'galaxy_value_region_end_grid' not in config_data:
                config_data['galaxy_value_region_end_grid'] = default_galaxy_value_region_end_grid
                config_changed = True
            if 'taskbar_search_start_grid' not in config_data:
                config_data['taskbar_search_start_grid'] = default_taskbar_search_start_grid
                config_changed = True
            if 'taskbar_search_end_grid' not in config_data:
                config_data['taskbar_search_end_grid'] = default_taskbar_search_end_grid
                config_changed = True
            if 'enable_focus_click' not in config_data:
                config_data['enable_focus_click'] = enable_focus_click
                config_changed = True
            if 'run_window_setup' not in config_data:
                config_data['run_window_setup'] = run_window_setup
                config_changed = True

            if config_changed:
                with open(ref_config_path, 'w', encoding='utf-8') as config_file:
                    json.dump(config_data, config_file, indent=2)
    except Exception as e:
        print(f"Warning: could not load runtime config from ipm_config.json: {e}")

    # Currency monitor region from config bounds
    currency_region = get_grid_region(currency_region_start_grid, currency_region_end_grid)
    if currency_region is None:
        currency_region = (800, 0, 800, 200)
        print("Using fallback currency region (800, 0, 800, 200)")

    # Tighten region to focus on currency text only
    # Shrink by 50px on Y sides, keep full X range
    rx, ry, rw, rh = currency_region
    currency_region = (rx, ry + 50, rw, max(1, rh - 100))

    # Galaxy value region from config bounds, trimmed by 5% left/right, 20% top, and 35% bottom
    galaxy_value_region = get_grid_region(galaxy_value_region_start_grid, galaxy_value_region_end_grid)
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

    return {
        'ref_config_path': ref_config_path,
        'grid_target': grid_target,
        'currency_region_start_grid': currency_region_start_grid,
        'currency_region_end_grid': currency_region_end_grid,
        'galaxy_value_region_start_grid': galaxy_value_region_start_grid,
        'galaxy_value_region_end_grid': galaxy_value_region_end_grid,
        'taskbar_search_start_grid': taskbar_search_start_grid,
        'taskbar_search_end_grid': taskbar_search_end_grid,
        'enable_focus_click': enable_focus_click,
        'run_window_setup': run_window_setup,
        'currency_region': currency_region,
        'galaxy_value_region': galaxy_value_region,
        'debug_dir_name': debug_dir_name,
    }


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
        # Open/focus BlueStacks
        open_bluestacks()

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
    else:
        print("Skipping game window setup actions (run_window_setup=False)")

    return None

def upgrade(planet):
        stat_upgrade(planet, "mining_rate")
        stat_upgrade(planet, "ship_speed")
        stat_upgrade(planet, "cargo")

def run_gameplay_loop(
    currency_region,
    galaxy_value_region,
    debug_dir_name,
    taskbar_search_start_grid,
    taskbar_search_end_grid,
):
    """
    Gameplay logic starts here.
    Setup/calibration should be completed before calling this function.
    """
    """
    #unlock_planet("Q8","Q9","p1",20,0)
    #time.sleep(0.5)
    sell_ores("copper", taskbar_search_start_grid, taskbar_search_end_grid)
    time.sleep(10)
    upgrade("p1")

    unlock_planet("R8","R8","p2",0,0)
    time.sleep(0.5)
    sell_ores("iron", taskbar_search_start_grid, taskbar_search_end_grid)
    time.sleep(10)
    upgrade("p2")
    """

    #open_resources_tab(taskbar_search_start_grid, taskbar_search_end_grid)
    #unlock_planet("R10","S11","p3",10,10)q
    time.sleep(10)
    upgrade("p3")

    unlock_planet("P11","Q11","p4",0,10)
    time.sleep(0.5)
    sell_ores("lead", taskbar_search_start_grid, taskbar_search_end_grid)
    time.sleep(10)
    upgrade("p4")
    #research_project("management",taskbar_search_start_grid,taskbar_search_end_grid)
    #research_project("crafter",taskbar_search_start_grid,taskbar_search_end_grid)

    print(f"\nMonitoring currency every 5 seconds in region: {currency_region}")
    print("Press 'q' to exit.")
    print("Saving OCR crops to bot_program/search_screenshots")

    value_stability_state = {
        'cash': {'last': None, 'pending': None},
        'galaxy_value': {'last': None, 'pending': None},
    }

    next_check = 0.0
    while True:
        if keyboard.is_pressed('q'):
            print("Exiting program...")
            os._exit(0)

        now = time.time()
        if now >= next_check:
            value_checker(
                currency_region=currency_region,
                galaxy_value_region=galaxy_value_region,
                debug_dir_name=debug_dir_name,
                value_stability_state=value_stability_state,
            )
            next_check = now + 5

        time.sleep(0.1)

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    game_log_path = os.path.join(base_dir, 'game_log.txt')
    setup_game_log(game_log_path)
    runtime_config = load_runtime_config(base_dir)
    
    setup = True
    if setup == True:
        game_window_setup(
            base_dir=base_dir,
            runtime_config=runtime_config,
            run_setup=bool(runtime_config.get('run_window_setup', True)),
        )

    currency_region = runtime_config['currency_region']
    galaxy_value_region = runtime_config['galaxy_value_region']
    debug_dir_name = runtime_config['debug_dir_name']
    taskbar_search_start_grid = runtime_config['taskbar_search_start_grid']
    taskbar_search_end_grid = runtime_config['taskbar_search_end_grid']

    run_gameplay_loop(
        currency_region=currency_region,
        galaxy_value_region=galaxy_value_region,
        debug_dir_name=debug_dir_name,
        taskbar_search_start_grid=taskbar_search_start_grid,
        taskbar_search_end_grid=taskbar_search_end_grid,
    )
