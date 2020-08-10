import urllib.parse
import shutil
import html
import json
import os

# Location of the video files (local)
ytpath = "/var/www/html/files/"
# Location of the video files (public)
ytpathweb = "/files/" # Could be something like https://example.com/files/ as well
# Where HTML files will be saved
outpath = "/var/www/html/"

# Load html templates into memory
templates = {}
for template in os.listdir('templates'):
    if template.endswith(".html"):
        with open(os.path.join('templates',template),"r") as f:
            templates[template[:-len(".html")]] = f.read()

# Copy assets
shutil.copy("templates/hobune.css",outpath)
shutil.copy("templates/hobune.js",outpath)
shutil.copy("templates/favicon.ico",outpath)

# Initialize channels list
channels = {
    "other": {
        "name": "Other videos",
        "date": -1,
        "videos": []
    }
}

# Allows you to disable .html extensions for links if you wish
# Doesn't affect actual filenames, just links
htmlext = ""#".html"

# Generate meta tags
def genMeta(meta):
    h = ""
    for m in meta:
        h += f'<meta name="{m}" content="{html.escape(meta[m])}">'
    return h

# Populate channels list
print("Populating channels list")
for root, subdirs, files in os.walk(ytpath):
    #sort videos by date
    files.sort(reverse = True)
    for file in (file for file in files if file.endswith(".info.json")):
        try:
            with open(os.path.join(root,file),"r") as f:
                v = json.load(f)
            if "/channels/" in root:
                channelid = v["uploader_id"]
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
                    v["custom_thumbnail"] = ytpathweb + x[len(ytpath):]
            channels[channelid]["videos"].append(v)
        except:
            print(f"Error processing {file}")

# Add channels to main navbar dropdown
dropdownhtml = ""
for channel in channels:
    if not channel == "other":
        dropdownhtml += f'<a class="item" href="/channels/{channel}{htmlext}">{html.escape(channels[channel]["name"])}</a>'
templates["base"] = templates["base"].replace("{channels}",dropdownhtml)

# Create video pages
for root, subdirs, files in os.walk(ytpath):
    print("Creating video pages for",root)
    for file in (file for file in files if file.endswith(".info.json")):
        try:
            with open(os.path.join(root,file),"r") as f:
                v = json.load(f)
            # Set mp4 path
            mp4path = f"{os.path.join(ytpathweb + root[len(ytpath):], file[:-len('.info.json')])}.mp4"
    
            # Get thumbnail path
            thumbnail = "/default.png"
            for ext in ["webp","jpg","png"]:
                if os.path.exists(x := os.path.join(root,file)[:-len('.info.json')] + f".{ext}"):
                    thumbnail = ytpathweb + x[len(ytpath):]
    
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
                            <a href="/dl{urllib.parse.quote(ytpathweb + altpath[len(ytpath):])}">
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
                    <a href="/dl{urllib.parse.quote(ytpathweb + descfile[len(ytpath):])}">
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
                            <a href="/dl{urllib.parse.quote(os.path.join(ytpathweb + root[len(ytpath):], vtt))}">
                                <div class="ui button">
                                    <i class="download icon"></i> Subtitles
                                </div>
                            </a>
                        </div>
                    """
    
            # Create HTML
            with open(os.path.join(outpath,f"videos/{v['id']}.html"),"w") as f:
                f.write(
                    templates["base"].format(title=html.escape(v['title']),meta=genMeta(
                        {
                            "description": v['description'][:256],
                            "author": v['uploader']
                        }
                    ),content=
                        templates["video"].format(
                            title=html.escape(v['title']),
                            description=html.escape(v['description']).replace('\n','<br>'),
                            views=v['view_count'],
                            uploader_url=('/channels/' + v['uploader_id'] + f'{htmlext}' if '/channels/' in root else f'/channels/other{htmlext}'),
                            uploader_id=v['uploader_id'],
                            uploader=html.escape(v['uploader']),
                            date=f"{v['upload_date'][:4]}-{v['upload_date'][4:6]}-{v['upload_date'][6:]}",
                            video=urllib.parse.quote(mp4path),
                            thumbnail=urllib.parse.quote(thumbnail),
                            download=downloadbtn
                        )
                    )
                )
        except:
            print(f"Error processing {file}")

# Create channel pages
print("Creating channel pages")
channelindex = ""
for channel in channels:
    channelindex += f"""
                    <div class="column searchable" data-name="{html.escape(channels[channel]['name'])}">
                        <a href="/channels/{channel}{htmlext}" class="ui card">
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
    with open(os.path.join(outpath,f"channels/{channel}.html"),"w") as f:
        cards = ""
        for v in channels[channel]["videos"]:
            cards += f"""
            <div class="column searchable" data-name="{html.escape(v['title'])}">
                <a href="/videos/{v['id']}{htmlext}" class="ui fluid card">
                  <div class="image">
                        <img loading="lazy" src="{urllib.parse.quote(v['custom_thumbnail'])}">
                  </div>
                  <div class="content">
                    <h3 class="header">{html.escape(v['title'])}</h3>
                    <p>{v['view_count']} views, {v['upload_date'][:4]}-{v['upload_date'][4:6]}-{v['upload_date'][6:]}</p>
                  </div>
                </a>
            </div>
            """
        f.write(templates["base"].format(title=html.escape(channels[channel]['name']),meta=genMeta(
            {
                "description": f"{channels[channel]['name']}'s channel archive"
            }
        ),content=templates["channel"].format(
                channel=html.escape(channels[channel]['name']),
                cards=cards
            )))
with open(os.path.join(outpath,f"channels/index.html"),"w") as f:
    f.write(templates["base"].format(title="Channels",meta=genMeta(
            {
                "description": "Archived channels"
            }
        ),content=templates["channel"].format(
                channel="Channels",
                cards=channelindex
            )))

# Write other pages
print("Writing other pages")
with open(os.path.join(outpath,f"contact.html"),"w") as f:
    f.write(templates["base"].format(title="Contact",meta="",content=templates["contact"]))
with open(os.path.join(outpath,f"index.html"),"w") as f:
    f.write(templates["base"].format(title="Home",meta=genMeta(
            {
                "description": "hobune - archive"
            }
        ),content=templates["index"]))

print("Done")
