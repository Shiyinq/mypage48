"""Shared media helpers for the notification channels.

Both channels capture the recap web screenshot from the same MyPage48 page and
split oversized screenshots the same way, so this lives here instead of inside
one channel's module.
"""

import logging
import math
import os

from PIL import Image

log = logging.getLogger("notify")

LIVE_DETAIL_BASE_URL = "https://mypage48.com/jkt48/live/history/live"


def _process_and_split_image(image_path: str, max_height: int = 8000) -> list[str]:
    """Check if image exceeds max_height, and if so, split it into multiple images."""
    try:
        # Increase max pixels limit for large web screenshots
        Image.MAX_IMAGE_PIXELS = None

        with Image.open(image_path) as img:
            width, height = img.size
            if height <= max_height:
                return [image_path]

            num_parts = math.ceil(height / max_height)
            part_height = math.ceil(height / num_parts)

            split_paths = []
            base_name, ext = os.path.splitext(image_path)

            for i in range(num_parts):
                top = i * part_height
                bottom = min((i + 1) * part_height, height)

                part_img = img.crop((0, top, width, bottom))
                part_path = f"{base_name}_part{i+1}{ext}"

                # Convert RGBA to RGB if saving as JPEG to avoid error
                if part_img.mode in ("RGBA", "P") and ext.lower() in (".jpg", ".jpeg"):
                    part_img = part_img.convert("RGB")

                part_img.save(part_path)
                split_paths.append(part_path)

            return split_paths
    except Exception as e:
        log.warning("Failed to process/split image %s: %s", image_path, e)
        return [image_path]
