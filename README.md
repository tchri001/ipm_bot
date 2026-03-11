# Mobile Game Bot

Layered Python automation framework for controlling a mobile game running in an emulator.

## Architecture

- `utilities`: Technical primitives (screen capture, template matching, mouse/keyboard control).
- `interaction`: Game interactions composed from low-level primitives.
- `gameplay`: Gameplay policy and orchestration.

## Quick Start

1. Create and activate a virtual environment.
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Run:
   - `python -m src.main`

## Notes

Currently opens the app, records game window location and size, adjusts the window details based on whether or not an ad banner is present.
Image detection function saves a screenshot of the search region.
Logging starts new on each run.
Press 'q' to terminate the program at any point.
