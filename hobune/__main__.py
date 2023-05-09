import os

from hobune.assets import init_assets, update_templates
from hobune.channels import initialize_channels, create_channel_pages
from hobune.logger import logger
from hobune.config import load_config
from hobune.videos import create_video_pages


def main():
    # TODO: Remove
    os.chdir("..")

    config = load_config()
    if not config:
        exit()

    templates = init_assets(config.output_path)

    # Extension appended to links
    html_ext = ".html" if config.add_html_ext else ""

    logger.info("Populating channels list")
    channels = initialize_channels(config)

    update_templates(config, templates, channels, html_ext)

    logger.info("Creating video pages")
    create_video_pages(config, channels, templates)

    logger.info("Creating channel pages")
    create_channel_pages(config, templates, channels, html_ext)

    logger.info("Done!")


if __name__ == '__main__':
    main()
