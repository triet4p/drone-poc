from pathlib import Path
from PIL import Image, ImageOps
from ..config import UPLOADS, PREVIEWS, THUMBS

def normalize(src: Image.Image, stem: str) -> tuple[int, int]:
    img = ImageOps.exif_transpose(src).convert("RGB")
    if max(img.size) > 6000:
        img.thumbnail((6000, 6000), Image.LANCZOS)
    img.save(UPLOADS / f"{stem}.jpg", "JPEG", quality=92)
    prev = img.copy()
    prev.thumbnail((2048, 2048), Image.LANCZOS)
    prev.save(PREVIEWS / f"{stem}.jpg", "JPEG", quality=88)
    thumb = img.copy()
    thumb.thumbnail((640, 640), Image.LANCZOS)
    thumb.save(THUMBS / f"{stem}.jpg", "JPEG", quality=85)
    return img.size


