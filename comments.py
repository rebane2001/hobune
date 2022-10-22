import json

"""
This script will look for a VIDEOID.jsonl file in comments_path and generate a HTML page based on it.
The comments format used is a modified version of the YouTube API, if you put the YT API comment responses into a jsonl file it *should* work.

This script assumes good-faith data, as the HTML used is what YouTube API provides.
Malicious actors could use this to achieve XSS, so please make sure your data is coming from a trusted source.

This script purposefully avoids config.json as I want people to understand what they're getting into before using this.
"""

comments_enabled = False
comments_path = "/var/www/html/comments/"

def getCommentHTML(csnip):
    timestamp = csnip["publishedAt"].replace("T"," ").replace("Z", " ")
    if csnip["publishedAt"] != csnip["updatedAt"]:
        timestamp += f' (edited {csnip["updatedAt"].replace("T"," ").replace("Z", " ")})'
    likes = str(csnip["likeCount"]) + (" like" if csnip["likeCount"] == 1 else " likes")
    return f"""
<a href="{csnip["authorChannelUrl"]}"><b>{csnip["authorDisplayName"]}</b></a> <i>{timestamp}</i>
<p>{csnip["textDisplay"]}</p>
<small>{likes}</small>
"""

def getCommentsHTML(title, videoid):
    if not comments_enabled:
        return False, 0
    comments = []
    header = {}
    try:
        with open(f"{comments_path}/{videoid}.jsonl", "r") as f:
            header = json.loads(f.readline())
            # Hacky workaround if you don't use my format of comments (w/header)
            if not "time_fetched" in header:
                comments.append(header)
                header = {"time_fetched": "N/A"}
            for l in f:
                comments.append(json.loads(l))
    except Exception:
        return False, 0
    comments_html = f"""<div class="ui container main">
    <h1 class="ui big header">{title}</h1>
                        <a href="/videos/{videoid}">Back to video page</a> | <a href="/comments/{videoid}.jsonl">Download comments jsonl</a>
                                     <h2 class="ui header">Comments (archived {header["time_fetched"][:16].replace("T", " ")})</h2>
                                                                                                         <div class="comments">\n"""
    comments_count = 0
    for comment in comments:
        comments_count += 1
        csnip = comment["snippet"]["topLevelComment"]["snippet"]
        comment_html = getCommentHTML(csnip)
        if "replies" in comment:
            replies = ""
            for reply in comment["replies"]["comments"][::-1]:
                replies += f'<div class="reply">{getCommentHTML(reply["snippet"])}</div>\n'
            comment_html += f"<details><summary>Replies ({len(comment['replies']['comments'])})</summary>\n{replies}</details>"
        comments_html += f'<div class="comment">{comment_html}</div>\n'
    comments_html += "</div></div>"
    return comments_html, comments_count