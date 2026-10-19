import pyautogui


class UniversalControl:
    """Basic mouse and keyboard control for macOS desktop applications."""

    def __init__(self):
        pyautogui.PAUSE = 0.15
        pyautogui.FAILSAFE = True

    def click(self, x=None, y=None, clicks=1, button="left"):
        try:
            if x is not None and y is not None:
                pyautogui.click(
                    x=int(x), y=int(y), clicks=int(clicks), button=button
                )
            else:
                pyautogui.click(clicks=int(clicks), button=button)
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

    def move_relative(self, direction, distance=40):
        """Move the cursor a fixed number of pixels in a direction."""
        try:
            x, y = pyautogui.position()
            width, height = pyautogui.size()
            distance = abs(int(distance))
            moves = {
                "up": (0, -distance),
                "down": (0, distance),
                "left": (-distance, 0),
                "right": (distance, 0),
                "up left": (-distance, -distance),
                "up right": (distance, -distance),
                "down left": (-distance, distance),
                "down right": (distance, distance),
            }
            if direction not in moves:
                print(f"Unsupported direction: {direction}")
                return False
            dx, dy = moves[direction]
            new_x = max(0, min(width - 1, x + dx))
            new_y = max(0, min(height - 1, y + dy))
            return self.move_mouse(new_x, new_y)
        except Exception as error:
            print(f"Relative mouse movement failed: {error}")
            return False

    def move_to_position(self, position):
        """Move the cursor to the center, an edge, or a screen corner."""
        try:
            width, height = pyautogui.size()
            margin = min(10, max(0, min(width, height) // 10))
            positions = {
                "center": (width // 2, height // 2),
                "centre": (width // 2, height // 2),
                "top": (width // 2, margin),
                "bottom": (width // 2, height - 1 - margin),
                "left": (margin, height // 2),
                "right": (width - 1 - margin, height // 2),
                "top left": (margin, margin),
                "top right": (width - 1 - margin, margin),
                "bottom left": (margin, height - 1 - margin),
                "bottom right": (width - 1 - margin, height - 1 - margin),
            }
            position = " ".join(str(position).casefold().split())
            if position not in positions:
                print(f"Unsupported screen position: {position}")
                return False
            x, y = positions[position]
            return self.move_mouse(x, y)
        except Exception as error:
            print(f"Screen positioning failed: {error}")
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
            pyautogui.hotkey(*(key.casefold().strip() for key in keys))
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
