import html
import json
import os
import urllib.parse

from comments import getCommentsHTML
from hobune.channels import is_full_channel
from hobune.logger import logger
from hobune.util import generate_meta_tags, quote_url


def generate_download_button(name, url, tag=None, prefix="/dl"):
    tag_part = ""
    if tag:
        tag_part = f"""
            <a class="ui basic right pointing label">
                {html.escape(tag)}
            </a>"""
    return f"""
    <a href="{prefix}{url}">
        {tag_part}
        <div class="ui button downloadbtn">
            <i class="download icon"></i> {html.escape(name)}
        </div>
    </a>
    <br>
    """


def create_video_pages(config, channels, templates):
    for channel in channels:
        logger.debug(f"Creating video pages for {channels[channel].name}")
        for video_entry in channels[channel].videos:
            root = video_entry["root"]
            file = video_entry["file"]
            base = file[:-len(".info.json")]
            files = os.listdir(root)
            try:
                with open(os.path.join(root, file), "r") as f:
                    v = json.load(f)
                # Generate comments
                comments_html, comments_count = getCommentsHTML(html.escape(v['title']), v['id'])
                comments_link = ""
                if comments_html:
                    with open(os.path.join(config.output_path, f"comments/{v['id']}.html"), "w") as f:
                        f.write(templates["base"].format(title=html.escape(v['title'] + ' - Comments'), meta=generate_meta_tags(
                            {
                                "description": v['description'][:256],
                                "author": v['uploader']
                            }
                        ), content=comments_html))
                    comments_link = f'<h3 class="ui small header" style="margin: 0;"><a href="/comments/{v["id"]}">View comments ({comments_count})</a></h3>'
                # Set mp4 path
                mp4path = f"{os.path.join(config.files_web_path + root[len(config.files_path):], base)}.mp4"
                for ext in ["mp4", "webm", "mkv"]:
                    if f"{base}.{ext}" in files:
                        mp4path = f"{os.path.join(config.files_web_path + root[len(config.files_path):], base)}.{ext}"
                        break

                # Get thumbnail path
                thumbnail = "/default.png"
                for ext in ["webp", "jpg", "png"]:
                    if (thumbnail_file := f"{base}.{ext}") in files:
                        thumbnail = config.files_web_path + (os.path.join(root, thumbnail_file))[len(config.files_path):]

                # Create a download button for the video
                download_buttons_html = generate_download_button("Download video", mp4path)

                # Create multiple video download buttons if we have multiple formats
                for ext in ["webm", "mkv"]:
                    if (alt_file := f"{base}.{ext}") in files:
                        alt_file_url = config.files_web_path + (os.path.join(root, alt_file))[len(config.files_path):]
                        download_buttons_html = generate_download_button("Download video", mp4path, tag="mp4") + \
                                                generate_download_button("Download video", alt_file_url, tag=ext)

                # Description download
                if (desc_file := f"{base}.description") in files:
                    desc_file_url = config.files_web_path + os.path.join(root, desc_file)[len(config.files_path):]
                    download_buttons_html += generate_download_button("Description", desc_file_url)

                # Thumbnail download
                if thumbnail != "/default.png":
                    download_buttons_html += generate_download_button("Thumbnail", thumbnail)

                # Subtitles download
                for vtt in (vtt for vtt in files if vtt.endswith(".vtt")):
                    if vtt.startswith(base):
                        vtt_url = os.path.join(config.files_web_path + root[len(config.files_path):], vtt)
                        vtt_tag = vtt[len(base) + 1:-len('.vtt')]
                        download_buttons_html += generate_download_button("Subtitles", vtt_url, tag=vtt_tag)

                # Create HTML
                page_html = templates["video"].format(
                    title=html.escape(v['title']),
                    description=html.escape(v['description']).replace('\n', '<br>'),
                    views=v['view_count'],
                    # TODO: Fix these
                    uploader_url="",
                    uploader_id="",
                    # uploader_url=(f'{config.web_root}channels/' + getUploaderId(
                    #     v) + f'{html_ext}' if is_full_channel(
                    #     root) else f'{config.web_root}channels/other{html_ext}'),
                    # uploader_id=getUploaderId(v),
                    uploader=html.escape(v['uploader']),
                    date=f"{v['upload_date'][:4]}-{v['upload_date'][4:6]}-{v['upload_date'][6:]}",
                    video=quote_url(mp4path),
                    thumbnail=quote_url(thumbnail),
                    download=download_buttons_html,
                    comments=comments_link
                )

                with open(os.path.join(config.output_path, f"videos/{v['id']}.html"), "w") as f:
                    f.write(
                        templates["base"].format(title=html.escape(v['title']), meta=generate_meta_tags(
                            {
                                "description": v['description'][:256],
                                "author": v['uploader']
                            }
                        ), content=page_html
                                                 )
                    )
            except Exception as e:
                logger.error(f"Error processing {file}")
                print(e)