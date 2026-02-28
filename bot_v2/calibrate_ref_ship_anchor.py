import json
import os
from datetime import datetime

from utils import find_reference_icon, _resolve_local_path


def calibrate_anchor(template_path='config/ref_ship.png', config_path='config/ipm_config.json', confidence=0.75):
    detection = find_reference_icon(template_path=template_path, confidence=confidence)
    if not detection:
        print(
            f"Could not find template on screen: {template_path}. "
            "Make sure the game window is visible and the screenshot matches current UI."
        )
        return False

    config_full_path = _resolve_local_path(config_path)
    os.makedirs(os.path.dirname(config_full_path), exist_ok=True)

    payload = {}
    if os.path.exists(config_full_path):
        try:
            with open(config_full_path, 'r', encoding='utf-8') as config_file:
                payload = json.load(config_file)
        except Exception:
            payload = {}

    payload['template_path'] = template_path
    payload['target_x'] = int(detection['center_x'])
    payload['target_y'] = int(detection['center_y'])
    payload['confidence'] = float(confidence)
    payload['saved_at'] = datetime.now().isoformat()

    if 'tolerance_px' not in payload:
        payload['tolerance_px'] = 30

    with open(config_full_path, 'w', encoding='utf-8') as config_file:
        json.dump(payload, config_file, indent=2)

    print(f"Anchor updated using {template_path}")
    print(f"target_x={payload['target_x']}, target_y={payload['target_y']}")
    print(f"Saved config: {config_full_path}")
    return True


if __name__ == '__main__':
    calibrate_anchor()
