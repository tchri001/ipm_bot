import subprocess
import os
import shutil
import json
import threading
import keyboard
import pygetwindow as gw
import time
import pyautogui
import easyocr
import re
import numpy as np
import cv2
import math
from datetime import datetime

_OCR_READER = None
_INPUT_LOG_PATH = None
_ZOOM_MODIFIER_KEY = 'ctrlleft'
_SEARCH_DEBUG_DIR_NAME = 'search_screenshots'
_AD_BANNER_CACHE = {
    'expires_at': 0.0,
    'present': False,
    'offset_x': 0,
}
_EXIT_LISTENER_STARTED = False


def set_input_log_path(log_path):
    """Set shared input log file path for utils-generated input events."""
    global _INPUT_LOG_PATH
    _INPUT_LOG_PATH = log_path


def log_input_event(event_type, key='', scan_code='', details=''):
    """Append a CSV input event row to the shared log file if configured."""
    if not _INPUT_LOG_PATH:
        return
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        safe_details = str(details).replace(',', ';')
        with open(_INPUT_LOG_PATH, 'a', encoding='utf-8') as log_file:
            log_file.write(f"{timestamp},{event_type},{key},{scan_code},{safe_details}\n")
    except OSError:
        pass


def _exit_hotkey_worker():
    while True:
        try:
            if keyboard.is_pressed('q'):
                print("Exit hotkey detected ('q'). Exiting program...")
                os._exit(0)
            time.sleep(0.05)
        except Exception as e:
            print(f"Warning: exit hotkey listener error: {e}")
            time.sleep(0.5)


def start_exit_hotkey_listener():
    global _EXIT_LISTENER_STARTED
    if _EXIT_LISTENER_STARTED:
        return

    listener_thread = threading.Thread(
        target=_exit_hotkey_worker,
        name='exit_hotkey_listener',
        daemon=True,
    )
    listener_thread.start()
    _EXIT_LISTENER_STARTED = True
    print("Exit hotkey listener started (press 'q' any time to exit)")


def directory_reset(path, label='directory', is_file=False):
    """Reset a directory or file path, returning True on success."""
    try:
        if os.path.exists(path):
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)

        if is_file:
            parent_dir = os.path.dirname(path)
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)
            with open(path, 'w', encoding='utf-8'):
                pass
        else:
            os.makedirs(path, exist_ok=True)

        print(f"Reset {label}: {path}")
        return True
    except Exception as e:
        print(f"Warning: could not reset {label}: {e}")
        return False


def _safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _normalize_grid_cell(value):
    text = str(value).strip().upper() if value is not None else ''
    if not text or text == 'XX':
        return None
    return text


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


def _resolve_local_path(path_value):
    """Resolve relative paths against this file's directory."""
    if os.path.isabs(path_value):
        return path_value
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), path_value)


def _build_debug_output_dir(debug_dir):
    if not debug_dir:
        return None
    if os.path.isabs(debug_dir):
        output_dir = debug_dir
    else:
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), debug_dir)
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


def _sanitize_filename_part(value):
    return re.sub(r'[^a-zA-Z0-9._-]+', '_', str(value))


def _save_template_search_screenshot(screenshot, template_path, search_region, debug_dir=_SEARCH_DEBUG_DIR_NAME, label=None):
    output_dir = _build_debug_output_dir(debug_dir)
    if output_dir is None:
        return None

    template_name = _sanitize_filename_part(os.path.splitext(os.path.basename(template_path))[0])
    label_part = ''
    if label:
        label_part = f"_{_sanitize_filename_part(label)}"

    if search_region is None:
        filename = f"search_{template_name}{label_part}_full_screen_latest.png"
    else:
        x, y, width, height = search_region
        filename = f"search_{template_name}{label_part}_x{x}_y{y}_w{width}_h{height}_latest.png"

    output_path = os.path.join(output_dir, filename)
    screenshot.save(output_path)
    return output_path


