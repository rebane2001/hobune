import os
import urllib.parse
import html


def generate_meta_tags(meta):
    h = ""
    for m in meta:
        h += f'<meta name="{m}" content="{html.escape(meta[m])}">'
    return h


# Quotes URL and fixes backslashes if necessary
def quote_url(url):
    if os.path.sep == "\\":
        url = url.replace("\\", "/")
        url = url.replace("%5C", "/")
    return urllib.parse.quote(url)

