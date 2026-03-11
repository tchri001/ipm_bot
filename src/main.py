from utilities import (
    initialize_game_log,
    open_and_focus_bluestacks_app_player,
    start_quit_listener_thread,
)


def main() -> None:
    start_quit_listener_thread()
    initialize_game_log()
    open_and_focus_bluestacks_app_player()


if __name__ == "__main__":
    main()
