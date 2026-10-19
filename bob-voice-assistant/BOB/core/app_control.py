
import subprocess
import sys


class AppControl:
    def __init__(self):
        # Supported applications and their macOS app names.
        self.applications = {
            "chrome": "Google Chrome",
            "google chrome": "Google Chrome",
            "safari": "Safari",
            "vscode": "Visual Studio Code",
            "vs code": "Visual Studio Code",
            "visual studio code": "Visual Studio Code",
            "spotify": "Spotify",
            "finder": "Finder",
            "calculator": "Calculator",
            "notes": "Notes",
            "whatsapp": "WhatsApp",
            "terminal": "Terminal",
        }

    def launch_app(self, app_name):
        """Open an installed macOS application."""

        if sys.platform != "darwin":
            print("AppControl is currently configured for macOS.")
            return False

        app_name = app_name.strip().casefold()
        mac_app_name = self.applications.get(app_name)

        if not mac_app_name:
            print(f"Unsupported application: {app_name}")
            return False

        try:
            result = subprocess.run(
                ["open", "-a", mac_app_name],
                capture_output=True,
                text=True,
                timeout=15
            )

            if result.returncode == 0:
                print(f"Opened application: {mac_app_name}")
                return True

            print(f"Could not open {mac_app_name}: {result.stderr.strip()}")
            return False

        except (OSError, subprocess.SubprocessError) as error:
            print(f"Application launch error: {error}")
            return False

    def close_app(self, app_name):
        """Ask an application to quit normally."""

        if sys.platform != "darwin":
            print("AppControl is currently configured for macOS.")
            return False

        app_name = app_name.strip().casefold()
        mac_app_name = self.applications.get(app_name)

        if not mac_app_name:
            print(f"Unsupported application: {app_name}")
            return False

        try:
            script = (
                f'tell application "{mac_app_name}" to quit'
            )

            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=15
            )

            if result.returncode == 0:
                print(f"Quit requested for: {mac_app_name}")
                return True

            print(f"Could not close {mac_app_name}: {result.stderr.strip()}")
            return False

        except (OSError, subprocess.SubprocessError) as error:
            print(f"Application close error: {error}")
            return False
