"""Basic macOS desktop and browser keyboard automation for BOB."""

from datetime import datetime
from pathlib import Path
import subprocess

import pyautogui


class DesktopControl:
    """Performs predictable desktop actions using macOS keyboard shortcuts."""

    @staticmethod
    def _hotkey(*keys):
        try:
            pyautogui.hotkey(*keys)
            return True
        except Exception as error:
            print(f"Desktop hotkey {keys} failed: {error}")
            return False

    def minimize_window(self):
        # macOS shortcut: Command+M
        return self._hotkey("command", "m")

    def maximize_window(self):
        # Ask macOS Accessibility to click the front window's Zoom button.
        script = '''tell application "System Events"
    set frontApp to first application process whose frontmost is true
    tell frontApp
        if (count of windows) is 0 then return false
        try
            click (first button of front window whose subrole is "AXZoomButton")
            return true
        on error
            return false
        end try
    end tell
end tell'''
        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                check=True,
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.stdout.strip().lower() == "true"
        except (OSError, subprocess.SubprocessError) as error:
            print(f"Window zoom failed: {error}")
            return False

    def toggle_fullscreen(self):
        # Control+Command+F is the standard macOS full-screen shortcut.
        return self._hotkey("ctrl", "command", "f")

    def exit_fullscreen(self):
        # Same shortcut toggles full screen off in most macOS apps.
        return self._hotkey("ctrl", "command", "f")

    def switch_app(self):
        # Leaves the app switcher visible so the user can choose an app.
        return self._hotkey("command", "tab")

    def new_tab(self):
        return self._hotkey("command", "t")

    def close_tab(self):
        return self._hotkey("command", "w")

    def next_tab(self):
        # Chrome and many browsers support Control+Tab.
        return self._hotkey("ctrl", "tab")

    def previous_tab(self):
        return self._hotkey("ctrl", "shift", "tab")

    def focus_address_bar(self):
        # In Chrome this focuses the address/search bar.
        return self._hotkey("command", "l")

    def take_screenshot(self):
        try:
            desktop = Path.home() / "Desktop"
            desktop.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = desktop / f"BOB_screenshot_{timestamp}.png"
            pyautogui.screenshot().save(path)
            return str(path)
        except Exception as error:
            print(f"Screenshot failed: {error}")
            return False
    def switch_to_app(self, app_name):
        """Bring a named macOS application to the foreground."""
        aliases = {
            "chrome": "Google Chrome",
            "google chrome": "Google Chrome",
            "whatsapp": "WhatsApp",
            "finder": "Finder",
            "safari": "Safari",
            "notes": "Notes",
            "calendar": "Calendar",
            "mail": "Mail",
            "messages": "Messages",
            "terminal": "Terminal",
            "visual studio code": "Visual Studio Code",
            "vs code": "Visual Studio Code",
            "spotify": "Spotify",
            "music": "Music",
        }
        requested = " ".join((app_name or "").strip().split())
        if not requested:
            return False
        app = aliases.get(requested.casefold(), requested)
        # Escape AppleScript string characters; app names are not shell commands.
        escaped = app.replace("\\", "\\\\").replace('"', '\\"')
        script = f'tell application "{escaped}" to activate'
        try:
            subprocess.run(
                ["osascript", "-e", script],
                check=True, capture_output=True, text=True, timeout=10,
            )
            return True
        except (OSError, subprocess.SubprocessError) as error:
            print(f"Could not switch to {app}: {error}")
            return False