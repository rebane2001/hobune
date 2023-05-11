import html
import json
import os
import shutil
from dataclasses import dataclass, field
from typing import Optional

from hobune.logger import logger
from hobune.util import quote_url, generate_meta_tags, extract_ids_from_txt, no_traverse


@dataclass
class HobuneChannel:
    id: str
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
        channel_id = v.get("channel_id", v.get("uploader_id", "NA"))
        channel_name = v["uploader"]
        uploader_id = v.get("uploader_id")
        channel_username = uploader_id if uploader_id[0] != "@" and uploader_id != channel_id else None
        channel_handle = uploader_id if uploader_id[0] == "@" else None
        if not channel_id:
            raise KeyError("channel_id not found")
        if channel_id not in channels:
            channels[channel_id] = HobuneChannel(channel_id, channel_name)
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


def initialize_channels(config):
    # Generate removed and unlisted videos sets
    removed_videos = extract_ids_from_txt(config.removed_videos_file)
    unlisted_videos = extract_ids_from_txt(config.unlisted_videos_file)

    channels = {
        "other": HobuneChannel("other", "Other videos")
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
                # Remember path of .info.json
                v["root"] = root
                v["file"] = file
                # Remove unnecessary keys to prevent memory exhaustion on big archives
                [v.pop(k) for k in list(v.keys()) if not k in
                                                         ["title", "id", "custom_thumbnail", "view_count", "upload_date",
                                                          "removed", "unlisted", "root", "file"]
                 ]
                channels[channel_id].videos.append(v)
            except Exception as e:
                print(f"Error processing {file}", e)
    # Fix username-only entries with no channel ID
    username_map = {}
    for _, channel in channels.items():
        if channel.username and channel.username != channel.id:
            username_map[channel.username] = channel.id
    for username, channel_id in username_map.items():
        channel = channels.pop(username, None)
        if channel:
            channels[channel_id].removed_count += channel.removed_count
            channels[channel_id].unlisted_count += channel.unlisted_count
            channels[channel_id].videos += channel.videos
            channels[channel_id].names += channel.names

    return channels


def get_channel_note(channel):
    note_path = f"note/{channel}".replace(".", "_")
    if not os.path.isfile(note_path):
        return ""
    with open(note_path, "r") as f:
        return f.read()


def get_channel_search_string(channel: HobuneChannel):
    all_names = list(channel.names) + list(channel.handles) + ([channel.username] if channel.username else [])
    search_string = "; ".join(all_names)
    return search_string


def get_channel_aka(channel: HobuneChannel):
    if channel.id == "other":
        return ""
    escaped_id = html.escape(channel.id)
    aka_string = f'<a href="https://www.youtube.com/channel/{escaped_id}">{escaped_id}</a>'
    if channel.username:
        escaped_username = html.escape(channel.username)
        aka_string += f', <a href="https://www.youtube.com/user/{escaped_username}">/user/{escaped_username}</a>'
    names = [name for name in list(channel.names) if name != channel.name]
    names_str = html.escape(", ".join(list(channel.handles) + names))
    if names_str:
        aka_string += "; " + names_str
    return aka_string


def create_channel_pages(config, templates, channels, html_ext):
    channelindex = ""
    for channel in channels:
        logger.debug(f"Creating channel pages for {channels[channel].name}")
        videos_count_str = f"{len(channels[channel].videos)} videos{' (' + str(channels[channel].removed_count) + ' removed)' if channels[channel].removed_count > 0 else ''}{' (' + str(channels[channel].unlisted_count) + ' unlisted)' if channels[channel].unlisted_count > 0 else ''}"
        channelindex += f"""
                        <div class="card searchable" data-search="{html.escape(get_channel_search_string(channels[channel]))}">
                            <a href="{config.web_root}channels/{channel}{html_ext}" class="inner">
                                <div class="content">
                                    <div class="title">{html.escape(channels[channel].name)}</div>
                                    <div class="meta">{channels[channel].username or channel}</div>
                                    <div class="description">
                                        {videos_count_str}
                                    </div>
                                </div>
                            </a>
                        </div>
                    """
        with open(channel_html_path := os.path.join(config.output_path, f"channels/{no_traverse(channel)}.html"), "w") as f:
            cards = ""
            subtitle = f"<p class=\"subtitle\">{get_channel_aka(channels[channel])}<br>{videos_count_str}</p>"
            for v in sorted(channels[channel].videos, key=lambda x: x['upload_date'], reverse=True):
                cards += f"""
                <div class="card searchable" data-search="{html.escape(v['title'])}" data-date="{v['upload_date']}" data-views="{v['view_count']}">
                    <a href="{config.web_root}videos/{v['id']}{html_ext}" class="inner">
                      <div class="image thumbnail">
                            <img loading="lazy" src="{quote_url(v['custom_thumbnail'])}">
                      </div>
                      <div class="content{' removed' if v["removed"] else ''}{' unlisted' if v["unlisted"] else ''}">
                        <h3 class="title">{html.escape(v['title'])}</h3>
                        <p>{v['view_count']} views, {v['upload_date'][:4]}-{v['upload_date'][4:6]}-{v['upload_date'][6:]}</p>
                      </div>
                    </a>
                </div>
                """
            f.write(templates["base"].format(title=html.escape(channels[channel].name), meta=generate_meta_tags(
                {
                    "description": f"{channels[channel].name}'s channel archive"
                }
            ), content=templates["channel"].format(
                channel=html.escape(channels[channel].name),
                subtitle=subtitle,
                note=get_channel_note(channel),
                sort="",
                cards=cards
            )))
        if channels[channel].username:
            shutil.copy(channel_html_path, os.path.join(config.output_path, f"channels/{no_traverse(channels[channel].username)}.html"))
    with open(os.path.join(config.output_path, "channels/index.html"), "w") as f:
        f.write(templates["base"].format(title="Channels", meta=generate_meta_tags(
            {
                "description": "Archived channels"
            }
        ), content=templates["channel"].format(
            channel="Channels",
            note="",
            subtitle="",
            sort=" hide",
            cards=channelindex
        )))