
import re
import time
import speech_recognition as sr


class VoiceEngine:
    def __init__(self, on_command, on_status):
        self.on_command = on_command
        self.on_status = on_status

        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()

        self.is_awake = False
        self.is_running = False
        self._status = None

        # Adaptive sensitivity for changing background noise
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.dynamic_energy_adjustment_damping = 0.15
        self.recognizer.dynamic_energy_ratio = 1.3

        # Speech boundary detection
        self.recognizer.pause_threshold = 0.8
        self.recognizer.non_speaking_duration = 0.4
        self.recognizer.phrase_threshold = 0.2

        # Limit supported network operations
        self.recognizer.operation_timeout = 10

    def _set_status(self, status):
        if status != self._status:
            self._status = status
            try:
                self.on_status(status)
            except Exception as error:
                print(f"Status callback error: {error}")

    @staticmethod
    def normalize_text(text):
        """Normalize recognized words for command matching."""
        text = text.casefold()
        text = re.sub(r"[^\w\s.]", " ", text)
        return re.sub(r"\s+", " ", text).strip()

    def _dispatch_command(self, command):
        command = command.strip()

        if not command:
            return

        print(f"Command queued: {command}")
        self._set_status("Processing command")

        try:
            self.on_command(command)
        except Exception as error:
            print(f"Command callback error: {error}")

        if self.is_awake:
            self._set_status("Listening for command")
        else:
            self._set_status("Waiting for wake word")

    def _process_recognized_text(self, text):
        if not text or not text.strip():
            return

        print(f"Recognized speech: {text}")
        normalized = self.normalize_text(text)

        # Wake-word detection while BOB is asleep
        if not self.is_awake:
            wake_match = re.search(
                r"\bhey\s+(?:bob|bo+|bawb)\b",
                normalized
            )

            # Do not activate for unrelated speech.
            if wake_match is None:
                if normalized == "hey":
                    print(
                        "Heard 'hey'; waiting for the complete wake word."
                    )
                return

            self.is_awake = True
            self._set_status("Active")
            print("BOB is now active.")
            print(f"DEBUG: Wake word detected. Remaining text: "
                f"{normalized[wake_match.end():].strip()!r}")

            # Support commands spoken with the wake word,
            # for example: "Hey Bob, open desktop"
            remaining_command = normalized[wake_match.end():].strip()

            if remaining_command:
                self._dispatch_command(remaining_command)
            else:
                self._set_status("Listening for command")

            return

        # Enter sleep mode without stopping the microphone
        if re.search(r"\bbob\s+sleep\b", normalized):
            self.is_awake = False
            self._set_status("Waiting for wake word")
            print("BOB is sleeping but still listening.")
            return

        # Preserve original recognized text for filenames
        # and commands that need the original wording.
        self._dispatch_command(text)

    def _capture_and_recognize(self, source):
        """Capture one phrase and send it to speech recognition."""
        if self.is_awake:
            self._set_status("Listening for command")
        else:
            self._set_status("Waiting for wake word")

        audio = self.recognizer.listen(
            source,
            timeout=1,
            phrase_time_limit=7
        )

        self._set_status("Recognizing speech")

        text = self.recognizer.recognize_google(
            audio,
            language="en-IN"
        )

        self._process_recognized_text(text)

    def listen_continuously(self):
        if self.is_running:
            print("Listener is already running.")
            return

        self.is_running = True
        print("BOB continuous listener starting...")

        try:
            # Keep one microphone session open
            with self.microphone as source:
                self._set_status("Calibrating microphone")
                print("Please remain quiet during calibration.")

                self.recognizer.adjust_for_ambient_noise(
                    source,
                    duration=1
                )

                print(
                    "Calibration complete. "
                    "Say 'Hey Bob' to activate."
                )

                while self.is_running:
                    try:
                        self._capture_and_recognize(source)

                    except sr.WaitTimeoutError:
                        continue

                    except sr.UnknownValueError:
                        print("Speech captured but not understood.")
                        continue

                    except sr.RequestError as error:
                        self._set_status(
                            "Speech service unavailable"
                        )
                        print(
                            f"Google recognition error: {error}"
                        )
                        time.sleep(1)
                        continue

                    except OSError as error:
                        self._set_status("Microphone error")
                        print(f"Microphone error: {error}")
                        break

                    except Exception as error:
                        print(f"Listening error: {error}")
                        time.sleep(0.2)

        except Exception as error:
            self._set_status("Listener failed")
            print(f"Could not start microphone listener: {error}")

        finally:
            self.is_running = False
            print("BOB continuous listener ended.")

    def stop_listening(self):
        # Called when the application is closing
        self.is_running = False
        self.is_awake = False
        self._set_status("Waiting for wake word")
