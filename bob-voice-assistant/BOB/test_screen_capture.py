
from core.screen_control import ScreenControl


def main():
    screen = ScreenControl()

    try:
        width, height = screen.get_screen_size()
        print(f"Screen resolution: {width} x {height}")

        print("Capturing screenshot temporarily...")

        with screen.capture_screen() as screenshot:
            print(f"Screenshot captured: {screenshot.size}")
            print("Image is available for analysis inside this block.")

        print("Screenshot closed. No image file was saved.")

    except Exception as error:
        print(f"Screen capture failed: {error}")
        print("Check macOS Screen Recording permission.")


if __name__ == "__main__":
    main()
