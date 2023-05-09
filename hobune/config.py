from dataclasses import dataclass
import json
import os
import shutil

CONFIG_PATH = "config.json"
DEFAULT_PATH = "default.json"


@dataclass
class HobuneConfig:
    # Name/Title of the site (e.g. "Hobune")
    site_name: str
    # Local path of the video files (e.g. "/var/www/html/files/")
    files_path: str
    # Web path of the video files (e.g. "/files/" or "https://example.com/files/")
    files_web_path: str
    # Web root path (e.g. "/" or "https://example.com/")
    web_root: str
    # Output path for the HTML files (e.g. "/var/www/html/")
    output_path: str
    # A text file where each line ends with a removed video ID (optional, e.g. "~/removed_videos.txt")
    removed_videos_file: str
    # Unlisted videos file - similar to the removed videos file (optional)
    unlisted_videos_file: str


# Add a slash to a path if it's missing
def fix_path(path: str) -> str:
    if path[-1] != "/":
        path += "/"
    return path


def fix_paths(hobune_config: HobuneConfig):
    hobune_config.files_path = fix_path(hobune_config.files_path)
    hobune_config.files_web_path = fix_path(hobune_config.files_web_path)
    hobune_config.web_root = fix_path(hobune_config.web_root)
    hobune_config.output_path = fix_path(hobune_config.output_path)
    return hobune_config


def load_config() -> None | HobuneConfig:
    # If config doesn't exist, create one
    if not os.path.exists(CONFIG_PATH):
        shutil.copy(DEFAULT_PATH, CONFIG_PATH)
        print(f"Created {CONFIG_PATH}, please set it up and re-run Hobune")
        return None
    else:
        with open(CONFIG_PATH, "r") as f:
            configfile = json.load(f)
            hobune_config = HobuneConfig(
                configfile["site_name"],
                configfile["files_path"],
                configfile["files_web_path"],
                configfile["web_root"],
                configfile["output_path"],
                configfile.get("removed_videos_file", ""),
                configfile.get("unlisted_videos_file", ""),
            )
        hobune_config = fix_paths(hobune_config)
        return hobune_config
