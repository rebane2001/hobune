import html


def generate_meta_tags(meta):
    h = ""
    for m in meta:
        h += f'<meta name="{m}" content="{html.escape(meta[m])}">'
    return h
