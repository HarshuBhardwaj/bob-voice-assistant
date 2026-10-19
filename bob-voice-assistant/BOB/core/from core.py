from core.pc_control import PCControl

from core.browser_control import BrowserControl

from core.file_control import FileControl

from core.app_control import AppControl
from core.universal_control import UniversalControl
import re

class CommandRouter:

    def __init__(self, on_response):

        self.on_response = on_response

        self.pc_control = PCControl()

        self.browser_control = BrowserControl()

        self.file_control = FileControl()

        self.app_control = AppControl()
        self.universal_control = UniversalControl()
        self.cursor_mode = False
        self.cursor_direction = "up"
        self.cursor_step = 40

    def process_command(self, text):

        raw_text = text.strip()
        command = raw_text.lower().strip()

        # 1. Search YouTube without automatically playing a video

        if command.startswith("search youtube for "):

            query = command.removeprefix(

                "search youtube for "

            ).strip()

            if not query:

                self.on_response(

                    "Please tell me what to search on YouTube."

                )

                return

            self.on_response(f"Searching YouTube for {query}...")

            success = self.browser_control.search_youtube_results(query)

            if success:

                self.on_response(

                    "YouTube results are ready. Say play the "

                    "first, second, third, fourth, or fifth video."

                )

            else:

                self.on_response("Could not load YouTube results.")

        # 2. Play a numbered video from current YouTube results

        elif command in (

            "play the first video", "play first video",

            "click the first video", "click first video",

            "play the second video", "play second video",

            "click the second video", "click second video",

            "play the third video", "play third video",

            "click the third video", "click third video",

            "play the fourth video", "play fourth video",

            "click the fourth video", "click fourth video",

            "play the fifth video", "play fifth video",

            "click the fifth video", "click fifth video",

        ):

            video_numbers = {

                "first": 1,

                "second": 2,

                "third": 3,

                "fourth": 4,

                "fifth": 5,

            }

            number = next(

                (

                    value

                    for word, value in video_numbers.items()

                    if word in command

                ),

                None

            )

            if number is None:

                self.on_response("Please specify a video number.")

                return

            self.on_response(f"Opening video number {number}...")

            success = self.browser_control.click_youtube_video(number)

            if not success:

                self.on_response(

                    "Could not open that video. "

                    "Search YouTube first and try again."

                )

        # 3. Search YouTube and open the first result

        elif command.startswith("play "):

            query = command.removeprefix("play ").strip()

            if not query:

                self.on_response(

                    "Please tell me what you want to play."

                )

                return

            self.on_response(f"Searching YouTube for {query}...")

            success = self.browser_control.play_youtube_video(query)

            if not success:

                self.on_response(

                    "Could not open the first YouTube result."

                )

        # 4. Explicit Google search

        elif command.startswith("search google for "):

            query = command.removeprefix(

                "search google for "

            ).strip()

            if not query:

                self.on_response(

                    "Please tell me what to search on Google."

                )

                return

            self.on_response(f"Searching Google for {query}...")

            success = self.pc_control.search_google(query)

            if not success:

                self.on_response("Could not search Google.")

        # 5. General search defaults to Google

        elif command.startswith("search for "):

            query = command.removeprefix("search for ").strip()

            if not query:

                self.on_response("Please tell me what to search for.")

                return

            self.on_response(f"Searching Google for {query}...")

            success = self.pc_control.search_google(query)

            if not success:

                self.on_response("Could not search Google.")

        # 6. Open Chrome using the existing PCControl

        elif command in ("open chrome", "open google chrome"):

            self.on_response("Opening Google Chrome...")

            success = self.pc_control.open_app("Google Chrome")

            if not success:

                self.on_response("Could not open Google Chrome.")

        # 7. Open YouTube website

        elif command in ("open youtube", "open you tube"):

            self.on_response("Opening YouTube...")

            success = self.pc_control.open_website(

                "https://www.youtube.com"

            )

            if not success:

                self.on_response("Could not open YouTube.")

        # 8. Close a supported application

        elif command.startswith("close "):

            app_name = command.removeprefix("close ").strip()

            if app_name.startswith("application "):

                app_name = app_name.removeprefix(

                    "application "

                ).strip()

            elif app_name.startswith("app "):

                app_name = app_name.removeprefix("app ").strip()

            if app_name not in self.app_control.applications:

                self.on_response(

                    f"Unsupported application: {app_name}."

                )

                return

            self.on_response(f"Closing {app_name}...")

            success = self.app_control.close_app(app_name)

            if success:

                self.on_response(

                    f"Quit requested for {app_name}."

                )

            else:

                self.on_response(

                    f"Could not close {app_name}."

                )

        # 9. Navigate to the parent folder

        elif command in (

            "go back",

            "go back folder",

            "go to parent folder",

        ):

            success = self.file_control.go_back()

            if success:

                self.on_response(

                    "Went back. Current folder is "

                    f"{self.file_control.current_directory.name}."

                )

            else:

                self.on_response("Could not go back.")

        # 10. Show the current directory

        elif command in (

            "where am i",

            "where am i?",

            "show current directory",

            "current directory",

        ):

            path = self.file_control.show_current_directory()

            self.on_response(f"Your current directory is {path}.")

        # 11. Open Desktop

        elif command in (

            "open desktop",

            "open the desktop",

            "open my desktop",

        ):

            self.on_response("Opening Desktop...")

            success = self.file_control.open_folder("desktop")

            if success:

                self.on_response("Desktop opened.")

            else:

                self.on_response("Could not open Desktop.")

        # 12. Open Home folder

        elif command in ("open home", "open home folder"):

            self.on_response("Opening your home folder...")

            success = self.file_control.open_folder("home")

            if success:

                self.on_response("Home folder opened.")

            else:

                self.on_response("Could not open the home folder.")

        # 13. Open a folder by name or path

        elif command.startswith("open folder "):

            folder_name = command.removeprefix(

                "open folder "

            ).strip()

            if not folder_name:

                self.on_response(

                    "Please specify a folder name or path."

                )

                return

            self.on_response(f"Opening folder {folder_name}...")

            success = self.file_control.open_folder(folder_name)

            if success:

                self.on_response(

                    f"Folder opened: "

                    f"{self.file_control.current_directory.name}."

                )

            else:

                self.on_response(

                    f"Could not open folder {folder_name}."

                )

        # 14. Open a file by name

        elif command.startswith("open file "):

            file_name = command.removeprefix(

                "open file "

            ).strip()

            if not file_name:

                self.on_response("Please specify a file name.")

                return

            self.on_response(f"Searching for {file_name}...")

            success = self.file_control.open_file(file_name)

            if success:

                self.on_response(f"Opening file {file_name}.")

            else:

                self.on_response(f"Could not find {file_name}.")

        # 15. Open a supported application, folder, or file

        elif command.startswith("open "):

            target = command.removeprefix("open ").strip()

            if target.startswith("my "):

                target = target.removeprefix("my ").strip()

            if target.endswith(" folder"):

                target = target.removesuffix(" folder").strip()

            if not target:

                self.on_response("Please tell me what to open.")

                return

            # NEW: Recognize "application X" and "app X"

            if target.startswith("application "):

                target = target.removeprefix(

                    "application "

                ).strip()

            elif target.startswith("app "):

                target = target.removeprefix("app ").strip()

            # NEW: Launch an app only if it is in AppControl's list

            if target in self.app_control.applications:

                self.on_response(f"Opening {target}...")

                success = self.app_control.launch_app(target)

                if success:

                    self.on_response(f"Opened {target}.")

                else:

                    self.on_response(f"Could not open {target}.")

                return

            # Existing folder and file handling

            if target in ("desktop", "home"):

                success = self.file_control.open_folder(target)

            else:

                target_path = (

                    self.file_control.current_directory / target

                )

                success = self.file_control.open_folder(

                    str(target_path)

                )

                if not success:

                    success = self.file_control.open_file(target)

            if success:

                self.on_response(f"Opened {target}.")

            else:

                self.on_response(

                    f"Could not find {target} in the current location."

                )

        # 16. Mouse positioning and continuous cursor movement
        elif command in ("stop cursor", "stop mouse", "stop moving"):
            self.cursor_mode = False
            self.on_response("Cursor movement mode stopped.")

        elif command in (
            "move cursor up", "move cursor down",
            "move cursor left", "move cursor right",
            "move cursor up left", "move cursor up right",
            "move cursor down left", "move cursor down right",
            "move mouse up", "move mouse down",
            "move mouse left", "move mouse right",
            "move mouse up left", "move mouse up right",
            "move mouse down left", "move mouse down right",
        ):
            self.cursor_direction = command.removeprefix("move cursor ").removeprefix("move mouse ")
            self.cursor_mode = True
            success = self.universal_control.move_relative(
                self.cursor_direction, self.cursor_step
            )
            self.on_response(
                f"Cursor moving {self.cursor_direction}. Say a direction to continue, or stop cursor."
                if success else "Could not move the cursor."
            )

        elif command.startswith(("move cursor to ", "move mouse to ")):
            position = command
            if position.startswith("move cursor to "):
                position = position.removeprefix("move cursor to ")
            else:
                position = position.removeprefix("move mouse to ")
            position = position.strip()
            position = re.sub(r"\s+", " ", position)
            success = self.universal_control.move_to_position(position)
            self.on_response(
                f"Moved cursor to {position}." if success
                else f"Unknown screen position: {position}."
            )

        elif command in ("faster", "move faster"):
            self.cursor_step = min(self.cursor_step + 20, 200)
            self.on_response(f"Cursor step is now {self.cursor_step} pixels.")

        elif command in ("slower", "move slower"):
            self.cursor_step = max(self.cursor_step - 20, 10)
            self.on_response(f"Cursor step is now {self.cursor_step} pixels.")

        elif command in (
            "up", "down", "left", "right",
            "up left", "up right", "down left", "down right",
        ) and self.cursor_mode:
            self.cursor_direction = command
            success = self.universal_control.move_relative(
                self.cursor_direction, self.cursor_step
            )
            if not success:
                self.on_response("Could not move the cursor.")

        elif self.cursor_mode and re.fullmatch(
            r"(up|down|left|right)(?:\s+\1)+", command
        ):
            # Handle a recognized phrase such as "up up up".
            directions = command.split()
            success = True
            for direction in directions:
                success = self.universal_control.move_relative(
                    direction, self.cursor_step
                ) and success
            if not success:
                self.on_response("Could not complete cursor movement.")

        # 17. Mouse and keyboard voice controls
        elif command in ("click", "click mouse", "single click"):
            success = self.universal_control.click()
            self.on_response("Clicked." if success else "Mouse click failed.")

        elif command in ("double click", "double-click"):
            success = self.universal_control.click(clicks=2)
            self.on_response("Double-clicked." if success else "Double-click failed.")

        elif command in ("scroll down", "scroll up"):
            direction = command.removeprefix("scroll ")
            success = self.universal_control.scroll(direction, 3)
            self.on_response(
                f"Scrolled {direction}." if success else "Scrolling failed."
            )

        elif command.startswith("type "):
            typed_text = raw_text[5:].strip()
            if not typed_text:
                self.on_response("Please tell me what to type.")
            else:
                success = self.universal_control.type_text(typed_text)
                self.on_response("Text typed." if success else "Typing failed.")

        elif command.startswith("press "):
            key_phrase = command.removeprefix("press ").strip()
            shortcut_keys = key_phrase.split()
            modifiers = {"command", "cmd", "shift", "control", "ctrl", "option", "alt"}
            key_map = {"cmd": "command", "ctrl": "ctrl", "alt": "option"}
            shortcut_keys = [key_map.get(key, key) for key in shortcut_keys]

            if len(shortcut_keys) >= 2 and any(
                key in modifiers for key in key_phrase.split()[:-1]
            ):
                success = self.universal_control.hotkey(*shortcut_keys)
            else:
                single_key_map = {
                    "return": "enter", "escape": "esc",
                    "spacebar": "space", "delete": "backspace",
                }
                key = single_key_map.get(key_phrase, key_phrase)
                success = self.universal_control.press_key(key)

            self.on_response(
                "Keyboard action completed." if success
                else "Keyboard action failed."
            )

        # 18. Unknown command
        else:
            self.on_response(
                "Sorry, I don't recognize that command."
            )
