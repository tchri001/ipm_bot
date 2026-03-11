# Bootstrap Checklist

Use this checklist to get up and running quickly after restart or on another PC.

## 1. Open Project
- Open workspace root: `ipm_bot`.

## 2. Install Dependencies
- `pip install -r requirements.txt`

## 3. Verify Required Paths
- `src/config.json`
- `assets/reference/bs_icon.png`
- `debugging/`
- `debugging/image_searches/`

## 4. Run App
- `python -m src.main`

## 5. Runtime Expectations
- Press `q` to terminate.
- `debugging/game_log.txt` is recreated on each run.
- BlueStacks window bounds are written to `src/config.json`.
- Image search debug captures are saved to `debugging/image_searches/`.

## 6. If Something Looks Wrong
- Check BlueStacks title exactly matches `BlueStacks App Player`.
- Check `src/config.json` has valid `game_window` values.
- Review latest lines in `debugging/game_log.txt`.
