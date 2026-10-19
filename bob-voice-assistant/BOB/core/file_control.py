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
        """Normalize spoken filenames and folder names."""
        name = (name or "").strip().casefold()

        # Convert spoken punctuation and common speech-recognition variants.
        name = re.sub(r"\bunder[\s-]*score\b", "_", name)
        name = re.sub(r"\bunderscore\b", "_", name)
        name = re.sub(r"\bdot\b", ".", name)

        # Remove spaces around punctuation.
        name = re.sub(r"\s*\.\s*", ".", name)
        name = re.sub(r"\s*_\s*", "_", name)

        # Convert "heart csv" into "heart.csv".
        for ext in self.extensions:
            name = re.sub(rf"\s+{re.escape(ext)}$", f".{ext}", name)

        # Collapse repeated whitespace, but keep single spaces in names.
        return re.sub(r"\s+", " ", name).strip()

    @staticmethod
    def _name_key(name):
        """Create a comparison key tolerant of spaces, underscores and hyphens."""
        name = (name or "").casefold().strip()
        name = re.sub(r"\bunder[\s-]*score\b", " ", name)
        name = re.sub(r"\bunderscore\b", " ", name)
        name = re.sub(r"\bdot\b", " dot ", name)
        # Treat spaces, underscores and hyphens equivalently for matching.
        return re.sub(r"[\s_-]+", "", name)

    def _find_child_folder(self, parent, spoken_name):
        """Find a direct child folder even if spoken separators differ."""
        try:
            if not parent.is_dir():
                return None

            wanted = self.normalize_filename(spoken_name)
            wanted_key = self._name_key(wanted)

            # First try exact normalized path.
            exact = parent / wanted
            if exact.is_dir():
                return exact

            # Then compare normalized names to actual child directory names.
            for child in parent.iterdir():
                if child.is_dir():
                    child_name = self.normalize_filename(child.name)
                    if child_name == wanted or self._name_key(child.name) == wanted_key:
                        return child
        except OSError as error:
            print(f"Could not search folders in {parent}: {error}")

        return None

    def open_folder(self, folder_name):
        """Set current directory and open it in the OS file manager."""
        original_name = (folder_name or "").strip()
        normalized_name = self.normalize_filename(original_name)
        folder_key = normalized_name.casefold()

        if folder_key in ("back", "go back", "previous folder"):
            return self.go_back()

        if folder_key in ("here", "this folder", "current folder"):
            folder = self.current_directory
        else:
            folder = self.special_folders.get(folder_key)

            if folder is None:
                # Support absolute/relative paths as well as common folders.
                candidate = Path(normalized_name).expanduser()
                if candidate.is_absolute():
                    folder = candidate
                else:
                    # Try current directory first, then Desktop/Downloads/Documents.
                    parents = [
                        self.current_directory,
                        self.home / "Desktop",
                        self.home / "Downloads",
                        self.home / "Documents",
                        self.home,
                    ]
                    folder = None
                    seen = set()
                    for parent in parents:
                        try:
                            resolved_parent = parent.resolve()
                        except OSError:
                            resolved_parent = parent
                        if resolved_parent in seen:
                            continue
                        seen.add(resolved_parent)

                        match = self._find_child_folder(parent, normalized_name)
                        if match is not None:
                            folder = match
                            break

                    # Fall back to a direct path relative to the current directory.
                    if folder is None:
                        folder = self.current_directory / normalized_name

        try:
            if not folder.exists() or not folder.is_dir():
                print(f"Folder not found: {folder}")
                return False

            self.current_directory = folder.resolve()

            if sys.platform == "darwin":
                subprocess.Popen(["open", str(self.current_directory)])
            elif sys.platform.startswith("win"):
                import os
                os.startfile(str(self.current_directory))
            else:
                subprocess.Popen(["xdg-open", str(self.current_directory)])

            print(f"Opened folder: {self.current_directory}")
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

        # Update directly so an absolute parent path is not treated as a name.
        self.current_directory = parent
        try:
            if sys.platform == "darwin":
                subprocess.Popen(["open", str(parent)])
            elif sys.platform.startswith("win"):
                import os
                os.startfile(str(parent))
            else:
                subprocess.Popen(["xdg-open", str(parent)])
            print(f"Went back. Current folder is {parent}.")
            return True
        except (OSError, subprocess.SubprocessError) as error:
            print(f"Could not open parent folder: {error}")
            return False

    def show_current_directory(self):
        print(f"Current directory: {self.current_directory}")
        return self.current_directory

    def find_file(self, filename):
        """Search common folders and subfolders for a file."""
        filename = self.normalize_filename(filename)
        filename_key = self._name_key(filename)

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

                exact_match = directory / filename
                if exact_match.is_file():
                    return exact_match

                for path in directory.rglob("*"):
                    if path.is_file():
                        actual_name = self.normalize_filename(path.name)
                        if (
                            actual_name == filename
                            or self._name_key(path.name) == filename_key
                        ):
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
