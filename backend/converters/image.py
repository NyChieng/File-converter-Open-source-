from pathlib import Path
from PIL import Image

SUPPORTED_OUTPUT = {"jpg", "jpeg", "png", "webp", "bmp", "tiff", "pdf"}


def convert_image(src: Path, dest: Path, output_format: str, quality: int = 85) -> Path:
    output_format = output_format.lower().lstrip(".")
    if output_format not in SUPPORTED_OUTPUT:
        raise ValueError(f"Unsupported output format: {output_format}")

    img = Image.open(src)

    if img.mode in ("P", "PA"):
        img = img.convert("RGBA")
    elif img.mode not in ("RGB", "RGBA", "L", "LA", "CMYK", "YCbCr", "LAB", "HSV"):
        img = img.convert("RGB")

    if output_format in ("jpg", "jpeg"):
        if img.mode == "RGBA":
            background = Image.new("RGB", img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])
            img = background
        elif img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        img.save(dest, "JPEG", quality=quality)
    elif output_format == "png":
        img.save(dest, "PNG", optimize=True)
    elif output_format == "webp":
        img.save(dest, "WEBP", quality=quality)
    elif output_format == "bmp":
        img.save(dest, "BMP")
    elif output_format == "tiff":
        img.save(dest, "TIFF")
    elif output_format == "pdf":
        if img.mode == "RGBA":
            background = Image.new("RGB", img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])
            img = background
        elif img.mode != "RGB":
            img = img.convert("RGB")
        img.save(dest, "PDF", resolution=100.0)

    img.close()
    return dest
