import keyboard
import os
import threading
import time
import pyautogui
from utils import (
    _apply_value_stability_guard,
    directory_reset,
    start_exit_hotkey_listener,
    open_resources_interface,
    find_template_match,
    find_template_match_brightness,
    get_currency_value_with_visualization,
    get_grid_region,
    log_input_event,
)
from config import get_planet_search_settings, load_runtime_config, set_planet_search_config
from setup import game_window_setup, setup_game_log


PLANET_MATCH_CONFIDENCE = 0.65


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


def unlock_planet(planet):
    planet_code = str(planet).strip().lower()
    template_path = f'config/icons/planets/locked/{planet_code}.png'

    planet_settings = get_planet_search_settings(planet_code)
    start_search_cell = planet_settings['start_grid']
    end_search_cell = planet_settings['end_grid']
    vertical_trim_ratio = planet_settings['vertical_trim_ratio'] if planet_settings['vertical_trim_ratio'] is not None else 0.0
    horizontal_trim_ratio = planet_settings['horizontal_trim_ratio'] if planet_settings['horizontal_trim_ratio'] is not None else 0.0

    if start_search_cell is None or end_search_cell is None:
        message = (
            f"missing planet region in config for {planet_code}; "
            "expected planet_regions.<planet>.start_grid and end_grid"
        )
        print(message)
        log_input_event('planet_search', '', '', f'planet={planet_code};status=config_region_missing')
        return None

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
        confidence=PLANET_MATCH_CONFIDENCE,
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
        confidence=PLANET_MATCH_CONFIDENCE,
        screenshot_label=f'planet_{planet_code}',
    )

    if unlocked_detection is not None:
        log_input_event(
            'planet_search',
            '',
            '',
            (
                f'planet={planet_code};template={unlocked_template_path};'
                f'region={start_search_cell}-{end_search_cell};'
                f'status=unlocked_found;score={float(unlocked_detection["score"]):.4f};'
                f'center_x={int(unlocked_detection["center_x"])};center_y={int(unlocked_detection["center_y"])}'
            )
        )
        print(f"Found unlocked planet icon for {planet_code}")
        close_tab_detection = close_planet(planet_code)
        if close_tab_detection is not None:
            log_input_event(
                'planet_search',
                '',
                '',
                (
                    f'planet={planet_code};template=config/icons/planets/planet_tab.png;'
                    'status=planet_tab_closed;'
                    f'center_x={int(close_tab_detection["center_x"])};center_y={int(close_tab_detection["center_y"])}'
                )
            )
        else:
            log_input_event(
                'planet_search',
                '',
                '',
                f'planet={planet_code};template=config/icons/planets/planet_tab.png;status=planet_tab_not_found;region=S6-V6'
            )
    else:
        log_input_event(
            'planet_search',
            '',
            '',
            (
                f'planet={planet_code};template={unlocked_template_path};'
                f'region={start_search_cell}-{end_search_cell};'
                'status=unlocked_not_found'
            )
        )
        print(f"Unlocked planet icon not found for {planet_code}")

    print(f"Clicked locked planet icon for {planet_code} at (x={center_x}, y={center_y})")
    return detection


def open_planet(planet):
    planet_code = str(planet).strip().lower()
    template_path = f'config/icons/planets/unlocked/{planet_code}.png'

    planet_settings = get_planet_search_settings(planet_code)
    start_search_cell = planet_settings['start_grid']
    end_search_cell = planet_settings['end_grid']
    vertical_trim_ratio = planet_settings['vertical_trim_ratio'] if planet_settings['vertical_trim_ratio'] is not None else 0.0
    horizontal_trim_ratio = planet_settings['horizontal_trim_ratio'] if planet_settings['horizontal_trim_ratio'] is not None else 0.0

    if start_search_cell is None or end_search_cell is None:
        message = (
            f"missing planet region in config for {planet_code}; "
            "expected planet_regions.<planet>.start_grid and end_grid"
        )
        print(message)
        log_input_event('planet_open', '', '', f'planet={planet_code};status=config_region_missing')
        return None

    search_region = get_grid_region(start_search_cell, end_search_cell)
    if search_region is None:
        print(f"Could not resolve planet search region: {start_search_cell} to {end_search_cell}")
        log_input_event(
            'planet_open',
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
        'planet_open',
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
        f"Searching for unlocked {planet_code} in {start_search_cell}-{end_search_cell} "
        f"with trim v={vertical_percent:.2f}% h={horizontal_percent:.2f}%"
    )

    detection = find_template_match(
        template_path=template_path,
        search_region=trimmed_region,
        confidence=PLANET_MATCH_CONFIDENCE,
        screenshot_label=f'planet_open_{planet_code}',
    )

    if detection is None:
        log_input_event(
            'planet_open',
            '',
            '',
            (
                f'planet={planet_code};template={template_path};region={start_search_cell}-{end_search_cell};'
                'status=not_found'
            )
        )
        print(f"Unlocked planet icon not found: {planet_code}")
        return None

    center_x = int(detection['center_x'])
    center_y = int(detection['center_y'])
    log_input_event(
        'planet_open',
        '',
        '',
        (
            f'planet={planet_code};template={template_path};region={start_search_cell}-{end_search_cell};'
            f'status=found;score={float(detection["score"]):.4f};center_x={center_x};center_y={center_y}'
        )
    )

    pyautogui.moveTo(center_x, center_y, duration=0.1)
    log_input_event('mouse_move', '', '', f'x={center_x};y={center_y};target={planet_code};phase=open_planet')
    pyautogui.click(center_x, center_y)
    log_input_event('mouse_click', '', '', f'x={center_x};y={center_y};button=left;target={planet_code};phase=open_planet')

    print(f"Opened unlocked planet icon for {planet_code} at (x={center_x}, y={center_y})")
    return detection


