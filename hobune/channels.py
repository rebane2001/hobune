import json
import os
from dataclasses import dataclass, field
from typing import Optional

from hobune.logger import logger


@dataclass
class HobuneChannel:
    name: str
    date: Optional[int] = 0
    removed_count: Optional[int] = 0
    unlisted_count: Optional[int] = 0
    videos: list = field(default_factory=list)
    names: set = field(default_factory=set)
    handles: set = field(default_factory=set)
    username: Optional[str] = None


# If this returns false, the videos go in the "other" channel (e.g. `return "/channels/" in root`)
def is_full_channel(root):
    return True


def process_channel(channels, v, full):
    if full:
        channel_id = v.get("channel_id", "NA")
        channel_name = v["uploader"]
        uploader_id = v.get("uploader_id")
        channel_username = uploader_id if uploader_id[0] != "@" else None
        channel_handle = uploader_id if uploader_id[0] == "@" else None
        if not channel_id:
            raise KeyError("channel_id not found")
        if channel_id not in channels:
            channels[channel_id] = HobuneChannel(channel_name)
            logger.debug(f"Added new channel {channel_name}")
        if channels[channel_id].date < int(v["upload_date"]):
            channels[channel_id].date = int(v["upload_date"])
            channels[channel_id].name = channel_name
        channels[channel_id].names.add(channel_name)
        if channel_handle:
            channels[channel_id].handles.add(channel_handle)
        if channel_username:
            channels[channel_id].username = channel_username
    else:
        channel_id = "other"
    return channel_id


def initialize_channels(config, removed_videos, unlisted_videos):
    channels = {
        "other": HobuneChannel("Other videos")
    }
    for root, subdirs, files in os.walk(config.files_path):
        # sort videos by date
        files.sort(reverse=True)
        for file in (file for file in files if file.endswith(".info.json")):
            try:
                with open(os.path.join(root, file), "r") as f:
                    v = json.load(f)
                # Skip channel/playlist info.json files
                if v.get("_type") == "playlist" or (len(v["id"]) == 24 and v.get("extractor") == "youtube:tab"):
                    continue
                channel_id = process_channel(channels, v, is_full_channel(root))
                v["custom_thumbnail"] = "/default.png"
                for ext in ["webp", "jpg", "png"]:
                    if os.path.exists(x := os.path.join(root, file)[:-len('.info.json')] + f".{ext}"):
                        v["custom_thumbnail"] = config.files_web_path + x[len(config.files_path):]
                # Tag video if removed
                v["removed"] = (v["id"] in removed_videos)
                if v["removed"]:
                    channels[channel_id].removed_count += 1
                # Tag video if unlisted
                v["unlisted"] = (v["id"] in unlisted_videos)
                if v["unlisted"]:
                    channels[channel_id].unlisted_count += 1
                # Remove unnecessary keys to prevent memory exhaustion on big archives
                [v.pop(k) for k in list(v.keys()) if not k in
                                                         ["title", "id", "custom_thumbnail", "view_count", "upload_date",
                                                          "removed", "unlisted"]
                 ]
                channels[channel_id].videos.append(v)
            except Exception as e:
                print(f"Error processing {file}", e)
    return channels
