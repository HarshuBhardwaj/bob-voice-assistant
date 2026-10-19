
import subprocess
from urllib.parse import quote_plus


class PCControl:
    def open_app(self, app_name):
        try:
            subprocess.Popen(["open", "-a", app_name])
            return True

        except OSError as error:
            print(f"Could not open {app_name}: {error}")
            return False

    def open_website(self, url):
        try:
            subprocess.Popen([
                "open",
                "-a",
                "Google Chrome",
                url
            ])
            return True

        except OSError as error:
            print(f"Could not open website {url}: {error}")
            return False

    def search_youtube(self, query):
        try:
            search_query = quote_plus(query)

            url = (
                "https://www.youtube.com/results?search_query="
                + search_query
            )

            subprocess.Popen([
                "open",
                "-a",
                "Google Chrome",
                url
            ])

            return True

        except OSError as error:
            print(f"YouTube search failed: {error}")
            return False

    def search_google(self, query):
        try:
            search_query = quote_plus(query)

            url = (
                "https://www.google.com/search?q="
                + search_query
            )

            subprocess.Popen([
                "open",
                "-a",
                "Google Chrome",
                url
            ])

            return True

        except OSError as error:
            print(f"Google search failed: {error}")
            return False