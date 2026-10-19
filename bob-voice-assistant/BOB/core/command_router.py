from core.pc_control import PCControl

from core.browser_control import BrowserControl

from core.file_control import FileControl

from core.app_control import AppControl

from core.universal_control import UniversalControl

from core.screen_control import ScreenControl
from core.desktop_control import DesktopControl

import re
import subprocess
import time
import threading

import pyautogui

from core.whatsapp_control import WhatsAppControl
from core.nlu import NaturalLanguageUnderstanding


class CommandRouter:

    def __init__(self, on_response):

        self.on_response = on_response

        self.pc_control = PCControl()

        self.browser_control = BrowserControl()

        self.file_control = FileControl()

        self.app_control = AppControl()

        self.universal_control = UniversalControl()

        self.screen_control = ScreenControl()
        self.desktop_control = DesktopControl()
        self.whatsapp_control = WhatsAppControl()
        self.nlu = NaturalLanguageUnderstanding()
        self.whatsapp_active_contact = ""
        self.whatsapp_pending_contact = ""
        self.whatsapp_pending_message = ""

        self.cursor_mode = False
        # Continuous dictation mode: all recognized speech is typed until stopped.
        self.typing_mode = False

        self.cursor_direction = "up"

        self.cursor_step = 40
        self._scroll_stop_event = threading.Event()
        self._scroll_thread = None
        self._scroll_direction = None

    def _whatsapp_open_chat(self, contact_name):
        """Search for and open a WhatsApp contact."""
        contact_name = contact_name.strip()
        if not contact_name:
            self.on_response("Please tell me which WhatsApp contact to open.")
            return False

        self.on_response(f"Opening WhatsApp chat with {contact_name}...")
        if not self.whatsapp_control.search_contact(contact_name):
            self.on_response("Could not search for that WhatsApp contact.")
            return False

        # Allow the search results to finish rendering before selecting.
        time.sleep(1)
        if not self.whatsapp_control.select_contact():
            self.on_response("Could not select the WhatsApp contact.")
            return False

        self.whatsapp_active_contact = contact_name
        self.on_response(
            f"Selection keys sent for {contact_name}. Verify that the correct chat is open."
        )
        return True

    def _whatsapp_prepare_message(self, contact_name, message):
        """Open a contact if needed, type a message, and request voice confirmation."""
        contact_name = contact_name.strip()
        message = message.strip()
        if not contact_name:
            self.on_response("No WhatsApp contact is selected. Tell me which contact to message.")
            return
        if not message:
            self.on_response("Please tell me what message to send.")
            return

        # If the requested recipient differs from the active chat, search and select it.
        if self.whatsapp_active_contact.casefold() != contact_name.casefold():
            if not self._whatsapp_open_chat(contact_name):
                return

        if not self.whatsapp_control.type_message(message):
            self.on_response("I could not type the WhatsApp message.")
            return

        self.whatsapp_pending_contact = contact_name
        self.whatsapp_pending_message = message
        self.on_response(
            f"Message prepared for {contact_name}: {message}. "
            "Check WhatsApp, then say 'confirm send' to send it, or 'cancel message' to cancel."
        )

    def _whatsapp_send_pending(self):
        """Send the prepared WhatsApp message after explicit voice confirmation."""
        if not self.whatsapp_pending_message or not self.whatsapp_pending_contact:
            self.on_response("There is no WhatsApp message waiting to be sent.")
            return

        try:
            # Return focus to WhatsApp after the voice confirmation was recognized.
            subprocess.run(
                ["osascript", "-e", 'tell application "WhatsApp" to activate'],
                check=True,
                capture_output=True,
                text=True,
                timeout=10,
            )
            time.sleep(1)
            # Use macOS System Events to send Return to the foreground app.
            subprocess.run(
                [
                    "osascript",
                    "-e",
                    'tell application "System Events" to key code 36',
                ],
                check=True,
                capture_output=True,
                text=True,
                timeout=10,
            )
            sent_contact = self.whatsapp_pending_contact
            self.whatsapp_pending_contact = ""
            self.whatsapp_pending_message = ""
            self.whatsapp_control.pending_message = ""
            self.on_response(
                f"Send key pressed for {sent_contact}. Check WhatsApp to confirm delivery."
            )
        except (OSError, subprocess.SubprocessError) as error:
            print(f"WhatsApp send failed: {error}")
            self.on_response("Could not send the WhatsApp message. Check macOS Accessibility permissions.")

    def _start_continuous_scroll(self, direction):
        """Keep scrolling until a stop command is received."""
        self._stop_continuous_scroll(notify=False)
        self._scroll_stop_event = threading.Event()
        self._scroll_direction = direction
        stop_event = self._scroll_stop_event

        def scroll_loop():
            # A short pause between scroll actions keeps the page usable and
            # allows the voice loop to recognize a stop command.
            while not stop_event.is_set():
                try:
                    self.universal_control.scroll(direction, 3)
                except Exception as error:
                    print(f"Continuous scroll failed: {error}")
                    break
                stop_event.wait(0.35)

        self._scroll_thread = threading.Thread(
            target=scroll_loop,
            name="BOBContinuousScroll",
            daemon=True,
        )
        self._scroll_thread.start()
        self.on_response(
            f"Continuous scrolling {direction}. Say 'stop scrolling', 'stop', or 'ruk jao' to stop."
        )

    def _stop_continuous_scroll(self, notify=True):
        """Stop an active continuous scroll loop, if any."""
        was_scrolling = self._scroll_thread is not None and self._scroll_thread.is_alive()
        self._scroll_stop_event.set()
        self._scroll_direction = None
        if notify:
            self.on_response(
                "Scrolling stopped." if was_scrolling else "Continuous scrolling is not active."
            )
        return was_scrolling

    def process_command(self, text):

        raw_text = self.nlu.normalize(text)
        print("Original command:", text)
        print("Normalized command:", raw_text)

        command = raw_text.lower().strip()

        # Browser history and numbered Google website results.
        if command in {"back", "go back", "back page", "go back page", "previous page", "pichhe jao", "peeche jao", "previous website page"}:
            self.on_response("Going back to the previous browser page...")
            success = self.browser_control.go_back()
            if success:
                self.on_response("Returned to the previous browser page.")
            else:
                # The visible browser may be regular Chrome rather than Playwright's managed window.
                # Use the standard macOS/browser back shortcut as a practical fallback.
                try:
                    success = self.universal_control.hotkey("command", "left")
                except Exception:
                    success = False
                self.on_response("Back command sent." if success else "Could not go back. There may be no previous page.")
            return

        website_match = re.fullmatch(
            r"(?:open|click|select) (?:the )?(first|1st|second|2nd|third|3rd|fourth|4th|fifth|5th) (?:website|web site|site|search result|result)",
            command,
        )
        if website_match:
            number_map = {"first": 1, "1st": 1, "second": 2, "2nd": 2, "third": 3, "3rd": 3, "fourth": 4, "4th": 4, "fifth": 5, "5th": 5}
            number = number_map[website_match.group(1)]
            self.on_response(f"Opening Google result {number}...")
            success = self.browser_control.open_search_result(number)
            self.on_response(f"Opened website result {number}." if success else f"Could not open result {number}. Search Google first and make sure results are loaded.")
            return

        # Continuous dictation controls. These are handled before normal routing.
        start_typing_commands = {
            "type mode", "start typing", "start typing mode", "begin dictation",
            "typing mode on", "likhna shuru karo", "typing shuru karo",
            "ab likhna shuru karo", "dictation mode on",
        }
        stop_typing_commands = {
            "stop typing", "stop typing mode", "not type", "typing mode off",
            "stop dictation", "dictation mode off", "likhna band karo",
            "likhna band kar do", "typing band karo", "bas ab mat likho",
        }
        if command in start_typing_commands:
            self.typing_mode = True
            self.on_response("Continuous typing mode is ON. Speak naturally; say 'stop typing' to stop.")
            return

        if command in stop_typing_commands:
            was_typing = self.typing_mode
            self.typing_mode = False
            self.on_response("Continuous typing mode is OFF." if was_typing else "Typing mode was already OFF.")
            return

        # Switch directly to a named app, including while dictation mode is active.
        switch_to_match = re.fullmatch(
            r"(?:switch to|activate|bring up)\s+(.+?)(?:\s+app)?", raw_text.strip(),
            flags=re.IGNORECASE,
        )
        if switch_to_match:
            app_name = switch_to_match.group(1).strip()
            if app_name.casefold() in {"the next app", "another app", "app"}:
                app_name = ""
            if app_name:
                self.on_response(f"Switching to {app_name}...")
                try:
                    success = self.desktop_control.switch_to_app(app_name)
                    self.on_response(
                        f"Switched to {app_name}." if success
                        else f"Could not switch to {app_name}. Check the app name and macOS permissions."
                    )
                except Exception as error:
                    print(f"Switch-to-app failed: {error}")
                    self.on_response(f"Could not switch to {app_name}.")
                return

        # Editing commands work both during and outside continuous typing mode.
        if command in {"delete last character", "backspace", "press backspace", "last character delete karo", "ek character delete karo"}:
            success = self.universal_control.press_key("backspace")
            self.on_response("Deleted the last character." if success else "Backspace failed.")
            return

        if command in {"delete last word", "last word delete karo", "pichhla word delete karo"}:
            success = self.universal_control.hotkey("option", "backspace")
            self.on_response("Deleted the last word." if success else "Could not delete the last word.")
            return

        if command in {"clear line", "clear this line", "line clear karo", "poori line delete karo"}:
            # Select the current field's contents, then remove them.
            success = self.universal_control.hotkey("command", "a") and self.universal_control.press_key("backspace")
            self.on_response("Cleared the current field." if success else "Could not clear the current field.")
            return

        if command in {"delete all", "clear all text", "saara text delete karo"}:
            success = self.universal_control.hotkey("command", "a") and self.universal_control.press_key("backspace")
            self.on_response("Deleted all text in the current field." if success else "Could not delete the text.")
            return

        # In typing mode, ordinary speech is dictated verbatim from the recognized
        # input (not the LLM rewrite) and gets one trailing space. Keyboard/editing
        # controls still go through the normal command router.
        typing_control_commands = {
            "press enter", "press return", "enter", "return", "enter dabao",
            "press tab", "press escape", "press esc", "press backspace",
            "press delete", "press space", "press spacebar",
            "scroll up", "scroll down", "upar scroll karo", "neeche scroll karo",
            "stop scrolling", "stop scroll", "stop", "ruka", "ruk jao", "ruk ja",
            "scroll band karo", "scrolling band karo",
            "switch app", "switch application", "switch window", "switch windows",
            "next window", "change window", "dusri window par jao", "app badlo",
        }
        is_shortcut = command.startswith("press ") and any(
            modifier in command.split()[1:-1]
            for modifier in ("command", "cmd", "shift", "control", "ctrl", "option", "alt")
        )
        if self.typing_mode and command not in typing_control_commands and not is_shortcut:
            dictated_text = (text or "").strip()
            if dictated_text:
                # Don't add duplicate whitespace if recognition already ends with punctuation.
                dictated_text = dictated_text.rstrip() + " "
                success = self.universal_control.type_text(dictated_text)
                self.on_response("Typed." if success else "Typing failed.")
            else:
                self.on_response("I didn't catch any text to type.")
            return

        # Continuous scrolling controls must be handled before ordinary routing.
        if command in {"stop scrolling", "stop scroll", "stop", "ruka", "ruk jao", "ruk ja", "scroll band karo", "scrolling band karo"}:
            self._stop_continuous_scroll()
            return

        if command in {"scroll up", "scroll down", "upar scroll karo", "neeche scroll karo"}:
            direction = "up" if command in {"scroll up", "upar scroll karo"} else "down"
            self._start_continuous_scroll(direction)
            return

        # WhatsApp: handle confirmations/cancellation before other commands.
        if command in ("confirm send", "yes send", "send it", "confirm message"):
            self._whatsapp_send_pending()
            return

        if command in ("cancel message", "cancel whatsapp message", "don't send", "do not send"):
            if self.whatsapp_pending_message:
                self.whatsapp_pending_contact = ""
                self.whatsapp_pending_message = ""
                self.whatsapp_control.pending_message = ""
                self.on_response("WhatsApp message cancelled. It was not sent.")
            else:
                self.on_response("There is no pending WhatsApp message to cancel.")
            return

        # Example: "send a WhatsApp message to Aadi that I will be late".
        direct_message = re.match(
            r"^(?:please\s+)?send\s+(?:a\s+)?whatsapp\s+message\s+to\s+(.+?)\s+that\s+(.+)$",
            raw_text,
            flags=re.IGNORECASE,
        )
        if direct_message:
            self._whatsapp_prepare_message(
                direct_message.group(1), direct_message.group(2)
            )
            return

        # Example: "open Punit Gym chats on WhatsApp".
        open_whatsapp_chat = re.match(
            r"^(?:please\s+)?open\s+(.+?)\s+(?:chat|chats|conversation|conversations)\s+on\s+whatsapp$",
            raw_text,
            flags=re.IGNORECASE,
        )
        if open_whatsapp_chat:
            self._whatsapp_open_chat(open_whatsapp_chat.group(1))
            return

        # Example: after opening a chat, say "send message you're ridiculous".
        current_chat_message = re.match(
            r"^(?:please\s+)?send\s+(?:a\s+)?message\s+(.+)$",
            raw_text,
            flags=re.IGNORECASE,
        )
        if current_chat_message:
            if not self.whatsapp_active_contact:
                self.on_response(
                    "No WhatsApp chat is remembered. First say, 'open [contact] chats on WhatsApp'."
                )
                return
            self._whatsapp_prepare_message(
                self.whatsapp_active_contact, current_chat_message.group(1)
            )
            return

        # Click visible screen text directly, without a separate confirmation.
        if command.startswith("click text "):
            target_text = raw_text[len("click text "):].strip()

            if not target_text:
                self.on_response("Please tell me which text to click.")
                return

            try:
                clicked = self.screen_control.click_text(
                    target_text,
                    self.universal_control,
                    min_confidence=0.7,
                )

                if clicked:
                    self.on_response(f"Clicked {target_text}.")
                else:
                    self.on_response(
                        f"Could not click {target_text}. "
                        "Text may not be visible or may be ambiguous."
                    )
            except Exception as error:
                print(f"Screen click failed: {error}")
                self.on_response("The screen click failed.")

            return

        # Desktop automation commands. Keep these before general open/close routing.
        desktop_actions = {
            "minimize window": ("minimize_window", "Minimizing the current window."),
            "minimize this window": ("minimize_window", "Minimizing the current window."),
            "maximize window": ("maximize_window", "Maximizing the current window."),
            "maximize this window": ("maximize_window", "Maximizing the current window."),
            "fullscreen": ("toggle_fullscreen", "Toggling full screen."),
            "full screen": ("toggle_fullscreen", "Toggling full screen."),
            "exit fullscreen": ("exit_fullscreen", "Exiting full screen."),
            "exit full screen": ("exit_fullscreen", "Exiting full screen."),
            "switch app": ("switch_app", "Switching to the next app."),
            "switch application": ("switch_app", "Switching to the next app."),
            "switch window": ("switch_app", "Switching apps. Use Command+Tab to choose an app."),
            "switch windows": ("switch_app", "Switching apps. Use Command+Tab to choose an app."),
            "next window": ("switch_app", "Switching to the next app."),
            "change window": ("switch_app", "Switching apps."),
            "new tab": ("new_tab", "Opening a new browser tab."),
            "open new tab": ("new_tab", "Opening a new browser tab."),
            "close tab": ("close_tab", "Closing the current browser tab."),
            "next tab": ("next_tab", "Switching to the next tab."),
            "previous tab": ("previous_tab", "Switching to the previous tab."),
            "focus address bar": ("focus_address_bar", "Focusing the browser address bar."),
            "focus search bar": ("focus_address_bar", "Focusing the browser address bar."),
            "go to search bar": ("focus_address_bar", "Focusing the browser address bar."),
            "take screenshot": ("take_screenshot", "Taking a screenshot."),
            "screenshot": ("take_screenshot", "Taking a screenshot."),
        }
        if command in desktop_actions:
            method_name, status_message = desktop_actions[command]
            self.on_response(status_message)
            try:
                result = getattr(self.desktop_control, method_name)()
                if method_name == "take_screenshot" and result:
                    self.on_response(f"Screenshot saved to {result}.")
                elif not result:
                    self.on_response("Desktop action failed. Check macOS permissions and the active app.")
            except Exception as error:
                print(f"Desktop automation failed: {error}")
                self.on_response("Desktop action failed. Check macOS Accessibility permissions.")
            return

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

            success = self.browser_control.search_google_results(query)

            if not success:

                self.on_response("Could not search Google.")

        # 5. General search defaults to Google

        elif command.startswith("search for "):

            query = command.removeprefix("search for ").strip()

            if not query:

                self.on_response("Please tell me what to search for.")

                return

            self.on_response(f"Searching Google for {query}...")

            success = self.browser_control.search_google_results(query)

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

        elif command in ("click", "click it", "click that", "click here", "click karo", "click mouse", "single click"):

            success = self.universal_control.click()

            self.on_response("Clicked." if success else "Mouse click failed.")

        elif command in ("double click", "double-click"):

            success = self.universal_control.click(clicks=2)

            self.on_response("Double-clicked." if success else "Double-click failed.")


        elif command.startswith("type "):

            typed_text = raw_text[5:].strip()

            if not typed_text:

                self.on_response("Please tell me what to type.")

            else:

                # One-shot typing also appends a trailing space for the next word.
                success = self.universal_control.type_text(typed_text.rstrip() + " ")

                self.on_response("Text typed with a trailing space." if success else "Typing failed.")

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