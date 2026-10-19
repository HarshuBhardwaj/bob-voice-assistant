
from core.screen_control import ScreenControl


def main():
    screen = ScreenControl()

    try:
        print("BOB S4.2 - Screen Text Detection")
        print("Reading visible text from the current screen...")

        results = screen.read_screen_text()

        if not results:
            print("No text detected on the screen.")
            return

        for item in results:
            print(
                f"Text: {item['text']!r} | "
                f"Confidence: {item['confidence']} | "
                f"Position: ({item['x']}, {item['y']})"
            )

        print(f"\nTotal text regions: {len(results)}")

    except Exception as error:
        print(f"OCR test failed: {error}")


if __name__ == "__main__":
    main()
