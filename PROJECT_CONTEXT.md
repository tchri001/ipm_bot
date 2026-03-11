# Project Context

## Purpose
Python automation bot for a mobile game running in BlueStacks App Player.

## Current Architecture
- `src/main.py`: Entry point and startup sequence.
- `src/utilities.py`: Low-level utilities and core runtime functions.
- `src/interaction.py`: Mid-level layer (currently empty).
- `src/gameplay.py`: High-level layer (currently empty).

## Startup Flow
1. Start quit listener thread (`q` key exits process).
2. Initialize fresh run log.
3. Open/focus BlueStacks App Player and record window bounds.

## Key Behaviors Implemented
- Detect BlueStacks window by title: `BlueStacks App Player`.
- Save `game_window` bounds (`x`, `y`, `width`, `height`) into `src/config.json`.
- Detect ad-banner presence using `assets/reference/bs_icon.png` in top 5 percent strip.
- If banner exists, detect dark-to-light transition in top 10 px and adjust `game_window.x` and `game_window.width`.
- Search for images in configurable percentage regions within `game_window`.
- Save each image-search region screenshot to `debugging/image_searches/`.
- Write run logs to `debugging/game_log.txt`.

## Logging + Debug Outputs
- Run log path: `debugging/game_log.txt`.
- Search screenshot path: `debugging/image_searches/`.
- Log resets each run.

## Dependencies
- `pyautogui`
- `opencv-python`
- `numpy`
- `Pillow`

## Notes
- User preference: implement only exactly specified logic, no extra fallback behavior unless explicitly requested.
- Session-end trigger configured in `.github/copilot-instructions.md` using phrases like `end session` to run context + memory updates.
- Additional session-end trigger phrases configured: `cheers dude`, `thanks for the help`, `see ya`.
