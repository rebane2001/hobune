# Hobune
A lightweight static HTML generator for self-hosting yt-dlp video archives.
  
# Features
- Static HTML (fast and secure)
- Parses yt-dlp info.json format
- Channel pages (with thumbnails, name history)
- Watch page (with stats, description etc)
- Download buttons (video, description, thumbnail, subtitles)
- Highlight deleted/unlisted videos
- Client-side search/sorting

# Usage
1. Clone this repo (or download as zip).
2. Rename the `default.json` file to `config.json` and edit the variables to suit your setup:
   - `site_name`: Name/Title of the site (e.g. "Hobune")
   - `files_path`: Local path of the video files (e.g. "/var/www/html/files/")
   - `files_web_path`: Web path of the video files (e.g. "/files/" or "https://example.com/files/")
   - `web_root`: Web root path (e.g. "/" or "https://example.com/")
   - `output_path`: Output path for the HTML files (e.g. "/var/www/html/")
   - `add_html_ext`: Add HTML extension to links (e.g. link to /videos/foobar.html instead of /videos/foobar)
   - `removed_videos_file`: A text file where each line ends with a removed video ID (optional, e.g. "~/removed_videos.txt")
   - `unlisted_videos_file`: Unlisted videos file - similar to the removed videos file (optional)

3. Run `python3 hobune.py`, this will generate HTML files in your `output_path`.
4. (optionally) Configure your webserver to allow downloads from /dl URLs and HTML pages without extensions.

```
# nginx sample config

location / {
    try_files $uri.html $uri $uri/ =404;
}

location /dl {
    alias /var/www/html/;
    add_header Content-disposition "attachment; filename=$1";
    try_files $uri $uri/ =404;
}
```

It is also recommended to edit the python script to suit your exact needs, since your setup probably won't be 1:1 same as the expected one.