def close_planet(planet):
    planet_code = str(planet).strip().lower()
    close_tab_region = get_grid_region('S6', 'V6')
    close_tab_template_path = 'config/icons/planets/planet_tab.png'

    if close_tab_region is None:
        log_input_event(
            'planet_close',
            '',
            '',
            f'planet={planet_code};template={close_tab_template_path};status=close_tab_region_error;region=S6-V6'
        )
        print("Could not resolve close tab region S6-V6")
        return None

    close_tab_detection = find_template_match(
        template_path=close_tab_template_path,
        search_region=close_tab_region,
        confidence=0.75,
        screenshot_label=f'planet_close_{planet_code}',
    )

    if close_tab_detection is None:
        log_input_event(
            'planet_close',
            '',
            '',
            f'planet={planet_code};template={close_tab_template_path};status=planet_tab_not_found;region=S6-V6'
        )
        print(f"Could not find planet tab close icon for {planet_code}")
        return None

    close_x = int(close_tab_detection['center_x'])
    close_y = int(close_tab_detection['center_y'])
    pyautogui.moveTo(close_x, close_y, duration=0.1)
    log_input_event('mouse_move', '', '', f'x={close_x};y={close_y};target=planet_tab;phase=close_planet')
    pyautogui.click(close_x, close_y)
    log_input_event('mouse_click', '', '', f'x={close_x};y={close_y};button=left;target=planet_tab;phase=close_planet')
    log_input_event(
        'planet_close',
        '',
        '',
        (
            f'planet={planet_code};template={close_tab_template_path};status=planet_tab_closed;'
            f'center_x={close_x};center_y={close_y}'
        )
    )
    print(f"Closed planet tab for {planet_code}")
    return close_tab_detection


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

    planet_search_message = f"opening unlocked planet {planet_code}"
    print(planet_search_message)
    log_input_event('stat_upgrade', '', '', planet_search_message)
    planet_detection = open_planet(planet_code)
    if planet_detection is None:
        not_found_message = f"unlocked planet not found: {planet_code}"
        print(not_found_message)
        log_input_event('stat_upgrade', '', '', not_found_message)
        return False
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
    close_tab_detection = close_planet(planet_code)
    if close_tab_detection is None:
        close_not_found = "planet tab close icon not found"
        print(close_not_found)
        log_input_event('stat_upgrade', '', '', close_not_found)
        return False
    return True


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


def start_value_monitor_listener(currency_region, galaxy_value_region, debug_dir_name):
    value_stability_state = {
        'cash': {'last': None, 'pending': None},
        'galaxy_value': {'last': None, 'pending': None},
    }

    def _monitor_loop():
        next_check = 0.0
        while True:
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

    monitor_thread = threading.Thread(target=_monitor_loop, daemon=True, name='value-monitor')
    monitor_thread.start()
    return monitor_thread


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
    #open_planet("p1")
    """
    unlock_planet("p1")
    time.sleep(0.5)
    sell_ores("copper", taskbar_search_start_grid, taskbar_search_end_grid)
    time.sleep(10)

    unlock_planet("p2")
    time.sleep(0.5)
    sell_ores("iron", taskbar_search_start_grid, taskbar_search_end_grid)
    time.sleep(10)
    
    open_resources_tab(taskbar_search_start_grid, taskbar_search_end_grid)
    unlock_planet("p3")
    time.sleep(10)
    
    unlock_planet("p4")
    time.sleep(0.5)
    sell_ores("lead", taskbar_search_start_grid, taskbar_search_end_grid)
    time.sleep(10)
    """
    for planet in ['p1', 'p2', 'p3', 'p4']:
        upgrade(planet)
    

    #Planet search regions/trims come from config/ipm_config.json -> planet_regions.

    #research_project("management",taskbar_search_start_grid,taskbar_search_end_grid)
    #research_project("crafter",taskbar_search_start_grid,taskbar_search_end_grid)

    while True:
        time.sleep(0.1)

if __name__ == "__main__":
    start_exit_hotkey_listener()
    base_dir = os.path.dirname(os.path.abspath(__file__))
    search_screenshots_dir = os.path.join(base_dir, 'search_screenshots')
    directory_reset(search_screenshots_dir, label='search screenshot directory')

    game_log_path = os.path.join(base_dir, 'game_log.txt')
    directory_reset(game_log_path, label='game log file', is_file=True)

    setup_game_log(game_log_path)
    runtime_config = load_runtime_config(base_dir)
    set_planet_search_config(runtime_config.get('planet_regions', {}))
    
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

    print(f"\nMonitoring currency every 5 seconds in region: {currency_region}")
    print("Press 'q' to exit.")
    print("Saving OCR crops to bot_program/search_screenshots")
    start_value_monitor_listener(
        currency_region=currency_region,
        galaxy_value_region=galaxy_value_region,
        debug_dir_name=debug_dir_name,
    )

    run_gameplay_loop(
        currency_region=currency_region,
        galaxy_value_region=galaxy_value_region,
        debug_dir_name=debug_dir_name,
        taskbar_search_start_grid=taskbar_search_start_grid,
        taskbar_search_end_grid=taskbar_search_end_grid,
    )
