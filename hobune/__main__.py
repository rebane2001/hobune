import urllib.parse
import shutil
import html
import json
import os
from comments import getCommentsHTML

from hobune.config import load_config

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

# Create folders
for folder in ["channels", "videos", "comments"]:
    os.makedirs(os.path.join(config.output_path, folder), exist_ok=True)

# Copy assets
shutil.copy("templates/hobune.css", config.output_path)
shutil.copy("templates/hobune.js", config.output_path)
shutil.copy("templates/favicon.ico", config.output_path)

# Initialize channels list
channels = {
    "other": {
        "name": "Other videos",
        "date": -1,
        "removed": 0,
        "unlisted": 0,
        "videos": []
    }
}

# Allows you to disable .html extensions for links if you wish
# Doesn't affect actual filenames, just links
# TODO: change back
htmlext = ".html"  # ""#".html"


# Generate meta tags
def genMeta(meta):
    h = ""
    for m in meta:
        h += f'<meta name="{m}" content="{html.escape(meta[m])}">'
    return h


# Get uploader id from video object
def getUploaderId(v):
    channelid = v.get("uploader_id", v.get("channel_id"))
    # Do not use @handles if possible
    if isinstance(channelid, str) and channelid[0] == "@":
        channelid = v.get("channel_id", channelid)
    return channelid


# Populate channels list
print("Populating channels list")
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
            if "/channels/" in root:
                channelid = getUploaderId(v)
                if not channelid:
                    raise KeyError("uploader_id nor channel_id found")
                if not channelid in channels:
                    channels[channelid] = {
                        "name": "",
                        "date": 0,
                        "removed": 0,
                        "unlisted": 0,
                        "videos": []
                    }
                if channels[channelid]["date"] < int(v["upload_date"]):
                    channels[channelid]["date"] = int(v["upload_date"])
                    channels[channelid]["name"] = v["uploader"]
            else:
                channelid = "other"
            v["custom_thumbnail"] = "/default.png"
            for ext in ["webp", "jpg", "png"]:
                if os.path.exists(x := os.path.join(root, file)[:-len('.info.json')] + f".{ext}"):
                    v["custom_thumbnail"] = config.files_web_path + x[len(config.files_path):]
            # Tag video if removed
            v["removed"] = (v["id"] in removed_videos)
            if v["removed"]:
                channels[channelid]["removed"] += 1
            # Tag video if unlisted
            v["unlisted"] = (v["id"] in unlisted_videos)
            if v["unlisted"]:
                channels[channelid]["unlisted"] += 1
            # Remove unnecessary keys to prevent memory exhaustion on big archives
            [v.pop(k) for k in list(v.keys()) if not k in
                                                     ["title", "id", "custom_thumbnail", "view_count", "upload_date",
                                                      "removed", "unlisted"]
             ]
            channels[channelid]["videos"].append(v)
        except Exception as e:
            print(f"Error processing {file}", e)

# Add channels to main navbar dropdown (but only if less than 25, otherwise the dropdown menu gets too long)
if len(channels) < 25:
    dropdownhtml = ""
    for channel in channels:
        if not channel == "other":
            dropdownhtml += f'<a class="item" href="{config.web_root}channels/{channel}{htmlext}">{html.escape(channels[channel]["name"])}</a>'
    channelshtml = f'''
            <div class="ui simple dropdown item">
            <a href="{config.web_root}channels">Channels</a> <i class="dropdown icon"></i>
            <div class="menu">
                <!-- <a class="item" href="/channels/other.html">Other videos</a> -->
                <a class="item" href="{config.web_root}channels/other">Other videos</a>
                <div class="divider"></div>
                {dropdownhtml}
            </div>
            </div>
    '''
else:
    channelshtml = f'''
        <a href="{config.web_root}" class="item">
          Channels
        </a>
    '''

