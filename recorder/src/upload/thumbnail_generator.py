import os
from logging import Logger
from typing import Optional

try:
    from PIL import Image
except ImportError:
    Image = None


def generate_youtube_thumbnail(
    screenshots_folder: str, output_path: str, log: Logger
) -> Optional[str]:
    """
    Generates a 1280x720 (16:9) collage thumbnail from vertical screenshots.
    Returns the path to the generated thumbnail, or None if failed.
    """
    if Image is None:
        log.error("Pillow library is not installed. Cannot generate thumbnail.")
        return None

    if not os.path.exists(screenshots_folder):
        log.warning("Screenshots folder does not exist: %s", screenshots_folder)
        return None

    jpgs = sorted([f for f in os.listdir(screenshots_folder) if f.endswith(".jpg")])
    if not jpgs:
        log.warning("No screenshots found in %s", screenshots_folder)
        return None

    paths = [os.path.join(screenshots_folder, f) for f in jpgs]

    if len(paths) == 1:
        # User preference: duplicate 3 times
        selected_paths = [paths[0], paths[0], paths[0]]
    elif len(paths) == 2:
        # User preference: Photo2 - Photo1 - Photo2
        selected_paths = [paths[1], paths[0], paths[1]]
    else:
        # Pick 3 spaced-out screenshots (at 25%, 50%, 75% marks)
        idx_25 = len(paths) // 4
        idx_50 = len(paths) // 2
        idx_75 = (3 * len(paths)) // 4
        selected_paths = [paths[idx_25], paths[idx_50], paths[idx_75]]

    try:
        # Canvas sizes
        canvas_w = 1280
        canvas_h = 720
        canvas = Image.new("RGB", (canvas_w, canvas_h), (0, 0, 0))

        # Slice configuration (Left, Center, Right)
        slices = [
            {"width": 427, "x_offset": 0},
            {"width": 426, "x_offset": 427},
            {"width": 427, "x_offset": 853},
        ]

        for i in range(3):
            img_path = selected_paths[i]
            slice_cfg = slices[i]
            target_w = slice_cfg["width"]
            target_h = canvas_h

            with Image.open(img_path) as img:
                # 1. Auto-crop black borders from the original screenshot
                gray = img.convert("L")
                bbox = gray.point(lambda p: p > 15 and 255).getbbox()
                if bbox:
                    img = img.crop(bbox)

                # Force crop an extra 4 pixels from all edges to completely eliminate
                # any faint 1px/2px compression artifacts or anti-aliasing lines on the edges.
                w, h = img.size
                if w > 8 and h > 8:
                    img = img.crop((4, 4, w - 4, h - 4))

                # 2. Aspect Fill (Scale to Fill) to ensure no black spaces
                orig_w, orig_h = img.size
                ratio = max(target_w / orig_w, target_h / orig_h)
                new_w = int(orig_w * ratio)
                new_h = int(orig_h * ratio)
                img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

                # 3. Center crop to exact target dimensions
                left = (new_w - target_w) / 2
                top = (new_h - target_h) / 2
                right = left + target_w
                bottom = top + target_h
                img_cropped = img_resized.crop((left, top, right, bottom))

                # Paste onto canvas
                canvas.paste(img_cropped, (slice_cfg["x_offset"], 0))

        canvas.save(output_path, "JPEG", quality=90)
        log.info("Generated 16:9 collage thumbnail at: %s", output_path)
        return output_path

    except Exception as e:
        log.error("Failed to generate custom thumbnail: %s", e)
        return None
