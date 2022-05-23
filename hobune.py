import urllib.parse
import shutil
import html
import json
import os

# If config doesn't exist, create one
if not os.path.exists("config.json"):
    shutil.copy("default.json", "config.json")
    print("Created config.json, please set it up and re-run Hobune")
    exit()
else:
    with open("config.json","r") as f:
        configfile = json.load(f)
        # Name/Title of the site (eg will be shown on homepages)
        sitename = configfile["sitename"] # "Hobune"
        # Location of the video files (local)
        ytpath = configfile["ytpath"] # "/var/www/html/files/"
        # Location of the video files (public), could be something like https://example.com/files/ as well
        ytpathweb = configfile["ytpathweb"] # "/files/"
        # Location of the website root (public), could be something like https://example.com/hobune/ as well
        webpath = configfile["webpath"] # "/"
        # Where HTML files will be saved
        outpath = configfile["outpath"] # "/var/www/html/"
        # Removed videos file - each line ends with the video ID of a removed video to "tag" it (optional)
        removedvideosfile = configfile["removedvideosfile"] # ""


# Add slashes to paths if they are missing
if not ytpath[-1] == "/":
    ytpath += "/"
if not ytpathweb[-1] == "/":
    ytpathweb += "/"
if not webpath[-1] == "/":
    webpath += "/"
if not outpath[-1] == "/":
    outpath += "/"

# Generate removed videos list
removedvideos = []
if not removedvideosfile == "":
    with open(removedvideosfile, "r") as f:
        for l in f:
            if len(l) > 11:
                removedvideos.append(l[-12:-1])

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
        "removed": 0,
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
            # Skip channel/playlist info.json files
            if v.get("_type") == "playlist" or (len(v["id"]) == 24 and v.get("extractor") == "youtube:tab"):
                continue
            if "/channels/" in root:
                channelid = v.get("uploader_id",v.get("channel_id"))
                if not channelid:
                    raise KeyError("uploader_id nor channel_id found")
                if not channelid in channels:
                    channels[channelid] = {
                        "name": "",
                        "date": 0,
                        "removed": 0,
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
            # Tag video if removed
            v["removed"] = (v["id"] in removedvideos)
            if v["removed"]:
                channels[channelid]["removed"] += 1
            # Remove unnecessary keys to prevent memory exhaustion on big archives
            [v.pop(k) for k in list(v.keys()) if not k in 
                ["title","id","custom_thumbnail","view_count","upload_date","removed"]
            ]
            channels[channelid]["videos"].append(v)
        except Exception as e:
            print(f"Error processing {file}", e)

# Add channels to main navbar dropdown (but only if less than 25, otherwise the dropdown menu gets too long)
if len(channels) < 25:
    dropdownhtml = ""
    for channel in channels:
        if not channel == "other":
            dropdownhtml += f'<a class="item" href="{webpath}channels/{channel}{htmlext}">{html.escape(channels[channel]["name"])}</a>'
    channelshtml = f'''
            <div class="ui simple dropdown item">
            <a href="{webpath}channels">Channels</a> <i class="dropdown icon"></i>
            <div class="menu">
                <!-- <a class="item" href="/channels/other.html">Other videos</a> -->
                <a class="item" href="{webpath}channels/other">Other videos</a>
                <div class="divider"></div>
                {dropdownhtml}
            </div>
            </div>
    '''
else:
    channelshtml = f'''
        <a href="{webpath}" class="item">
          Channels
        </a>
    '''

custompageshtml = ""
# Creating links to custom pages
for custompage in os.listdir('custom'):
    custompage = os.path.splitext(custompage)[0]
    custompageshtml += f'<a href="{webpath}{custompage}{htmlext}" class="{"item right" if len(custompageshtml) == 0 else "item"}">{custompage}</a>'

templates["base"] = templates["base"].replace("{channels}",channelshtml).replace("{custompages}",custompageshtml).replace("{webpath}",webpath).replace("{sitename}",sitename)



# Create video pages
for root, subdirs, files in os.walk(ytpath):
    print("Creating video pages for",root)
    for file in (file for file in files if file.endswith(".info.json")):
        try:
            with open(os.path.join(root,file),"r") as f:
                v = json.load(f)
            # Skip channel/playlist info.json files
            if v.get("_type") == "playlist" or (len(v["id"]) == 24 and v.get("extractor") == "youtube:tab"):
                continue
            # Set mp4 path
            mp4path = f"{os.path.join(ytpathweb + root[len(ytpath):], file[:-len('.info.json')])}.mp4"
            for ext in ["mp4","webm","mkv"]:
                if os.path.exists(altpath := os.path.join(root,file)[:-len('.info.json')] + f".{ext}"):
                    mp4path = f"{os.path.join(ytpathweb + root[len(ytpath):], file[:-len('.info.json')])}.{ext}"
                    break
    
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
                            uploader_url=(f'{webpath}channels/' + v.get("uploader_id",v.get("channel_id")) + f'{htmlext}' if '/channels/' in root else f'{webpath}channels/other{htmlext}'),
                            uploader_id=v.get("uploader_id",v.get("channel_id")),
                            uploader=html.escape(v['uploader']),
                            date=f"{v['upload_date'][:4]}-{v['upload_date'][4:6]}-{v['upload_date'][6:]}",
                            video=urllib.parse.quote(mp4path),
                            thumbnail=urllib.parse.quote(thumbnail),
                            download=downloadbtn
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
                        <a href="{webpath}channels/{channel}{htmlext}" class="ui card">
                            <div class="content">
                                <div class="header">{html.escape(channels[channel]['name'])}</div>
                                <div class="meta">{channel}</div>
                                <div class="description">
                                    {len(channels[channel]['videos'])} videos{' (' + str(channels[channel]['removed']) + ' removed)' if channels[channel]['removed'] > 0 else ''}
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
                <a href="{webpath}videos/{v['id']}{htmlext}" class="ui fluid card">
                  <div class="image thumbnail">
                        <img loading="lazy" src="{urllib.parse.quote(v['custom_thumbnail'])}">
                  </div>
                  <div class="content{' removedvideo' if v["removed"] else ''}">
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
                note=get_channel_note(channel),
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
for custompage in os.listdir('custom'):
    with open(f"custom/{custompage}", "r") as custompagef:
        custompage = os.path.splitext(custompage)[0]
        with open(os.path.join(outpath,f"{custompage}.html"),"w") as f:
            f.write(templates["base"].format(title=custompage,meta="",content=custompagef.read()))
with open(os.path.join(outpath,f"index.html"),"w") as f:
    f.write(templates["base"].format(title="Home",meta=genMeta(
            {
                "description": f"{sitename} - archive"
            }
        ),content=templates["index"].replace("{sitename}",sitename)))

print("Done")
