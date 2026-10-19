
from core.screen_control import ScreenControl


def main():
    screen = ScreenControl()

    target = input("Enter text to find on screen: ").strip()

    try:
        matches = screen.find_text(target)

        if not matches:
            print(f"No matching text found for: {target!r}")
            return

        print(f"\nFound {len(matches)} matching result(s):")

        for item in matches:
            print(
                f"Text: {item['text']!r} | "
                f"Position: ({item['x']}, {item['y']}) | "
                f"Confidence: {item['confidence']}"
            )

    except Exception as error:
        print(f"Text search failed: {error}")


if __name__ == "__main__":
    main()
