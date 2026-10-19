
from pathlib import Path
import subprocess
import sys
import re


class FileControl:
    def __init__(self):
        self.home = Path.home()
        self.current_directory = self.home

        self.special_folders = {
            "desktop": self.home / "Desktop",
            "desktop folder": self.home / "Desktop",
            "downloads": self.home / "Downloads",
            "downloads folder": self.home / "Downloads",
            "documents": self.home / "Documents",
            "documents folder": self.home / "Documents",
            "home": self.home,
            "home folder": self.home,
        }

        self.extensions = (
            "png", "jpg", "jpeg", "gif", "webp", "bmp",
            "pdf", "csv", "txt", "py", "ipynb",
            "docx", "doc", "xlsx", "xls", "json",
            "mp3", "wav", "mp4", "mov", "html",
            "css", "js", "pptx", "zip", "xml",
            "md", "log", "sql", "parquet"
        )

    def normalize_filename(self, name):
        """Convert spoken filenames into standard filenames."""
        name = name.strip().casefold()

        # Convert spoken punctuation
        name = re.sub(r"\bunder[\s-]*score\b", "_", name)
        name = re.sub(r"\bunderscore\b", "_", name)
        name = re.sub(r"\bdot\b", ".", name)

        # Remove spaces around punctuation
        name = re.sub(r"\s*\.\s*", ".", name)
        name = re.sub(r"\s*_\s*", "_", name)

        # Convert "heart csv" into "heart.csv"
        for ext in self.extensions:
            name = re.sub(
                rf"\s+{re.escape(ext)}$",
                f".{ext}",
                name
            )

        return re.sub(r"\s+", " ", name).strip()

    def open_folder(self, folder_name):
        """Set the current directory and open it in the OS file manager."""
        folder_name = folder_name.strip().casefold()

        if folder_name in ("back", "go back", "previous folder"):
            return self.go_back()

        if folder_name in ("here", "this folder", "current folder"):
            folder = self.current_directory
        else:
            folder = self.special_folders.get(folder_name)

            if folder is None:
                folder = self.current_directory / folder_name

        try:
            if not folder.exists() or not folder.is_dir():
                print(f"Folder not found: {folder}")
                return False

            # Update BOB's current working directory
            self.current_directory = folder

            # Open the folder visibly in the operating system
            if sys.platform == "darwin":
                subprocess.Popen(["open", str(folder)])
            elif sys.platform.startswith("win"):
                import os
                os.startfile(str(folder))
            else:
                subprocess.Popen(["xdg-open", str(folder)])

            print(f"Opened folder: {folder}")
            return True

        except (OSError, subprocess.SubprocessError) as error:
            print(f"Could not open folder: {error}")
            return False

    def go_back(self):
        """Move to the parent directory and open it."""
        parent = self.current_directory.parent

        if parent == self.current_directory:
            print("Already at the root directory.")
            return False

        return self.open_folder(str(parent))

    def show_current_directory(self):
        """Print and return the current directory."""
        print(f"Current directory: {self.current_directory}")
        return self.current_directory

    def find_file(self, filename):
        """Search common folders and their subfolders for a file."""
        filename = self.normalize_filename(filename)

        search_directories = [
            self.current_directory,
            self.home / "Desktop",
            self.home / "Downloads",
            self.home / "Documents",
        ]

        checked = set()

        for directory in search_directories:
            try:
                if not directory.is_dir():
                    continue

                resolved = str(directory.resolve())

                if resolved in checked:
                    continue

                checked.add(resolved)

                # Try an exact path first
                exact_match = directory / filename

                if exact_match.is_file():
                    return exact_match

                # Search subfolders
                for path in directory.rglob("*"):
                    if path.is_file() and path.name.casefold() == filename:
                        return path

            except OSError as error:
                print(f"Could not search {directory}: {error}")

        return None

    def open_file(self, filename):
        """Find and open a file using the operating system."""
        filename = self.normalize_filename(filename)
        file_path = self.find_file(filename)

        if file_path is None:
            print(f"File not found: {filename}")
            return False

        try:
            if sys.platform == "darwin":
                subprocess.Popen(["open", str(file_path)])
            elif sys.platform.startswith("win"):
                import os
                os.startfile(str(file_path))
            else:
                subprocess.Popen(["xdg-open", str(file_path)])

            print(f"Opened file: {file_path}")
            return True

        except (OSError, subprocess.SubprocessError) as error:
            print(f"Could not open file: {error}")
            return False
