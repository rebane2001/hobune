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


def update_templates(config, templates, html_ext):
    custom_pages_html = ""
    # Creating links to custom pages
    for custom_page in os.listdir('custom'):
        custom_page = os.path.splitext(custom_page)[0]
        custom_pages_html += f'<a href="{config.web_root}{custom_page}{html_ext}" class="{"item right" if len(custom_pages_html) == 0 else "item"}">{custom_page}</a> '

    templates["base"] = templates["base"]\
        .replace("{custom_pages}", custom_pages_html)\
        .replace("{web_root}", config.web_root)\
        .replace("{site_name}", config.site_name)

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
        ), content=templates["index"].replace("{site_name}", config.site_name)))
