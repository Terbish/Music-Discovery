import importlib.util
import json
import os
import platform
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


APP_NAME = "DailyDiscovery"
REPO_ROOT = Path(__file__).resolve().parents[1]
DEV_PERSONAL_DIR = REPO_ROOT / "personal"


@dataclass
class AppSettings:
    library_path: str = str(DEV_PERSONAL_DIR / "music_library_with_genres.csv")
    output_path: str = str(DEV_PERSONAL_DIR / "discovery")
    audio_output_path: str = str(DEV_PERSONAL_DIR / "audio_output")
    audio_format: str = "mp3"
    youtube_cookies_path: str = ""
    batch_size: int = 20
    launch_at_startup: bool = False
    minimize_to_tray: bool = False
    notifications_enabled: bool = True
    use_repo_personal_dir: bool = True


def user_config_dir() -> Path:
    system = platform.system()
    if system == "Windows":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        return base / APP_NAME
    if system == "Darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "daily-discovery"


def user_data_dir() -> Path:
    system = platform.system()
    if system == "Windows":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return base / APP_NAME
    if system == "Darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME / "Data"
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "daily-discovery"


def settings_path() -> Path:
    return user_config_dir() / "settings.json"


def load_settings() -> AppSettings:
    path = settings_path()
    if not path.exists():
        settings = AppSettings()
        save_settings(settings)
        return settings

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    defaults = asdict(AppSettings())
    defaults.update({key: value for key, value in data.items() if key in defaults})
    return AppSettings(**defaults)


def save_settings(settings: AppSettings | dict[str, Any]) -> AppSettings:
    if isinstance(settings, dict):
        defaults = asdict(AppSettings())
        defaults.update({key: value for key, value in settings.items() if key in defaults})
        settings = AppSettings(**defaults)

    path = settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(asdict(settings), f, indent=2)
    return settings


def resolve_data_dir(settings: AppSettings | None = None) -> Path:
    current = settings or load_settings()
    if current.use_repo_personal_dir or DEV_PERSONAL_DIR.exists():
        DEV_PERSONAL_DIR.mkdir(parents=True, exist_ok=True)
        return DEV_PERSONAL_DIR

    path = user_data_dir()
    path.mkdir(parents=True, exist_ok=True)
    return path


def resolve_binary(name: str) -> str | None:
    found = shutil.which(name)
    if found:
        return found

    for candidate in (Path("/opt/homebrew/bin") / name, Path("/usr/local/bin") / name):
        if candidate.exists():
            return str(candidate)
    return None


def environment_status() -> dict[str, Any]:
    return {
        "config_dir": str(user_config_dir()),
        "data_dir": str(resolve_data_dir()),
        "ffmpeg": resolve_binary("ffmpeg"),
        "yt_dlp": importlib.util.find_spec("yt_dlp") is not None,
    }
