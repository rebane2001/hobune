import urllib.parse
import shutil
import html
import json
import os
from dataclasses import dataclass, field
from typing import Optional

from comments import getCommentsHTML
from hobune.assets import init_assets, update_templates
from hobune.channels import is_full_channel, initialize_channels
from hobune.logger import logger
from hobune.config import load_config
from hobune.util import generate_meta_tags, quote_url
from hobune.videos import create_video_pages

# TODO: Remove
os.chdir("..")

config = load_config()
if not config:
    exit()


def extract_ids_from_txt(filename):
    ids = set()
    if len(filename):
        with open(filename, "r") as f:
            for l in f:
                if len(l.strip()) >= 11:
                    ids.add(l.strip()[-11:])
    return ids


# Generate removed and unlisted videos sets
removed_videos = extract_ids_from_txt(config.removed_videos_file)
unlisted_videos = extract_ids_from_txt(config.unlisted_videos_file)

templates = init_assets(config.output_path)

# Extension appended to links
html_ext = ".html" if config.add_html_ext else ""

logger.info("Populating channels list")
channels = initialize_channels(config, removed_videos, unlisted_videos)

update_templates(config, templates, channels, html_ext)

logger.info("Creating video pages")
create_video_pages(config, channels, templates)


def get_channel_note(channel):
    note_path = f"note/{channel}".replace(".", "_")
    if not os.path.isfile(note_path):
        return ""
    with open(note_path, "r") as f:
        return f.read()


# Create channel pages
print("Creating channel pages")
channelindex = ""
for channel in channels:
    channelindex += f"""
                    <div class="column searchable" data-name="{html.escape(channels[channel].name)}">
                        <a href="{config.web_root}channels/{channel}{html_ext}" class="ui card">
                            <div class="content">
                                <div class="header">{html.escape(channels[channel].name)}</div>
                                <div class="meta">{channel}</div>
                                <div class="description">
                                    {len(channels[channel].videos)} videos{' (' + str(channels[channel].removed_count) + ' removed)' if channels[channel].removed_count > 0 else ''}{' (' + str(channels[channel].unlisted_count) + ' unlisted)' if channels[channel].unlisted_count > 0 else ''}
                                </div>
                            </div>
                        </a>
                    </div>
                """
    with open(os.path.join(config.output_path, f"channels/{channel}.html"), "w") as f:
        cards = ""
        for v in channels[channel].videos:
            cards += f"""
            <div class="column searchable" data-name="{html.escape(v['title'])}">
                <a href="{config.web_root}videos/{v['id']}{html_ext}" class="ui fluid card">
                  <div class="image thumbnail">
                        <img loading="lazy" src="{quote_url(v['custom_thumbnail'])}">
                  </div>
                  <div class="content{' removedvideo' if v["removed"] else ''}{' unlistedvideo' if v["unlisted"] else ''}">
                    <h3 class="header">{html.escape(v['title'])}</h3>
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
            note=get_channel_note(channel),
            cards=cards
        )))
with open(os.path.join(config.output_path, f"channels/index.html"), "w") as f:
    f.write(templates["base"].format(title="Channels", meta=generate_meta_tags(
        {
            "description": "Archived channels"
        }
    ), content=templates["channel"].format(
        channel="Channels",
        note="",
        cards=channelindex
    )))

print("Done")
