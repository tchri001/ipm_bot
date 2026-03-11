# Mobile Game Bot

Layered Python automation framework for controlling a mobile game running in an emulator.

## Architecture

- `low_level`: Technical primitives (screen capture, template matching, mouse/keyboard control).
- `mid_level`: Game interactions composed from low-level primitives.
- `high_level`: Gameplay policy and orchestration.

## Quick Start

1. Create and activate a virtual environment.
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Run:
   - `python -m src.main`

## Notes

- Keep game-specific behavior out of `low_level`.
- Keep strategy decisions in `high_level`.
- Keep repeated interaction patterns in `mid_level`.
