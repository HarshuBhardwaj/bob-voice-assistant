
from core.screen_control import ScreenControl
from core.universal_control import UniversalControl


def main():
    screen = ScreenControl()
    mouse = UniversalControl()

    target = input("Enter exact text to click: ").strip()

    confirm = input(
        f"Allow BOB to click the position for {target!r}? (yes/no): "
    ).strip().casefold()

    if confirm != "yes":
        print("Click cancelled.")
        return

    try:
        success = screen.click_text(
            target,
            mouse_control=mouse,
        )

        if success:
            print("Click command executed.")
        else:
            print("Click was not performed.")

    except Exception as error:
        print(f"Click test failed: {error}")


if __name__ == "__main__":
    main()
