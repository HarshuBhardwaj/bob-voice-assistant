
import subprocess
import sys
import time

import pyautogui


class WhatsAppControl:
    def __init__(self):
        self.pending_message = ""
        self.pending_contact = ""
        self.contact_search_performed = False

    def activate_whatsapp(self):
        """Open WhatsApp Desktop and bring it to the foreground."""

        if sys.platform != "darwin":
            print("This version supports macOS only.")
            return False

        try:
            subprocess.run(
                ["open", "-a", "WhatsApp"],
                check=True,
                capture_output=True,
                text=True,
                timeout=15,
            )

            subprocess.run(
                [
                    "osascript",
                    "-e",
                    'tell application "WhatsApp" to activate',
                ],
                check=True,
                capture_output=True,
                text=True,
                timeout=10,
            )

            time.sleep(2)
            return True

        except (OSError, subprocess.SubprocessError) as error:
            print(f"WhatsApp activation error: {error}")
            return False

    def search_contact(self, contact_name):
        """Open search and type a contact name."""

        contact_name = contact_name.strip()

        if not contact_name:
            print("Contact name cannot be empty.")
            return False

        self.contact_search_performed = False
        self.pending_contact = ""
        self.pending_message = ""

        if not self.activate_whatsapp():
            return False

        try:
            # Open WhatsApp search using Command + F.
            pyautogui.keyDown("command")
            try:
                pyautogui.press("f")
            finally:
                pyautogui.keyUp("command")

            time.sleep(1.5)

            # Type the contact name using the working search method.
            pyautogui.write(contact_name, interval=0.12)
            time.sleep(2)

            self.pending_contact = contact_name
            print(f"Search results ready for: {contact_name}")
            return True

        except Exception as error:
            print(f"Contact search error: {error}")
            return False

        finally:
            pyautogui.keyUp("command")

    def select_contact(self):
        """Select the contact using macOS keyboard events."""

        if not self.pending_contact:
            print("Search for a contact first.")
            return False

        try:
            subprocess.run(
                [
                    "osascript",
                    "-e",
                    'tell application "WhatsApp" to activate',
                ],
                check=True,
                capture_output=True,
                text=True,
                timeout=10,
            )

            time.sleep(1.5)

            script = """
            tell application "System Events"
                key code 125
                delay 0.5
                key code 125
                delay 0.8
                key code 36
            end tell
            """

            subprocess.run(
                ["osascript", "-e", script],
                check=True,
                capture_output=True,
                text=True,
                timeout=10,
            )

            time.sleep(2)

            # Mark selection as attempted; verify the chat visually.
            self.contact_search_performed = True

            print("Selection keys executed. Verify the correct chat.")
            return True

        except (OSError, subprocess.SubprocessError) as error:
            print(f"Contact selection error: {error}")
            return False

    def type_message(self, message):
        """Type a message into the open WhatsApp chat without sending."""

        message = message.strip()

        if not message:
            print("Message cannot be empty.")
            return False

        if not self.contact_search_performed:
            print("Search for and select a contact first.")
            return False

        try:
            # Restore WhatsApp after Terminal input.
            subprocess.run(
                [
                    "osascript",
                    "-e",
                    'tell application "WhatsApp" to activate',
                ],
                check=True,
                capture_output=True,
                text=True,
                timeout=10,
            )

            time.sleep(1.5)

            # Type using the same method that works for contact search.
            pyautogui.write(message, interval=0.12)
            time.sleep(1)

            self.pending_message = message
            print("Message typed. NOT sent yet.")
            return True

        except (OSError, subprocess.SubprocessError) as error:
            print(f"Could not activate WhatsApp: {error}")
            return False

        except Exception as error:
            print(f"Message typing error: {error}")
            return False


if __name__ == "__main__":
    whatsapp = WhatsAppControl()

    # Collect inputs before switching to WhatsApp.
    contact = input("Enter contact name: ").strip()
    message = input("Enter message: ").strip()

    if whatsapp.search_contact(contact):
        input(
            "Wait for search results, then press Enter in Terminal..."
        )

        if whatsapp.select_contact():
            input(
                "Verify the correct chat is open. "
                "Press Enter in Terminal to type the message..."
            )

            if whatsapp.type_message(message):
                print("Check WhatsApp. The message has not been sent.")
    else:
        print("Contact search failed.")
