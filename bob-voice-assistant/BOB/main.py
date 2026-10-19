
import tkinter as tk

from config.settings import APP_NAME, ASSISTANT_VERSION
from gui.app import BobApp


def main():
    print(f"{APP_NAME} Assistant is starting...")
    print(f"Version: {ASSISTANT_VERSION}")

    root = tk.Tk()
    app = BobApp(root)

    root.after(100, app.start_listening)

    root.mainloop()


if __name__ == "__main__":
    main()
