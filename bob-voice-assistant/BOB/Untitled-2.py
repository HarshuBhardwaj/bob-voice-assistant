
import time
import pyautogui


class UniversalControl:
    """
    Basic mouse and keyboard control for macOS.
    Commands act on the currently focused application.
    """

    def __init__(self):
        # Small delay between PyAutoGUI actions
        pyautogui.PAUSE = 0.15

        # Keep fail-safe enabled:
        # move the mouse to the top-left corner to abort.
        pyautogui.FAILSAFE = True

    def click(self, x=None, y=None, clicks=1, button="left"):
        try:
            if x is not None and y is not None:
                pyautogui.click(
                    x=int(x),
                    y=int(y),
                    clicks=int(clicks),
                    button=button
                )
            else:
                pyautogui.click(
                    clicks=int(clicks),
                    button=button
                )

            return True

        except Exception as error:
            print(f"Mouse click failed: {error}")
            return False

    def move_mouse(self, x, y):
        try:
            pyautogui.moveTo(int(x), int(y), duration=0.2)
            return True

        except Exception as error:
            print(f"Mouse movement failed: {error}")
            return False

    def scroll(self, direction, amount=3):
        try:
            amount = abs(int(amount))
            direction = direction.casefold().strip()

            if direction == "down":
                pyautogui.scroll(-amount)
            elif direction == "up":
                pyautogui.scroll(amount)
            else:
                print("Direction must be 'up' or 'down'.")
                return False

            return True

        except Exception as error:
            print(f"Scrolling failed: {error}")
            return False

    def type_text(self, text):
        try:
            pyautogui.write(str(text), interval=0.03)
            return True

        except Exception as error:
            print(f"Typing failed: {error}")
            return False

    def press_key(self, key):
        try:
            pyautogui.press(key.casefold().strip())
            return True

        except Exception as error:
            print(f"Key press failed: {error}")
            return False

    def hotkey(self, *keys):
        try:
            if not keys:
                print("Please provide at least one key.")
                return False

            pyautogui.hotkey(
                *(key.casefold().strip() for key in keys)
            )
            return True

        except Exception as error:
            print(f"Keyboard shortcut failed: {error}")
            return False

    def get_screen_size(self):
        try:
            width, height = pyautogui.size()
            print(f"Screen size: {width} x {height}")
            return width, height

        except Exception as error:
            print(f"Could not get screen size: {error}")
            return None
