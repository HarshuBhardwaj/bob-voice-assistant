
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
        """Open WhatsApp search and type a contact name."""

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
            # Step 1: Open search using Command + F.
            pyautogui.keyDown("command")
            try:
                pyautogui.press("f")
            finally:
                pyautogui.keyUp("command")

            time.sleep(1.5)

            # Step 2: Type the contact name.
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
        """Select a search result using macOS keyboard events."""

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

            # Two Down Arrow presses followed by Return.
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
            self.contact_search_performed = True

            print("Selection keys executed. Verify the correct chat.")
            return True

        except subprocess.CalledProcessError as error:
            print(f"AppleScript failed: {error}")
            print(f"AppleScript stderr: {error.stderr}")
            return False

        except (OSError, subprocess.SubprocessError) as error:
            print(f"Contact selection error: {error}")
            return False

    def type_message(self, message):
        """Type a message without sending it."""

        message = message.strip()

        if not message:
            print("Message cannot be empty.")
            return False

        if not self.contact_search_performed:
            print("Search for and select a contact first.")
            return False

        try:
            # Bring WhatsApp to the foreground after Terminal input.
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

            # Use the same typing method that already works.
            pyautogui.write(message, interval=0.12)
            time.sleep(1)

            self.pending_message = message
            print("Message typed. It has NOT been sent.")
            return True

        except (OSError, subprocess.SubprocessError) as error:
            print(f"WhatsApp activation error: {error}")
            return False

        except Exception as error:
            print(f"Message typing error: {error}")
            return False

    def send_message(self):
        """Send the pending message after explicit confirmation."""

        if not self.pending_message:
            print("No pending message to send.")
            return False

        print("\nPlease verify before sending:")
        print(f"Contact entered: {self.pending_contact}")
        print(f"Message: {self.pending_message}")

        confirmation = input(
            "\nIf the correct chat and message are visible, "
            "type YES to send: "
        ).strip()

        if confirmation.casefold() != "yes":
            print("Sending cancelled. Message was not sent by BOB.")
            return False

        try:
            # Return to WhatsApp after Terminal confirmation.
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

            # Send the message currently in the WhatsApp composer.
            pyautogui.press("enter")
            time.sleep(1)

            self.pending_message = ""
            print("Send key pressed. Check WhatsApp to confirm delivery.")
            return True

        except (OSError, subprocess.SubprocessError) as error:
            print(f"WhatsApp activation error: {error}")
            return False

        except Exception as error:
            print(f"Message sending error: {error}")
            return False


if __name__ == "__main__":
    whatsapp = WhatsAppControl()

    # Collect both inputs before starting WhatsApp automation.
    contact = input("Enter contact name: ").strip()
    message = input("Enter message: ").strip()

    if whatsapp.search_contact(contact):
        input(
            "\nWait for the search results. Press Enter in Terminal "
            "when you are ready to select the contact..."
        )

        if whatsapp.select_contact():
            proceed = input(
                "\nVerify the correct chat is open. "
                "Type YES in Terminal to type the message: "
            ).strip()

            if proceed.casefold() == "yes":
                if whatsapp.type_message(message):
                    whatsapp.send_message()
            else:
                print("Cancelled. Message was not typed or sent.")
    else:
        print("Contact search failed.")
