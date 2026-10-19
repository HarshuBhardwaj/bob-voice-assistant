
import queue
import threading
import tkinter as tk
from tkinter import scrolledtext

from config.settings import APP_NAME
from core.voice_engine import VoiceEngine
from core.command_router import CommandRouter


class BobApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_NAME} Assistant")
        self.root.geometry("700x500")

        self.events = queue.Queue()
        self.command_queue = queue.Queue()

        self.closing = False
        self.listener_thread = None
        self.command_thread = None

        self.status_label = tk.Label(
            root,
            text="Status: Initializing",
            font=("Arial", 14)
        )
        self.status_label.pack(pady=10)

        self.log_area = scrolledtext.ScrolledText(
            root,
            width=75,
            height=20,
            state="disabled"
        )
        self.log_area.pack(padx=10, pady=10)

        self.write_log("BOB Assistant initialized.")

        self.command_router = CommandRouter(
            on_response=self.handle_command_response
        )

        self.voice_engine = VoiceEngine(
            on_command=self.queue_command,
            on_status=self.queue_status
        )

        # Start the sequential command worker.
        self.command_thread = threading.Thread(
            target=self.command_worker,
            daemon=True,
            name="BOBCommandWorker"
        )
        self.command_thread.start()

        # Poll GUI events on Tkinter's main thread.
        self.root.after(100, self.process_events)

        # Close cleanly when the window is closed.
        self.root.protocol(
            "WM_DELETE_WINDOW",
            self.close_app
        )

    def write_log(self, message):
        self.log_area.config(state="normal")
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state="disabled")

    def queue_status(self, status):
        if not self.closing:
            self.events.put(("status", status))

    def queue_command(self, text):
        if not self.closing:
            self.events.put(("user_command", text))
            self.command_queue.put(text)

    def handle_command_response(self, message):
        if not self.closing:
            self.events.put(("response", message))

    def command_worker(self):
        while True:
            command = self.command_queue.get()

            try:
                if command is None:
                    return

                if self.closing:
                    continue

                print(f"Executing command: {command}")
                self.command_router.process_command(command)

            except Exception as error:
                print(f"Command execution error: {error}")
                self.handle_command_response(
                    f"Command failed: {error}"
                )

            finally:
                self.command_queue.task_done()

    def process_events(self):
        if self.closing:
            return

        try:
            while True:
                event_type, value = self.events.get_nowait()

                if event_type == "status":
                    self.status_label.config(
                        text=f"Status: {value}"
                    )

                elif event_type == "user_command":
                    self.write_log(f"You: {value}")

                elif event_type == "response":
                    self.write_log(f"BOB: {value}")

        except queue.Empty:
            pass

        if not self.closing:
            self.root.after(100, self.process_events)

    def start_listening(self):
        # Do not create duplicate microphone listeners.
        if (
            self.listener_thread is not None
            and self.listener_thread.is_alive()
        ):
            return

        self.listener_thread = threading.Thread(
            target=self.voice_engine.listen_continuously,
            daemon=True,
            name="BOBVoiceListener"
        )
        self.listener_thread.start()

        self.write_log("Continuous listening started.")

    def close_app(self):
        self.closing = True
        self.voice_engine.stop_listening()

        # Release a worker waiting for the next command.
        self.command_queue.put(None)

        self.root.destroy()
