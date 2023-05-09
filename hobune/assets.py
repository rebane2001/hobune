import html
import os
import shutil

from hobune.util import generate_meta_tags


def init_assets(output_path):
    # Load html templates into memory
    templates = {}
    for template in os.listdir('templates'):
        if template.endswith(".html"):
            with open(os.path.join('templates', template), "r") as f:
                templates[template[:-len(".html")]] = f.read()

    # Create folders
    for folder in ["channels", "videos", "comments"]:
        os.makedirs(os.path.join(output_path, folder), exist_ok=True)

    # Copy assets
    shutil.copy("templates/hobune.css", output_path)
    shutil.copy("templates/hobune.js", output_path)
    shutil.copy("templates/favicon.ico", output_path)

    return templates


def update_templates(config, templates, channels, html_ext):
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

    custom_pages_html = ""
    # Creating links to custom pages
    for custom_page in os.listdir('custom'):
        custom_page = os.path.splitext(custom_page)[0]
        custom_pages_html += f'<a href="{config.web_root}{custom_page}{html_ext}" class="{"item right" if len(custom_pages_html) == 0 else "item"}">{custom_page}</a> '

    templates["base"] = templates["base"].replace("{channels}", channels_html).replace("{custom_pages}",
                                                                                       custom_pages_html).replace(
        "{config.web_root}", config.web_root).replace("{config.site_name}", config.site_name)

    print("Writing other pages")
    for custom_page in os.listdir('custom'):
        with open(f"custom/{custom_page}", "r") as custom_page_file:
            custom_page = os.path.splitext(custom_page)[0]
            with open(os.path.join(config.output_path, f"{custom_page}.html"), "w") as f:
                f.write(templates["base"].format(title=custom_page, meta="", content=custom_page_file.read()))
    with open(os.path.join(config.output_path, "index.html"), "w") as f:
        f.write(templates["base"].format(title="Home", meta=generate_meta_tags(
            {
                "description": f"{config.site_name} - archive"
            }
        ), content=templates["index"].replace("{config.site_name}", config.site_name)))
