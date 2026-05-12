import io
from pathlib import Path
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader


def convert_images_to_pdf(
    image_paths: list[Path], dest: Path,
    fit_to_page: bool = True, page_size: tuple = A4,
) -> Path:
    if not image_paths:
        raise ValueError("Need at least one image")

    c = canvas.Canvas(str(dest), pagesize=page_size)
    pw, ph = page_size

    for img_path in image_paths:
        img = Image.open(img_path)
        if img.mode == "RGBA":
            bg = Image.new("RGB", img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[3])
            img = bg
        elif img.mode not in ("RGB", "L"):
            img = img.convert("RGB")

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=90)
        buf.seek(0)
        reader = ImageReader(buf)

        iw, ih = img.size
        if fit_to_page:
            scale = min(pw / iw, ph / ih) * 0.92
            dw, dh = iw * scale, ih * scale
        else:
            dw, dh = iw, ih
        x, y = (pw - dw) / 2, (ph - dh) / 2

        c.drawImage(reader, x, y, dw, dh, preserveAspectRatio=True)
        c.showPage()
        img.close()
        buf.close()

    c.save()
    return dest
