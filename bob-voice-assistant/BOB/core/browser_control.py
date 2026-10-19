"""Chrome-based browser control for BOB on macOS.

Uses the user's installed Google Chrome instead of launching Playwright Chromium.
Keyboard navigation works without Playwright. Numbered-result selection uses
Chrome's JavaScript-from-Apple-Events feature when enabled in Chrome settings.
"""
from urllib.parse import quote_plus
import subprocess
import time

import pyautogui


class BrowserControl:
    """Control the normal installed Google Chrome window on macOS."""

    def __init__(self):
        self.last_search_kind = None
        self.last_search_query = ""

    def _run_osascript(self, script, timeout=10):
        return subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=timeout,
        )

    def _activate_chrome(self):
        if __import__("sys").platform != "darwin":
            print("Chrome browser control currently supports macOS only.")
            return False
        try:
            opened = subprocess.run(
                ["open", "-a", "Google Chrome"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if opened.returncode != 0:
                print("Could not open Google Chrome:", (opened.stderr or opened.stdout).strip())
                return False
            activated = self._run_osascript('tell application "Google Chrome" to activate')
            if activated.returncode != 0:
                print("Could not activate Google Chrome:", (activated.stderr or activated.stdout).strip())
                return False
            time.sleep(0.35)
            return True
        except Exception as error:
            print(f"Google Chrome activation failed: {error}")
            return False

    def _navigate(self, url):
        if not self._activate_chrome():
            return False
        try:
            pyautogui.hotkey("command", "l")
            time.sleep(0.15)
            pyautogui.write(url, interval=0.001)
            pyautogui.press("enter")
            time.sleep(1.2)
            return True
        except Exception as error:
            print(f"Chrome navigation failed: {error}")
            return False

    @staticmethod
    def _escape_applescript_string(value):
        # AppleScript quoted strings use backslash escaping for quotes/backslashes.
        return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")

    def _execute_javascript(self, javascript):
        """Run JS in the active Chrome tab; requires Chrome's Apple Events JS setting."""
        if not self._activate_chrome():
            return None
        escaped = self._escape_applescript_string(javascript)
        script = (
            'tell application "Google Chrome"\n'
            'if (count of windows) is 0 then return "NO_WINDOW"\n'
            f'execute active tab of front window javascript "{escaped}"\n'
            'end tell'
        )
        try:
            result = self._run_osascript(script, timeout=12)
            if result.returncode != 0:
                detail = (result.stderr or result.stdout or "unknown AppleScript error").strip()
                if "Allow JavaScript from Apple Events" in detail or "JavaScript" in detail:
                    print("Chrome JavaScript control is unavailable. In Chrome, enable View > Developer > Allow JavaScript from Apple Events.")
                else:
                    print(f"Chrome result automation failed: {detail}")
                return None
            return (result.stdout or "").strip()
        except Exception as error:
            print(f"Chrome JavaScript automation failed: {error}")
            return None

    def start_browser(self):
        """Open/activate normal Google Chrome; kept for router compatibility."""
        return self._activate_chrome()

    def _ensure_page(self):
        # Compatibility with the previous Playwright implementation.
        return self._activate_chrome()

    def _foreground(self):
        return self._activate_chrome()

    def focus_address_bar(self):
        if not self._activate_chrome():
            return False
        try:
            pyautogui.hotkey("command", "l")
            return True
        except Exception as error:
            print(f"Chrome address bar focus failed: {error}")
            return False

    def new_tab(self):
        if not self._activate_chrome():
            return False
        try:
            pyautogui.hotkey("command", "t")
            return True
        except Exception as error:
            print(f"Chrome new tab failed: {error}")
            return False

    def close_tab(self):
        if not self._activate_chrome():
            return False
        try:
            pyautogui.hotkey("command", "w")
            return True
        except Exception as error:
            print(f"Chrome close tab failed: {error}")
            return False

    def refresh_page(self):
        if not self._activate_chrome():
            return False
        try:
            pyautogui.hotkey("command", "r")
            return True
        except Exception as error:
            print(f"Chrome refresh failed: {error}")
            return False

    def go_back(self):
        if not self._activate_chrome():
            return False
        try:
            pyautogui.hotkey("command", "[")
            return True
        except Exception as error:
            print(f"Chrome back failed: {error}")
            return False

    def go_forward(self):
        if not self._activate_chrome():
            return False
        try:
            pyautogui.hotkey("command", "]")
            return True
        except Exception as error:
            print(f"Chrome forward failed: {error}")
            return False

    def search_google_results(self, query):
        query = (query or "").strip()
        if not query:
            print("Google search query cannot be empty.")
            return False
        self.last_search_kind = "google"
        self.last_search_query = query
        return self._navigate("https://www.google.com/search?q=" + quote_plus(query))

    def open_search_result(self, number):
        if number < 1:
            return False
        # Select an organic Google result in the current Chrome tab.
        result = self._execute_javascript(
            "(() => { const a = Array.from(document.querySelectorAll('#search a')).filter(x => x.querySelector('h3') && x.href); "
            f"if (a.length < {int(number)}) return 'NOT_FOUND'; a[{int(number)-1}].click(); return 'CLICKED'; }})()"
        )
        if result and "CLICKED" in result:
            time.sleep(1.0)
            return True
        if result and "NOT_FOUND" in result:
            print(f"Google organic result {number} was not found on the current page.")
        else:
            print("To select numbered Google results, enable 'Allow JavaScript from Apple Events' in Chrome. Search/navigation still works without it.")
        return False

    def search_youtube_results(self, query):
        query = (query or "").strip()
        if not query:
            print("YouTube search query cannot be empty.")
            return False
        self.last_search_kind = "youtube"
        self.last_search_query = query
        return self._navigate("https://www.youtube.com/results?search_query=" + quote_plus(query))

    def click_youtube_video(self, number):
        if number < 1:
            return False
        # Count video cards, not both title and thumbnail links for each video.
        result = self._execute_javascript(
            "(() => { const cards = Array.from(document.querySelectorAll('ytd-video-renderer')) "
            ".filter(card => card.querySelector('a#video-title[href*=\"/watch\"]')); "
            f"if (cards.length < {int(number)}) return 'NOT_FOUND'; "
            f"const card = cards[{int(number)-1}]; "
            "const link = card.querySelector('a#thumbnail[href*=\"/watch\"]') || "
            "card.querySelector('a#video-title[href*=\"/watch\"]'); "
            "if (!link) return 'NOT_FOUND'; link.click(); return 'CLICKED'; })()"
        )
        if result and "CLICKED" in result:
            time.sleep(1.0)
            return True
        if result and "NOT_FOUND" in result:
            print(f"YouTube video result {number} was not found on the current page.")
        else:
            print("To select numbered YouTube results, enable 'Allow JavaScript from Apple Events' in Chrome.")
        return False

    def play_youtube_video(self, query):
        if not self.search_youtube_results(query):
            return False
        time.sleep(2.0)
        return self.click_youtube_video(1)

    def stop(self):
        """No persistent Playwright process is used by the Chrome implementation."""
        return True
