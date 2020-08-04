import urllib.parse
import shutil
import html
import json
import os

ytpath = "files/"
webpath = "/var/www/html/"

# Load html templates into memory
templates = {}
for template in os.listdir('templates'):
    with open(os.path.join('templates',template),"r") as f:
        templates[template[:-len(".html")]] = f.read()

# Copy CSS
shutil.copy("templates/hobune.css",webpath)

# Initialize channels list
channels = {
    "other": {
        "name": "Other videos",
        "date": -1,
        "videos": []
    }
}

# Populate channels list
print("Populating channels list")
for root, subdirs, files in os.walk(webpath + ytpath):
    for file in (file for file in files if file.endswith(".info.json")):
        with open(os.path.join(root,file),"r") as f:
            v = json.load(f)
        if "/channels/" in root:
            channelid = v["channel_id"]
            if not channelid in channels:
                channels[channelid] = {
                    "name": "",
                    "date": 0,
                    "videos": []
                }
            if channels[channelid]["date"] < int(v["upload_date"]):
                channels[channelid]["date"] = int(v["upload_date"])
                channels[channelid]["name"] = v["uploader"]
        else:
            channelid = "other"
        v["custom_thumbnail"] = "/default.png"
        for ext in ["webp","jpg","png"]:
            if os.path.exists(x := os.path.join(root,file)[:-len('.info.json')] + f".{ext}"):
                v["custom_thumbnail"] = x[len(webpath)-1:]
        channels[channelid]["videos"].append(v)

# Add channels to main navbar dropdown
dropdownhtml = ""
for channel in channels:
    if not channel == "other":
        dropdownhtml += f'<a class="item" href="/channels/{channel}.html">{html.escape(channels[channel]["name"])}</a>'
templates["base"] = templates["base"].replace("{channels}",dropdownhtml)

# Create video pages
for root, subdirs, files in os.walk(webpath + ytpath):
    print("Creating video pages for",root)
    for file in (file for file in files if file.endswith(".info.json")):
        with open(os.path.join(root,file),"r") as f:
            v = json.load(f)
        # Set mp4 path
        mp4path = f"{os.path.join(root[len(webpath)-1:], file[:-len('.info.json')])}.mp4"

        # Get thumbnail path
        thumbnail = "/default.png"
        for ext in ["webp","jpg","png"]:
            if os.path.exists(x := os.path.join(root,file)[:-len('.info.json')] + f".{ext}"):
                thumbnail = x[len(webpath)-1:]

        # Create a download button for the video
        downloadbtn = f"""
            <a href="/dl{urllib.parse.quote(mp4path)}">
                <div class="ui button downloadbtn">
                    <i class="download icon"></i> Download video
                </div>
            </a>
        """

        # Create multiple video download buttons if we have multiple formats
        for ext in ["webm","mkv"]:
            if os.path.exists(altpath := os.path.join(root,file)[:-len('.info.json')] + f".{ext}"):
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
                        <a href="/dl{urllib.parse.quote(altpath[len(webpath)-1:])}">
                            <div class="ui button">
                                <i class="download icon"></i> Download video
                            </div>
                        </a>
                    </div>
                """

        # Description download
        if os.path.exists(descfile := os.path.join(root,file)[:-len('.info.json')] + f".description"):
            downloadbtn += f"""
                <br>
                <a href="/dl{urllib.parse.quote(descfile[len(webpath)-1:])}">
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
                            {vtt[len(file[:-len('.info.json')])+1:-len('.vtt')]}
                        </a>
                        <a href="/dl{urllib.parse.quote(os.path.join(root[len(webpath)-1:], vtt))}">
                            <div class="ui button">
                                <i class="download icon"></i> Subtitles
                            </div>
                        </a>
                    </div>
                """

        # Create HTML
        with open(os.path.join(webpath,f"videos/{v['id']}.html"),"w") as f:
            f.write(
                templates["base"].format(title=html.escape(v['title']),content=
                    templates["video"].format(
                        title=html.escape(v['title']),
                        description=html.escape(v['description']).replace('\n','<br>'),
                        views=v['view_count'],
                        uploader_url=('/channels/' + v['channel_id'] + '.html' if '/channels/' in root else '/channels/other.html'),
                        uploader=html.escape(v['uploader']),
                        video=urllib.parse.quote(mp4path),
                        thumbnail=urllib.parse.quote(thumbnail),
                        download=downloadbtn
                    )
                )
            )

# Create channel pages
print("Creating channel pages")
channelindex = ""
for channel in channels:
    channelindex += f"""
                    <div class="column">
                        <a href="/channels/{channel}.html" class="ui card">
                            <div class="content">
                                <div class="header">{html.escape(channels[channel]['name'])}</div>
                                <div class="meta">{channel}</div>
                                <div class="description">
                                    {len(channels[channel]['videos'])} videos
                                </div>
                            </div>
                        </a>
                    </div>
                """
    with open(os.path.join(webpath,f"channels/{channel}.html"),"w") as f:
        cards = ""
        for v in channels[channel]["videos"]:
            cards += f"""
            <div class="column">
                <a href="/videos/{v['id']}.html" class="ui fluid card">
                  <div class="image">
                        <img src="{urllib.parse.quote(v['custom_thumbnail'])}">
                  </div>
                  <div class="content">
                    <h3 class="header">{html.escape(v['title'])}</h3>
                    <p>{v['view_count']} views</p>
                  </div>
                </a>
            </div>
            """
        f.write(templates["base"].format(title=html.escape(channels[channel]['name']),content=templates["channel"].format(
                channel=html.escape(channels[channel]['name']),
                cards=cards
            )))
with open(os.path.join(webpath,f"channels/index.html"),"w") as f:
    f.write(templates["base"].format(title=html.escape(channels[channel]['name']),content=templates["channel"].format(
                channel="Channels",
                cards=channelindex
            )))

# Write other pages
print("Writing other pages")
with open(os.path.join(webpath,f"contact.html"),"w") as f:
    f.write(templates["base"].format(title="Contact",content=templates["contact"]))
with open(os.path.join(webpath,f"index.html"),"w") as f:
    f.write(templates["base"].format(title="Home",content=templates["index"]))

print("Done")
