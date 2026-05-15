from pathlib import Path

import webview

from music_discovery_app.desktop_api import DesktopApi


APP_TITLE = "Daily Discovery"


def main() -> None:
    frontend_path = Path(__file__).parent / "desktop_frontend" / "index.html"
    webview.create_window(
        APP_TITLE,
        frontend_path.resolve().as_uri(),
        js_api=DesktopApi(),
        width=1280,
        height=760,
        min_size=(1280, 720),
    )
    webview.start(debug=True)


if __name__ == "__main__":
    main()
