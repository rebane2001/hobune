import urllib.parse
import shutil
import html
import json
import os
from dataclasses import dataclass, field
from typing import Optional

from comments import getCommentsHTML
from hobune.channels import is_full_channel, initialize_channels
from hobune.logger import logger
from hobune.config import load_config
from hobune.util import generate_meta_tags
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

# Load html templates into memory
templates = {}
for template in os.listdir('templates'):
    if template.endswith(".html"):
        with open(os.path.join('templates', template), "r") as f:
            templates[template[:-len(".html")]] = f.read()


def init_assets(output_path):
    # Create folders
    for folder in ["channels", "videos", "comments"]:
        os.makedirs(os.path.join(output_path, folder), exist_ok=True)

    # Copy assets
    shutil.copy("templates/hobune.css", output_path)
    shutil.copy("templates/hobune.js", output_path)
    shutil.copy("templates/favicon.ico", output_path)


init_assets(config.output_path)

# Extension appended to links
html_ext = ".html" if config.add_html_ext else ""





# Get uploader id from video object
def getUploaderId(v):
    channelid = v.get("uploader_id", v.get("channel_id"))
    # Do not use @handles if possible
    if isinstance(channelid, str) and channelid[0] == "@":
        channelid = v.get("channel_id", channelid)
    return channelid


logger.info("Populating channels list")
channels = initialize_channels(config, removed_videos, unlisted_videos)

# Add channels to main navbar dropdown (but only if less than 25, otherwise the dropdown menu gets too long)
if len(channels) < 25:
    dropdown_html = ""
    for channel in channels:
        if channel != "other":
            dropdown_html += f'<a class="item" href="{config.web_root}channels/{channel}{html_ext}">{html.escape(channels[channel].name)}</a> '
    channels_html = f'''
            <div class="ui simple dropdown item">
            <a href="{config.web_root}channels">Channels</a> <i class="dropdown icon"></i>
            <div class="menu">
                <a class="item" href="{config.web_root}channels/other{html_ext}">Other videos</a>
                <div class="divider"></div>
                {dropdown_html}
            </div>
            </div>
    '''
else:
    channels_html = f'''
        <a href="{config.web_root}" class="item">
          Channels
        </a>
    '''

custompageshtml = ""
# Creating links to custom pages
for custompage in os.listdir('custom'):
    custompage = os.path.splitext(custompage)[0]
    custompageshtml += f'<a href="{config.web_root}{custompage}{html_ext}" class="{"item right" if len(custompageshtml) == 0 else "item"}">{custompage}</a>'

templates["base"] = templates["base"].replace("{channels}", channels_html).replace("{custompages}",
                                                                                   custompageshtml).replace(
    "{config.web_root}", config.web_root).replace("{config.site_name}", config.site_name)


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
                        <img loading="lazy" src="{urllib.parse.quote(v['custom_thumbnail'])}">
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

# Write other pages
print("Writing other pages")
for custompage in os.listdir('custom'):
    with open(f"custom/{custompage}", "r") as custompagef:
        custompage = os.path.splitext(custompage)[0]
        with open(os.path.join(config.output_path, f"{custompage}.html"), "w") as f:
            f.write(templates["base"].format(title=custompage, meta="", content=custompagef.read()))
with open(os.path.join(config.output_path, f"index.html"), "w") as f:
    f.write(templates["base"].format(title="Home", meta=generate_meta_tags(
        {
            "description": f"{config.site_name} - archive"
        }
    ), content=templates["index"].replace("{config.site_name}", config.site_name)))

print("Done")