def _find_template_match(template_path, search_region=None, confidence=0.75, screenshot_label=None):
    """Find a template and return center/score details or None if not found."""
    try:
        if search_region is None:
            region_details = 'full_screen'
        else:
            rx, ry, rw, rh = search_region
            region_details = f'x={int(rx)};y={int(ry)};w={int(rw)};h={int(rh)}'

        log_input_event(
            'image_search',
            '',
            '',
            f'template={template_path};region={region_details};confidence={float(confidence):.3f};status=start'
        )

        template_full_path = _resolve_local_path(template_path)
        template_img = cv2.imread(template_full_path, cv2.IMREAD_GRAYSCALE)
        if template_img is None:
            log_input_event(
                'image_search',
                '',
                '',
                f'template={template_path};region={region_details};confidence={float(confidence):.3f};status=template_missing'
            )
            return None

        screenshot = pyautogui.screenshot(region=search_region)
        _save_template_search_screenshot(
            screenshot=screenshot,
            template_path=template_path,
            search_region=search_region,
            debug_dir=_SEARCH_DEBUG_DIR_NAME,
            label=screenshot_label,
        )
        screenshot_np = np.array(screenshot)
        screenshot_gray = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2GRAY)

        result = cv2.matchTemplate(screenshot_gray, template_img, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        if max_val < confidence:
            log_input_event(
                'image_search',
                '',
                '',
                f'template={template_path};region={region_details};confidence={float(confidence):.3f};status=not_found;score={float(max_val):.4f}'
            )
            return None

        template_h, template_w = template_img.shape
        center_x = max_loc[0] + (template_w // 2)
        center_y = max_loc[1] + (template_h // 2)

        if search_region is not None:
            region_x, region_y, _, _ = search_region
            center_x += region_x
            center_y += region_y

        log_input_event(
            'image_search',
            '',
            '',
            (
                f'template={template_path};region={region_details};confidence={float(confidence):.3f};'
                f'status=found;score={float(max_val):.4f};center_x={int(center_x)};center_y={int(center_y)}'
            )
        )

        return {
            'center_x': int(center_x),
            'center_y': int(center_y),
            'score': float(max_val),
            'template_w': int(template_w),
            'template_h': int(template_h),
        }
    except Exception as e:
        log_input_event(
            'image_search',
            '',
            '',
            f'template={template_path};confidence={float(confidence):.3f};status=error;error={e}'
        )
        return None


def _find_template_match_color(template_path, search_region=None, confidence=0.75):
    """Find a template with color matching and return center/score details or None if not found."""
    try:
        if search_region is None:
            region_details = 'full_screen'
        else:
            rx, ry, rw, rh = search_region
            region_details = f'x={int(rx)};y={int(ry)};w={int(rw)};h={int(rh)}'

        log_input_event(
            'image_search',
            '',
            '',
            f'template={template_path};region={region_details};confidence={float(confidence):.3f};mode=color;status=start'
        )

        template_full_path = _resolve_local_path(template_path)
        template_img = cv2.imread(template_full_path, cv2.IMREAD_COLOR)
        if template_img is None:
            log_input_event(
                'image_search',
                '',
                '',
                f'template={template_path};region={region_details};confidence={float(confidence):.3f};mode=color;status=template_missing'
            )
            return None

        screenshot = pyautogui.screenshot(region=search_region)
        _save_template_search_screenshot(
            screenshot=screenshot,
            template_path=template_path,
            search_region=search_region,
            debug_dir=_SEARCH_DEBUG_DIR_NAME,
        )
        screenshot_np = np.array(screenshot)
        screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)

        result = cv2.matchTemplate(screenshot_bgr, template_img, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        if max_val < confidence:
            log_input_event(
                'image_search',
                '',
                '',
                (
                    f'template={template_path};region={region_details};confidence={float(confidence):.3f};'
                    f'mode=color;status=not_found;score={float(max_val):.4f}'
                )
            )
            return None

        template_h, template_w, _ = template_img.shape
        center_x = max_loc[0] + (template_w // 2)
        center_y = max_loc[1] + (template_h // 2)

        if search_region is not None:
            region_x, region_y, _, _ = search_region
            center_x += region_x
            center_y += region_y

        log_input_event(
            'image_search',
            '',
            '',
            (
                f'template={template_path};region={region_details};confidence={float(confidence):.3f};'
                f'mode=color;status=found;score={float(max_val):.4f};center_x={int(center_x)};center_y={int(center_y)}'
            )
        )

        return {
            'center_x': int(center_x),
            'center_y': int(center_y),
            'score': float(max_val),
            'template_w': int(template_w),
            'template_h': int(template_h),
        }
    except Exception as e:
        log_input_event(
            'image_search',
            '',
            '',
            f'template={template_path};confidence={float(confidence):.3f};mode=color;status=error;error={e}'
        )
        return None


def _find_template_match_brightness(template_path, search_region=None, confidence=0.75):
    """Find a template using brightness (HSV V channel) and return center/score details or None."""
    try:
        if search_region is None:
            region_details = 'full_screen'
        else:
            rx, ry, rw, rh = search_region
            region_details = f'x={int(rx)};y={int(ry)};w={int(rw)};h={int(rh)}'

        log_input_event(
            'image_search',
            '',
            '',
            f'template={template_path};region={region_details};confidence={float(confidence):.3f};mode=brightness;status=start'
        )

        template_full_path = _resolve_local_path(template_path)
        template_img_bgr = cv2.imread(template_full_path, cv2.IMREAD_COLOR)
        if template_img_bgr is None:
            log_input_event(
                'image_search',
                '',
                '',
                f'template={template_path};region={region_details};confidence={float(confidence):.3f};mode=brightness;status=template_missing'
            )
            return None

        screenshot = pyautogui.screenshot(region=search_region)
        _save_template_search_screenshot(
            screenshot=screenshot,
            template_path=template_path,
            search_region=search_region,
            debug_dir=_SEARCH_DEBUG_DIR_NAME,
        )

        screenshot_np = np.array(screenshot)
        screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)

        template_v = cv2.cvtColor(template_img_bgr, cv2.COLOR_BGR2HSV)[:, :, 2]
        screenshot_v = cv2.cvtColor(screenshot_bgr, cv2.COLOR_BGR2HSV)[:, :, 2]

        result = cv2.matchTemplate(screenshot_v, template_v, cv2.TM_SQDIFF_NORMED)
        min_val, _, min_loc, _ = cv2.minMaxLoc(result)
        score = 1.0 - float(min_val)

        if score < confidence:
            log_input_event(
                'image_search',
                '',
                '',
                (
                    f'template={template_path};region={region_details};confidence={float(confidence):.3f};'
                    f'mode=brightness;status=not_found;score={score:.4f};sqdiff={float(min_val):.4f}'
                )
            )
            return None

        template_h, template_w = template_v.shape
        center_x = min_loc[0] + (template_w // 2)
        center_y = min_loc[1] + (template_h // 2)

        if search_region is not None:
            region_x, region_y, _, _ = search_region
            center_x += region_x
            center_y += region_y

        log_input_event(
            'image_search',
            '',
            '',
            (
                f'template={template_path};region={region_details};confidence={float(confidence):.3f};'
                f'mode=brightness;status=found;score={score:.4f};sqdiff={float(min_val):.4f};'
                f'center_x={int(center_x)};center_y={int(center_y)}'
            )
        )

        return {
            'center_x': int(center_x),
            'center_y': int(center_y),
            'score': float(score),
            'template_w': int(template_w),
            'template_h': int(template_h),
        }
    except Exception as e:
        log_input_event(
            'image_search',
            '',
            '',
            f'template={template_path};confidence={float(confidence):.3f};mode=brightness;status=error;error={e}'
        )
        return None


def find_template_match(template_path, search_region=None, confidence=0.65, screenshot_label=None):
    """Public wrapper for template matching with shared logging behavior."""
    return _find_template_match(
        template_path=template_path,
        search_region=search_region,
        confidence=confidence,
        screenshot_label=screenshot_label,
    )


def find_template_match_color(template_path, search_region=None, confidence=0.75):
    """Public wrapper for color template matching with shared logging behavior."""
    return _find_template_match_color(
        template_path=template_path,
        search_region=search_region,
        confidence=confidence,
    )


def find_template_match_brightness(template_path, search_region=None, confidence=0.75):
    """Public wrapper for brightness-based template matching (HSV value channel)."""
    return _find_template_match_brightness(
        template_path=template_path,
        search_region=search_region,
        confidence=confidence,
    )


def set_zoom_modifier_key(key_name):
    """Set the key used as zoom modifier for scroll shortcuts (pyautogui key name)."""
    global _ZOOM_MODIFIER_KEY
    if key_name:
        _ZOOM_MODIFIER_KEY = key_name


def _get_zoom_scroll_amounts(config_path='config/ipm_config.json'):
    """Load zoom scroll amounts from config with safe defaults."""
    scroll_up_amount = 100
    scroll_down_amount = -30
    try:
        config_full_path = _resolve_local_path(config_path)
        if os.path.exists(config_full_path):
            with open(config_full_path, 'r', encoding='utf-8') as config_file:
                config = json.load(config_file)
            scroll_up_amount = int(config.get('scroll_up_amount', scroll_up_amount))
            scroll_down_amount = int(config.get('scroll_down_amount', scroll_down_amount))
    except Exception as e:
        print(f"Warning: could not read zoom scroll amounts from config: {e}")

    return scroll_up_amount, scroll_down_amount


def _get_ad_banner_settings(config_path='config/ipm_config.json'):
    """Load ad banner detection settings from config with safe defaults."""
    settings = {
        'enabled': True,
        'template_path': 'config/ad_banner_probe.png',
        'confidence': 0.75,
        'offset_x': 290,
        'cache_seconds': 2.0,
        'search_top_px': 450,
        'fixed_width_px': 580,
        'pixel_threshold': 18,
        'nonblack_ratio_threshold': 0.35,
    }

    try:
        config_full_path = _resolve_local_path(config_path)
        if os.path.exists(config_full_path):
            with open(config_full_path, 'r', encoding='utf-8') as config_file:
                config = json.load(config_file)

            settings['enabled'] = bool(config.get('ad_banner_detection_enabled', settings['enabled']))
            settings['template_path'] = str(
                config.get('ad_banner_template_path', settings['template_path'])
            ).strip() or settings['template_path']
            settings['confidence'] = float(config.get('ad_banner_confidence', settings['confidence']))
            settings['offset_x'] = int(config.get('ad_banner_offset_x', settings['offset_x']))
            settings['cache_seconds'] = float(config.get('ad_banner_cache_seconds', settings['cache_seconds']))
            settings['search_top_px'] = int(config.get('ad_banner_search_top_px', settings['search_top_px']))
            settings['fixed_width_px'] = int(config.get('ad_banner_fixed_width_px', settings['fixed_width_px']))
            settings['pixel_threshold'] = int(config.get('ad_banner_pixel_threshold', settings['pixel_threshold']))
            settings['nonblack_ratio_threshold'] = float(
                config.get('ad_banner_nonblack_ratio_threshold', settings['nonblack_ratio_threshold'])
            )
    except Exception as e:
        print(f"Warning: could not read ad banner settings from config: {e}")

    return settings


def _detect_ad_banner_left_strip(
    fixed_width_px=580,
    search_top_px=450,
    pixel_threshold=18,
    nonblack_ratio_threshold=0.35,
):
    """
    Detect ad banner by measuring non-black pixel density in the left strip.
    """
    try:
        screenshot_np = np.array(pyautogui.screenshot().convert('RGB'))
        screen_h, screen_w = screenshot_np.shape[:2]

        strip_w = max(1, min(int(fixed_width_px), int(screen_w)))
        top_h = max(1, min(int(search_top_px), int(screen_h)))

        left_top = screenshot_np[:top_h, :strip_w, :]
        gray = cv2.cvtColor(left_top, cv2.COLOR_RGB2GRAY)
        nonblack_ratio = float((gray > int(pixel_threshold)).sum()) / float(gray.size)
        is_present = nonblack_ratio >= float(nonblack_ratio_threshold)
        return is_present, nonblack_ratio
    except Exception:
        return False, 0.0


def detect_ad_banner(template_path='config/ad_banner_probe.png', confidence=0.75, search_region=None, settings=None):
    """
    Detect whether an ad banner is visible.

    Uses left-strip heuristic first (robust for fixed-width left ad), then template fallback.
    """
    effective_settings = settings or {}

    strip_present, strip_ratio = _detect_ad_banner_left_strip(
        fixed_width_px=int(effective_settings.get('fixed_width_px', 580)),
        search_top_px=int(effective_settings.get('search_top_px', 450)),
        pixel_threshold=int(effective_settings.get('pixel_threshold', 18)),
        nonblack_ratio_threshold=float(effective_settings.get('nonblack_ratio_threshold', 0.35)),
    )
    if strip_present:
        return True, {
            'method': 'left_strip',
            'score': float(strip_ratio),
        }

    template_full_path = _resolve_local_path(template_path)
    template_img = cv2.imread(template_full_path, cv2.IMREAD_GRAYSCALE)
    if template_img is None:
        return False, {
            'method': 'left_strip_only',
            'score': float(strip_ratio),
        }

    safe_region = search_region
    if safe_region is not None:
        _, _, region_w, region_h = safe_region
        template_h, template_w = template_img.shape
        if template_w > int(region_w) or template_h > int(region_h):
            safe_region = None

    detection = _find_template_match(
        template_path=template_path,
        search_region=safe_region,
        confidence=confidence,
    )
    if detection is not None:
        return True, {
            'method': 'template',
            'score': float(detection.get('score', 0.0)),
        }

    return False, {
        'method': 'left_strip',
        'score': float(strip_ratio),
    }


def get_active_ad_x_offset(config_path='config/ipm_config.json', force_refresh=False):
    """
    Return the active X offset caused by ad banner presence.

    Returns configured offset (default +290) when ad is detected, else 0.
    """
    global _AD_BANNER_CACHE

    settings = _get_ad_banner_settings(config_path=config_path)
    if not settings['enabled']:
        _AD_BANNER_CACHE = {
            'expires_at': 0.0,
            'present': False,
            'offset_x': 0,
        }
        return 0

    now = time.time()
    if (not force_refresh) and now < float(_AD_BANNER_CACHE.get('expires_at', 0.0)):
        return int(_AD_BANNER_CACHE.get('offset_x', 0))

    search_region = None
    try:
        top_px = max(1, int(settings['search_top_px']))
        screen_width, screen_height = pyautogui.size()
        search_region = (0, 0, int(screen_width), int(min(screen_height, top_px)))
    except Exception:
        search_region = None

    is_present, detection_meta = detect_ad_banner(
        template_path=settings['template_path'],
        confidence=float(settings['confidence']),
        search_region=search_region,
        settings=settings,
    )

    active_offset = int(settings['offset_x']) if is_present else 0
    previous_present = bool(_AD_BANNER_CACHE.get('present', False))

    _AD_BANNER_CACHE = {
        'expires_at': now + max(0.2, float(settings['cache_seconds'])),
        'present': is_present,
        'offset_x': active_offset,
        'method': str(detection_meta.get('method', 'unknown')),
        'score': float(detection_meta.get('score', 0.0)),
    }

    if is_present != previous_present:
        if is_present:
            print(
                f"Ad banner detected via {_AD_BANNER_CACHE['method']} "
                f"(score={_AD_BANNER_CACHE['score']:.3f}); applying X offset +{active_offset}px"
            )
        else:
            print(
                f"Ad banner not detected via {_AD_BANNER_CACHE['method']} "
                f"(score={_AD_BANNER_CACHE['score']:.3f}); using X offset +0px"
            )

    return active_offset


def _resolve_runtime_anchor_target_x(config, config_path='config/ipm_config.json', force_refresh_ad=False):
    """
    Resolve runtime target_x from stored anchor mode.

    Modes:
    - normalized: stored target_x is baseline without ad shift.
    - legacy_with_ad_banner: stored target_x was captured while ad was visible.
    """
    settings = _get_ad_banner_settings(config_path=config_path)
    configured_offset_x = int(settings['offset_x'])
    active_offset_x = int(get_active_ad_x_offset(config_path=config_path, force_refresh=force_refresh_ad))

    anchor_mode = str(config.get('anchor_x_mode', 'legacy_with_ad_banner')).strip().lower()
    stored_target_x = int(config['target_x'])

    if anchor_mode == 'normalized':
        return stored_target_x + active_offset_x

    if anchor_mode == 'legacy_with_ad_banner':
        return stored_target_x - configured_offset_x + active_offset_x

    return stored_target_x + active_offset_x


def _resolve_runtime_x_from_mode(stored_x, mode, config_path='config/ipm_config.json', force_refresh_ad=False):
    """Resolve runtime X from a stored X using mode + current ad state."""
    settings = _get_ad_banner_settings(config_path=config_path)
    configured_offset_x = int(settings['offset_x'])
    active_offset_x = int(get_active_ad_x_offset(config_path=config_path, force_refresh=force_refresh_ad))
    normalized_mode = str(mode or 'legacy_with_ad_banner').strip().lower()

    if normalized_mode == 'normalized':
        return int(stored_x) + active_offset_x

    if normalized_mode == 'legacy_with_ad_banner':
        return int(stored_x) - configured_offset_x + active_offset_x

    return int(stored_x) + active_offset_x


def _get_grid_x_mode(config_path='config/ipm_config.json'):
    """Get how grid X coordinates were originally captured."""
    try:
        config_full_path = _resolve_local_path(config_path)
        if os.path.exists(config_full_path):
            with open(config_full_path, 'r', encoding='utf-8') as config_file:
                config = json.load(config_file)
            return str(config.get('grid_x_mode', 'legacy_with_ad_banner')).strip().lower() or 'legacy_with_ad_banner'
    except Exception:
        pass
    return 'legacy_with_ad_banner'


def find_reference_icon(template_path='config/ref_icon.png', search_region=None, confidence=0.75):
    """
    Find the reference icon on screen using template matching.

    Returns dict with center and match score, or None if not found.
    """
    try:
        detection = _find_template_match(
            template_path=template_path,
            search_region=search_region,
            confidence=confidence,
        )
        if detection is None:
            template_full_path = _resolve_local_path(template_path)
            if not os.path.exists(template_full_path):
                print(f"Reference icon not found or unreadable: {template_full_path}")
            return None
        return detection
    except Exception as e:
        print(f"Error finding reference icon: {e}")
        return None


def save_reference_icon_anchor(template_path='config/ref_icon.png', config_path='config/ipm_config.json', confidence=0.75):
    """
    Detect current reference icon position and save as startup anchor coordinates.
    """
    detection = find_reference_icon(template_path=template_path, confidence=confidence)
    if not detection:
        return None

    config_full_path = _resolve_local_path(config_path)
    existing_scroll_start_grid = 'T9'
    existing_currency_region_start_grid = 'I1'
    existing_currency_region_end_grid = 'P2'
    existing_scroll_up_amount = 100
    existing_scroll_down_amount = -30
    if os.path.exists(config_full_path):
        try:
            with open(config_full_path, 'r', encoding='utf-8') as existing_config_file:
                existing_config = json.load(existing_config_file)
            existing_scroll_start_grid = str(existing_config.get('scroll_start_grid', 'T9')).strip().upper() or 'T9'
            existing_currency_region_start_grid = str(existing_config.get('currency_region_start_grid', 'I1')).strip().upper() or 'I1'
            existing_currency_region_end_grid = str(existing_config.get('currency_region_end_grid', 'P2')).strip().upper() or 'P2'
            existing_scroll_up_amount = int(existing_config.get('scroll_up_amount', 100))
            existing_scroll_down_amount = int(existing_config.get('scroll_down_amount', -30))
        except Exception:
            existing_scroll_start_grid = 'T9'
            existing_currency_region_start_grid = 'I1'
            existing_currency_region_end_grid = 'P2'
            existing_scroll_up_amount = 100
            existing_scroll_down_amount = -30

    ad_offset_x = get_active_ad_x_offset(config_path=config_path, force_refresh=True)
    normalized_target_x = int(detection['center_x']) - int(ad_offset_x)

    payload = {
        'template_path': template_path,
        'target_x': normalized_target_x,
        'target_y': detection['center_y'],
        'anchor_x_mode': 'normalized',
        'scroll_start_grid': existing_scroll_start_grid,
        'currency_region_start_grid': existing_currency_region_start_grid,
        'currency_region_end_grid': existing_currency_region_end_grid,
        'scroll_up_amount': existing_scroll_up_amount,
        'scroll_down_amount': existing_scroll_down_amount,
        'tolerance_px': 30,
        'confidence': confidence,
        'saved_at': datetime.now().isoformat(),
    }
    with open(config_full_path, 'w', encoding='utf-8') as config_file:
        json.dump(payload, config_file, indent=2)

    print(
        f"Saved reference icon anchor: ({payload['target_x']}, {payload['target_y']}) "
        f"[normalized by ad offset {ad_offset_x}px] -> {config_full_path}"
    )
    return payload


def align_screen_to_reference_icon(config_path='config/ipm_config.json', tolerance_px=30, max_attempts=8):
    """
    Align the map by dragging until the reference icon is within tolerance.
    """
    try:
        config_full_path = _resolve_local_path(config_path)
        if not os.path.exists(config_full_path):
            print(f"Reference config not found: {config_full_path}")
            return False

        with open(config_full_path, 'r', encoding='utf-8') as config_file:
            config = json.load(config_file)

        template_path = config.get('template_path', 'config/ref_icon.png')
        target_x = _resolve_runtime_anchor_target_x(
            config=config,
            config_path=config_path,
            force_refresh_ad=True,
        )
        target_y = int(config['target_y'])

        for attempt in range(1, max_attempts + 1):
            detection = find_reference_icon(template_path=template_path, confidence=float(config.get('confidence', 0.75)))
            if not detection:
                print(f"Reference icon not found on attempt {attempt}/{max_attempts}")
                return False

            current_x = detection['center_x']
            current_y = detection['center_y']
            dx = target_x - current_x
            dy = target_y - current_y

            if abs(dx) <= tolerance_px and abs(dy) <= tolerance_px:
                print(f"Reference aligned within tolerance ({tolerance_px}px): dx={dx}, dy={dy}")
                return True

            # Use slightly longer drags so BlueStacks consistently registers map movement.
            # Apply a larger fraction of remaining offset each attempt.
            step_dx = int(max(-140, min(140, dx * 0.7)))
            step_dy = int(max(-110, min(110, dy * 0.7)))

            # Ensure drag distance is substantial enough to be recognized.
            min_drag_distance_px = 35
            step_distance = math.hypot(step_dx, step_dy)
            if step_distance > 0 and step_distance < min_drag_distance_px:
                scale = float(min_drag_distance_px) / float(step_distance)
                step_dx = int(round(step_dx * scale))
                step_dy = int(round(step_dy * scale))

            # Ensure we still move when non-zero offset exists
            if step_dx == 0 and dx != 0:
                step_dx = 1 if dx > 0 else -1
            if step_dy == 0 and dy != 0:
                step_dy = 1 if dy > 0 else -1

            pyautogui.moveTo(current_x, current_y, duration=0.12)
            log_input_event('mouse_move', '', '', f'x={current_x};y={current_y};phase=alignment_drag_start;attempt={attempt}')

            # Break movement into moderate chunks: long enough to register, short enough to avoid inertia.
            chunk_count = max(1, max(abs(step_dx) // 45, abs(step_dy) // 45))
            chunk_dx = step_dx / chunk_count
            chunk_dy = step_dy / chunk_count

            # Explicitly hold mouse during drag to avoid intermittent release.
            pyautogui.mouseDown(button='left')
            log_input_event('mouse_down', '', '', f'x={current_x};y={current_y};attempt={attempt}')
            try:
                for chunk_index in range(chunk_count):
                    this_dx = int(round(chunk_dx))
                    this_dy = int(round(chunk_dy))
                    if this_dx == 0 and step_dx != 0:
                        this_dx = 1 if step_dx > 0 else -1
                    if this_dy == 0 and step_dy != 0:
                        this_dy = 1 if step_dy > 0 else -1

                    pyautogui.moveRel(this_dx, this_dy, duration=0.22)
                    log_input_event(
                        'mouse_drag',
                        '',
                        '',
                        f'start_x={current_x};start_y={current_y};dx={this_dx};dy={this_dy};attempt={attempt};chunk={chunk_index+1}/{chunk_count}'
                    )
                    time.sleep(0.06)
            finally:
                pyautogui.mouseUp(button='left')
                log_input_event('mouse_up', '', '', f'attempt={attempt}')

            # Allow post-drag momentum to settle before re-detection.
            time.sleep(0.45)

        print(f"Could not align within {max_attempts} attempts")
        return False
    except Exception as e:
        print(f"Error aligning to reference icon: {e}")
        return False


def _get_ocr_reader():
    global _OCR_READER
    if _OCR_READER is None:
        print("Initializing OCR reader (first run may take a moment)...")
        _OCR_READER = easyocr.Reader(['en'])
    return _OCR_READER


def _parse_compact_currency(value_text):
    """
    Parse compact currency strings like:
    - 61.91K
    - 1,234
    - 2.5M
    Returns integer value or None.
    """
    if not value_text:
        return None

    cleaned = value_text.upper().replace(',', '').replace(' ', '')
    match = re.match(r'^(\d+(?:\.\d+)?)([KMBTQ]?)$', cleaned)
    if not match:
        return None

    number = float(match.group(1))
    suffix = match.group(2)

    multiplier = 1
    if suffix == 'K':
        multiplier = 1_000
    elif suffix == 'M':
        multiplier = 1_000_000
    elif suffix == 'B':
        multiplier = 1_000_000_000
    elif suffix == 'T':
        multiplier = 1_000_000_000_000
    elif suffix == 'Q':
        multiplier = 1_000_000_000_000_000

    return int(number * multiplier)


def _extract_currency_from_texts(texts):
    """
    Extract currency from OCR text snippets.
    Prefers '$' anchored matches but has a fallback compact-number match.
    """
    parsed_candidates = []

    def _append_parsed(raw_value):
        parsed = _parse_compact_currency(raw_value)
        if parsed is not None:
            parsed_candidates.append(parsed)

    # 1) Strong matches: numbers that follow '$' in each OCR snippet.
    for text in texts:
        text_upper = text.upper()
        anchored_matches = re.findall(r'\$\s*([\d][\d,]*(?:\.\d+)?\s*[KMBTQ]?)', text_upper)
        for match_value in anchored_matches:
            _append_parsed(match_value)

    # 2) Join all snippets and try again.
    # Also test a compacted version to handle split OCR tokens like "$4" + ".5Q".
    joined = ' '.join(t.upper() for t in texts)
    joined_compact = re.sub(r'\s+', '', joined)

    anchored_joined_matches = re.findall(r'\$\s*([\d][\d,]*(?:\.\d+)?\s*[KMBTQ]?)', joined)
    for match_value in anchored_joined_matches:
        _append_parsed(match_value)

    anchored_joined_compact_matches = re.findall(r'\$([\d][\d,]*(?:\.\d+)?[KMBTQ]?)', joined_compact)
    for match_value in anchored_joined_compact_matches:
        _append_parsed(match_value)

    # 3) Fallback: compact number with suffix even if '$' is missed by OCR.
    fallback_matches = re.findall(r'\b([\d][\d,]*(?:\.\d+)?\s*[KMBTQ])\b', joined)
    for match_value in fallback_matches:
        _append_parsed(match_value)

    fallback_compact_matches = re.findall(r'\b([\d][\d,]*(?:\.\d+)?[KMBTQ])\b', joined_compact)
    for match_value in fallback_compact_matches:
        _append_parsed(match_value)

    if parsed_candidates:
        return max(parsed_candidates)

    return None


def _save_currency_debug_screenshot(screenshot, region, debug_dir, debug_filename='currency_region_latest.png'):
    """Save the OCR crop image for debugging where currency detection is looking."""
    if not debug_dir:
        return None

    output_dir = _build_debug_output_dir(debug_dir)
    if output_dir is None:
        return None

    x, y, width, height = region
    filename = str(debug_filename).strip() or 'currency_region_latest.png'
    output_path = os.path.join(output_dir, filename)
    screenshot.save(output_path)

    name_root, name_ext = os.path.splitext(filename)
    same_target_prefix = f"{name_root}_"
    stale_debug_files = []
    for entry in os.scandir(output_dir):
        if not entry.is_file():
            continue
        if entry.path == output_path:
            continue
        if entry.name.startswith(same_target_prefix) and entry.name.endswith(name_ext):
            stale_debug_files.append(entry.path)

    for file_path in stale_debug_files:
        try:
            os.remove(file_path)
        except OSError:
            pass

    return output_path


def get_grid_midpoint(
    grid_code,
    coords_file='../grid_overlay/screen_grid_coords.txt',
    box_size=100,
    config_path='config/ipm_config.json',
    apply_ad_offset=True,
):
    """
    Read a grid code (e.g., 'O15') and return the midpoint coordinates of that cell.
    
    Args:
        grid_code: Grid cell code (e.g., 'O15')
        coords_file: Path to ../grid_overlay/screen_grid_coords.txt
        box_size: Size of each grid cell in pixels (default 100)
    
    Returns:
        Tuple (x, y) of the cell midpoint, or None if not found
    """
    try:
        # Ensure grid code is uppercase
        grid_code = grid_code.upper().strip()

        if not os.path.isabs(coords_file):
            local_candidate = os.path.join(os.path.dirname(os.path.abspath(__file__)), coords_file)
            if os.path.exists(local_candidate):
                coords_file = local_candidate
        
        # Read the coordinates file
        with open(coords_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith(grid_code + ':'):
                    # Parse line like "O15:x=1400,y=1400"
                    parts = line.strip().split(':')
                    if len(parts) == 2:
                        coords = parts[1]  # "x=1400,y=1400"
                        x_str = coords.split(',')[0].split('=')[1]  # Extract 1400 from x=1400
                        y_str = coords.split(',')[1].split('=')[1]  # Extract 1400 from y=1400
                        
                        x = int(x_str)
                        y = int(y_str)
                        
                        # Return midpoint (add half of box_size to get center)
                        midpoint_x = x + (box_size // 2)
                        midpoint_y = y + (box_size // 2)

                        if apply_ad_offset:
                            midpoint_x = _resolve_runtime_x_from_mode(
                                stored_x=midpoint_x,
                                mode=_get_grid_x_mode(config_path=config_path),
                                config_path=config_path,
                                force_refresh_ad=False,
                            )
                        
                        return (midpoint_x, midpoint_y)
        
        print(f"Grid code '{grid_code}' not found in {coords_file}")
        return None
        
    except FileNotFoundError:
        print(f"Coordinates file '{coords_file}' not found")
        return None
    except Exception as e:
        print(f"Error reading grid coordinates: {e}")
        return None


def get_grid_region(
    top_left_code,
    bottom_right_code,
    coords_file='../grid_overlay/screen_grid_coords.txt',
    box_size=100,
    config_path='config/ipm_config.json',
    apply_ad_offset=True,
):
    """
    Return a screenshot region tuple (x, y, width, height) bounded by two grid cells.

    Example: J1 to L2 with box_size=100 -> (900, 0, 300, 200)
    """
    try:
        if not os.path.isabs(coords_file):
            local_candidate = os.path.join(os.path.dirname(os.path.abspath(__file__)), coords_file)
            if os.path.exists(local_candidate):
                coords_file = local_candidate

        lookup = {}
        with open(coords_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or ':' not in line:
                    continue
                label, raw_coords = line.split(':', 1)
                parts = raw_coords.split(',')
                if len(parts) != 2:
                    continue
                x = int(parts[0].split('=')[1])
                y = int(parts[1].split('=')[1])
                lookup[label.upper()] = (x, y)

        start = lookup.get(top_left_code.upper())
        end = lookup.get(bottom_right_code.upper())
        if not start or not end:
            print(f"Could not find grid bounds: {top_left_code} to {bottom_right_code}")
            return None

        x1, y1 = start
        x2, y2 = end
        width = (x2 - x1) + box_size
        height = (y2 - y1) + box_size
        if apply_ad_offset:
            x1 = _resolve_runtime_x_from_mode(
                stored_x=x1,
                mode=_get_grid_x_mode(config_path=config_path),
                config_path=config_path,
                force_refresh_ad=False,
            )

        return (x1, y1, width, height)
    except Exception as e:
        print(f"Error building grid region: {e}")
        return None


def open_resources_interface(
    interface_search_start='M17',
    interface_search_end='V17',
    verify_search_start='S8',
    verify_search_end='V9',
    closed_icon_template='config/icons/tabs/closed/resources_icon_closed.png',
    resource_window_template='config/icons/tabs/resource_window.png',
    click_confidence=0.75,
    verify_confidence=0.75,
    window_height_trim_ratio=0.2,
):
    """
    Open the Resources interface by clicking the closed icon in the taskbar region,
    then verify the resource window appears in the verification region.
    """
    log_input_event(
        'interface_check',
        '',
        '',
        (
            f'name=resources;icon_template={closed_icon_template};window_template={resource_window_template};'
            f'icon_region={interface_search_start}-{interface_search_end};verify_region={verify_search_start}-{verify_search_end}'
        )
    )

    interface_region = get_grid_region(interface_search_start, interface_search_end)
    if interface_region is None:
        print("Could not resolve interface search region for resources icon")
        return False

    closed_match = _find_template_match(
        template_path=closed_icon_template,
        search_region=interface_region,
        confidence=float(click_confidence),
    )

    verify_region = get_grid_region(verify_search_start, verify_search_end)
    if verify_region is None:
        print("Could not resolve verification region for resources window")
        return False

    vx, vy, vw, vh = verify_region
    trim = max(0, int(vh * float(window_height_trim_ratio)))
    trimmed_verify_region = (vx, vy + trim, vw, max(1, vh - (trim * 2)))

    if closed_match is None:
        existing_window = _find_template_match(
            template_path=resource_window_template,
            search_region=trimmed_verify_region,
            confidence=float(verify_confidence),
        )
        if existing_window is not None:
            print(
                "Resources interface appears already open "
                f"(score={existing_window['score']:.3f})"
            )
            return True

        print("resources_icon_closed not found in taskbar region")
        return False

    click_x = int(closed_match['center_x'])
    click_y = int(closed_match['center_y'])
    pyautogui.moveTo(click_x, click_y, duration=0.1)
    log_input_event('mouse_move', '', '', f'x={click_x};y={click_y};target=resources_icon_closed')
    pyautogui.click(click_x, click_y)
    log_input_event('mouse_click', '', '', f'x={click_x};y={click_y};button=left;target=resources_icon_closed')
    time.sleep(0.35)

    verified_window = _find_template_match(
        template_path=resource_window_template,
        search_region=trimmed_verify_region,
        confidence=float(verify_confidence),
    )
    if verified_window is not None:
        print("resources tab opened, window confirmed")
        log_input_event(
            'interface_check',
            '',
            '',
            f'name=resources;status=opened_confirmed;score={float(verified_window["score"]):.4f}'
        )
        return True

    print("Clicked resources icon but could not verify resource window")
    return False


def open_bluestacks():
    """
    Opens BlueStacks App Player or brings it to focus if already running.
    If minimized, it will be restored and brought to the foreground.
    """
    try:
        # Try to find the BlueStacks window
        windows = gw.getWindowsWithTitle('BlueStacks')
        
        if windows:
            # BlueStacks is already running, bring it to focus
            bluestacks_window = windows[0]
            bluestacks_window.activate()
            print("BlueStacks brought to focus")
        else:
            # BlueStacks is not running, launch it
            # Try common installation paths
            possible_paths = [
                r"C:\Program Files\BlueStacks\BlueStacks.exe",
                r"C:\Program Files (x86)\BlueStacks\BlueStacks.exe",
                r"C:\Program Files\BlueStacks_nxt\BlueStacks.exe",
            ]
            
            launched = False
            for path in possible_paths:
                if os.path.exists(path):
                    subprocess.Popen(path)
                    print(f"BlueStacks launched from {path}")
                    launched = True
                    time.sleep(0.5)  # Wait for BlueStacks to start
                    break
            
            if not launched:
                print("Could not find BlueStacks installation")
                
    except Exception as e:
        print(f"Error opening BlueStacks: {e}")


def zoom_to_max():
    """
    Zoom in to maximum using configured scroll amount.
    """
    scroll_up_amount, _ = _get_zoom_scroll_amounts(config_path='config/ipm_config.json')
    time.sleep(0.5)  # Wait for BlueStacks to be ready before zoom input

    pyautogui.keyDown(_ZOOM_MODIFIER_KEY)
    time.sleep(0.5)
    for i in range(5):
        pyautogui.scroll(scroll_up_amount)
        log_input_event('mouse_scroll', '', '', f'amount={scroll_up_amount};zoom_in_iter={i+1}')
        time.sleep(0.2)
    pyautogui.keyUp(_ZOOM_MODIFIER_KEY)
    time.sleep(0.5)
    print("Zoomed in to maximum")


def zoom_out_configured_amount():
    """
    Zoom out by the configured amount.
    """
    _, scroll_down_amount = _get_zoom_scroll_amounts(config_path='config/ipm_config.json')
    time.sleep(0.5)

    pyautogui.keyDown(_ZOOM_MODIFIER_KEY)
    time.sleep(0.4)
    for i in range(5):
        pyautogui.scroll(scroll_down_amount)
        log_input_event('mouse_scroll', '', '', f'amount={scroll_down_amount};zoom_out_iter={i+1}')
        time.sleep(0.1)
    pyautogui.keyUp(_ZOOM_MODIFIER_KEY)
    time.sleep(0.4)
    print("Zoomed out by configured amount")


def zoom_to_max_then_down_one():
    """
    Backward-compatible zoom sequence:
    1) Zoom in to maximum
    2) Zoom out by configured amount
    """
    zoom_to_max()
    zoom_out_configured_amount()


def get_currency_value_with_visualization(region=(0, 0, 1920, 150), display=True, debug_dir=None, debug_filename='currency_region_latest.png'):
    """
    Captures currency value from the game window using OCR.
    
    Args:
        region: Tuple (x, y, width, height) for the screenshot region
        display: (Kept for compatibility, not used currently)
    
    Returns:
        Integer value of the currency, or None if not found
    """
    try:
        # Take screenshot of the specified region
        screenshot = pyautogui.screenshot(region=region)

        # Save OCR target crop for debugging if requested
        _save_currency_debug_screenshot(screenshot, region, debug_dir, debug_filename=debug_filename)

        # Reuse OCR reader for faster repeated polling
        reader = _get_ocr_reader()
        
        # Extract text from screenshot
        screenshot_np = np.array(screenshot)
        text_results = reader.readtext(screenshot_np)
        detected_texts = [item[1] for item in text_results if len(item) > 1]

        currency_value = _extract_currency_from_texts(detected_texts)
        if currency_value is not None:
            return currency_value
        
        print(f"Currency value not found in region. OCR saw: {detected_texts}")
        return None
        
    except Exception as e:
        print(f"Error getting currency value: {e}")
        return None