custompageshtml = ""
# Creating links to custom pages
for custompage in os.listdir('custom'):
    custompage = os.path.splitext(custompage)[0]
    custompageshtml += f'<a href="{config.web_root}{custompage}{htmlext}" class="{"item right" if len(custompageshtml) == 0 else "item"}">{custompage}</a>'

templates["base"] = templates["base"].replace("{channels}", channelshtml).replace("{custompages}",
                                                                                  custompageshtml).replace(
    "{config.web_root}", config.web_root).replace("{config.site_name}", config.site_name)

# Create video pages
for root, subdirs, files in os.walk(config.files_path):
    print("Creating video pages for", root)
    for file in (file for file in files if file.endswith(".info.json")):
        try:
            with open(os.path.join(root, file), "r") as f:
                v = json.load(f)
            # Skip channel/playlist info.json files
            if v.get("_type") == "playlist" or (len(v["id"]) == 24 and v.get("extractor") == "youtube:tab"):
                continue
            # Generate comments
            comments_html, comments_count = getCommentsHTML(html.escape(v['title']), v['id'])
            comments_link = ""
            if comments_html:
                with open(os.path.join(config.output_path, f"comments/{v['id']}.html"), "w") as f:
                    f.write(templates["base"].format(title=html.escape(v['title'] + ' - Comments'), meta=genMeta(
                        {
                            "description": v['description'][:256],
                            "author": v['uploader']
                        }
                    ), content=comments_html))
                comments_link = f'<h3 class="ui small header" style="margin: 0;"><a href="/comments/{v["id"]}">View comments ({comments_count})</a></h3>'
            # Set mp4 path
            mp4path = f"{os.path.join(config.files_web_path + root[len(config.files_path):], file[:-len('.info.json')])}.mp4"
            for ext in ["mp4", "webm", "mkv"]:
                if os.path.exists(altpath := os.path.join(root, file)[:-len('.info.json')] + f".{ext}"):
                    mp4path = f"{os.path.join(config.files_web_path + root[len(config.files_path):], file[:-len('.info.json')])}.{ext}"
                    break

            # Get thumbnail path
            thumbnail = "/default.png"
            for ext in ["webp", "jpg", "png"]:
                if os.path.exists(x := os.path.join(root, file)[:-len('.info.json')] + f".{ext}"):
                    thumbnail = config.files_web_path + x[len(config.files_path):]

            # Create a download button for the video
            downloadbtn = f"""
                <a href="/dl{urllib.parse.quote(mp4path)}">
                    <div class="ui button downloadbtn">
                        <i class="download icon"></i> Download video
                    </div>
                </a>
            """

            # Create multiple video download buttons if we have multiple formats
            for ext in ["webm", "mkv"]:
                if os.path.exists(altpath := os.path.join(root, file)[:-len('.info.json')] + f".{ext}"):
                    downloadbtn = f"""
                        <div class="ui left labeled button downloadbtn">
                            <a class="ui basic right pointing label">
                                1080/mp4
                            </a>
                            <a href="/dl{urllib.parse.quote(mp4path)}">
                                <div class="ui button">
                                    <i class="download icon"></i> Download video
                                </div>
                            </a>
                        </div>
                        <div class="ui left labeled button downloadbtn">
                            <a class="ui basic right pointing label">
                                4K/{ext}
                            </a>
                            <a href="/dl{urllib.parse.quote(config.files_web_path + altpath[len(config.files_path):])}">
                                <div class="ui button">
                                    <i class="download icon"></i> Download video
                                </div>
                            </a>
                        </div>
                    """

            # Description download
            if os.path.exists(descfile := os.path.join(root, file)[:-len('.info.json')] + f".description"):
                downloadbtn += f"""
                    <br>
                    <a href="/dl{urllib.parse.quote(config.files_web_path + descfile[len(config.files_path):])}">
                        <div class="ui button downloadbtn">
                            <i class="download icon"></i> Description
                        </div>
                    </a>
                """

            # Thumbnail download
            if not thumbnail == "/default.png":
                downloadbtn += f"""
                    <br>
                    <a href="/dl{urllib.parse.quote(thumbnail)}">
                        <div class="ui button downloadbtn">
                            <i class="download icon"></i> Thumbnail
                        </div>
                    </a>
                """

            # Subtitles download
            for vtt in (vtt for vtt in files if vtt.endswith(".vtt")):
                if vtt.startswith(file[:-len('.info.json')]):
                    downloadbtn += f"""
                        <br>
                        <div class="ui left labeled button downloadbtn">
                            <a class="ui basic right pointing label">
                                {vtt[len(file[:-len('.info.json')]) + 1:-len('.vtt')]}
                            </a>
                            <a href="/dl{urllib.parse.quote(os.path.join(config.files_web_path + root[len(config.files_path):], vtt))}">
                                <div class="ui button">
                                    <i class="download icon"></i> Subtitles
                                </div>
                            </a>
                        </div>
                    """

            # Create HTML
            with open(os.path.join(config.output_path, f"videos/{v['id']}.html"), "w") as f:
                f.write(
                    templates["base"].format(title=html.escape(v['title']), meta=genMeta(
                        {
                            "description": v['description'][:256],
                            "author": v['uploader']
                        }
                    ), content=
                                             templates["video"].format(
                                                 title=html.escape(v['title']),
                                                 description=html.escape(v['description']).replace('\n', '<br>'),
                                                 views=v['view_count'],
                                                 uploader_url=(f'{config.web_root}channels/' + getUploaderId(
                                                     v) + f'{htmlext}' if '/channels/' in root else f'{config.web_root}channels/other{htmlext}'),
                                                 uploader_id=getUploaderId(v),
                                                 uploader=html.escape(v['uploader']),
                                                 date=f"{v['upload_date'][:4]}-{v['upload_date'][4:6]}-{v['upload_date'][6:]}",
                                                 video=urllib.parse.quote(mp4path),
                                                 thumbnail=urllib.parse.quote(thumbnail),
                                                 download=downloadbtn,
                                                 comments=comments_link
                                             )
                                             )
                )
        except Exception as e:
            print(f"Error processing {file}", e)


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
                    <div class="column searchable" data-name="{html.escape(channels[channel]['name'])}">
                        <a href="{config.web_root}channels/{channel}{htmlext}" class="ui card">
                            <div class="content">
                                <div class="header">{html.escape(channels[channel]['name'])}</div>
                                <div class="meta">{channel}</div>
                                <div class="description">
                                    {len(channels[channel]['videos'])} videos{' (' + str(channels[channel]['removed']) + ' removed)' if channels[channel]['removed'] > 0 else ''}{' (' + str(channels[channel]['unlisted']) + ' unlisted)' if channels[channel]['unlisted'] > 0 else ''}
                                </div>
                            </div>
                        </a>
                    </div>
                """
    with open(os.path.join(config.output_path, f"channels/{channel}.html"), "w") as f:
        cards = ""
        for v in channels[channel]["videos"]:
            cards += f"""
            <div class="column searchable" data-name="{html.escape(v['title'])}">
                <a href="{config.web_root}videos/{v['id']}{htmlext}" class="ui fluid card">
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
        f.write(templates["base"].format(title=html.escape(channels[channel]['name']), meta=genMeta(
            {
                "description": f"{channels[channel]['name']}'s channel archive"
            }
        ), content=templates["channel"].format(
            channel=html.escape(channels[channel]['name']),
            note=get_channel_note(channel),
            cards=cards
        )))
with open(os.path.join(config.output_path, f"channels/index.html"), "w") as f:
    f.write(templates["base"].format(title="Channels", meta=genMeta(
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
    f.write(templates["base"].format(title="Home", meta=genMeta(
        {
            "description": f"{config.site_name} - archive"
        }
    ), content=templates["index"].replace("{config.site_name}", config.site_name)))

print("Done")
