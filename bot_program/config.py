import json
import os

from utils import _normalize_grid_cell, _safe_float, get_grid_region


PLANET_SEARCH_CONFIG = {}


def set_planet_search_config(planet_search_config):
    global PLANET_SEARCH_CONFIG
    if isinstance(planet_search_config, dict):
        PLANET_SEARCH_CONFIG = planet_search_config
    else:
        PLANET_SEARCH_CONFIG = {}


def get_planet_search_settings(planet):
    planet_code = str(planet).strip().lower()
    planet_entry = PLANET_SEARCH_CONFIG.get(planet_code, {})
    if not isinstance(planet_entry, dict):
        planet_entry = {}

    start_grid = _normalize_grid_cell(planet_entry.get('start_grid'))
    end_grid = _normalize_grid_cell(planet_entry.get('end_grid'))

    vertical_trim_ratio = _safe_float(planet_entry.get('vertical_trim_ratio'))
    horizontal_trim_ratio = _safe_float(planet_entry.get('horizontal_trim_ratio'))

    return {
        'start_grid': start_grid,
        'end_grid': end_grid,
        'vertical_trim_ratio': vertical_trim_ratio,
        'horizontal_trim_ratio': horizontal_trim_ratio,
    }


def load_runtime_config(base_dir):
    ref_config_path = os.path.join(base_dir, 'config', 'ipm_config.json')
    default_scroll_start_grid = "T9"
    default_currency_region_start_grid = "I1"
    default_currency_region_end_grid = "P2"
    default_galaxy_value_region_start_grid = "M3"
    default_galaxy_value_region_end_grid = "P4"
    default_taskbar_search_start_grid = "M17"
    default_taskbar_search_end_grid = "V17"
    enable_focus_click = True
    run_window_setup = True

    grid_target = default_scroll_start_grid
    currency_region_start_grid = default_currency_region_start_grid
    currency_region_end_grid = default_currency_region_end_grid
    galaxy_value_region_start_grid = default_galaxy_value_region_start_grid
    galaxy_value_region_end_grid = default_galaxy_value_region_end_grid
    taskbar_search_start_grid = default_taskbar_search_start_grid
    taskbar_search_end_grid = default_taskbar_search_end_grid
    default_planet_regions = {
        'p1': {
            'start_grid': 'XX',
            'end_grid': 'XX',
            'vertical_trim_ratio': 'XX',
            'horizontal_trim_ratio': 'XX',
        },
        'p2': {
            'start_grid': 'XX',
            'end_grid': 'XX',
            'vertical_trim_ratio': 'XX',
            'horizontal_trim_ratio': 'XX',
        },
        'p3': {
            'start_grid': 'XX',
            'end_grid': 'XX',
            'vertical_trim_ratio': 'XX',
            'horizontal_trim_ratio': 'XX',
        },
        'p4': {
            'start_grid': 'XX',
            'end_grid': 'XX',
            'vertical_trim_ratio': 'XX',
            'horizontal_trim_ratio': 'XX',
        },
    }
    planet_regions = dict(default_planet_regions)

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

            config_planet_regions = config_data.get('planet_regions')
            if isinstance(config_planet_regions, dict):
                for planet_code, defaults in default_planet_regions.items():
                    planet_entry = config_planet_regions.get(planet_code, {})
                    if not isinstance(planet_entry, dict):
                        planet_entry = {}
                    planet_regions[planet_code] = {
                        'start_grid': str(planet_entry.get('start_grid', defaults['start_grid'])).strip().upper(),
                        'end_grid': str(planet_entry.get('end_grid', defaults['end_grid'])).strip().upper(),
                        'vertical_trim_ratio': planet_entry.get('vertical_trim_ratio', defaults['vertical_trim_ratio']),
                        'horizontal_trim_ratio': planet_entry.get('horizontal_trim_ratio', defaults['horizontal_trim_ratio']),
                    }

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
            if 'planet_regions' not in config_data:
                config_data['planet_regions'] = planet_regions
                config_changed = True

            if config_changed:
                with open(ref_config_path, 'w', encoding='utf-8') as config_file:
                    json.dump(config_data, config_file, indent=2)
    except Exception as e:
        print(f"Warning: could not load runtime config from ipm_config.json: {e}")

    currency_region = get_grid_region(currency_region_start_grid, currency_region_end_grid)
    if currency_region is None:
        currency_region = (800, 0, 800, 200)
        print("Using fallback currency region (800, 0, 800, 200)")

    rx, ry, rw, rh = currency_region
    currency_region = (rx, ry + 50, rw, max(1, rh - 100))

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
        'planet_regions': planet_regions,
        'currency_region': currency_region,
        'galaxy_value_region': galaxy_value_region,
        'debug_dir_name': debug_dir_name,
    }
