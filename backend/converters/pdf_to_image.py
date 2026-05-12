import zipfile
from pathlib import Path


def _pdf2image_available():
    import shutil
    if shutil.which("pdftoppm") or shutil.which("pdfinfo"):
        try:
            from pdf2image import convert_from_path
            return True
        except Exception:
            pass
    return False


def _parse_page_range(pages_str: str | None, total_pages: int) -> list[int]:
    if pages_str is None:
        return list(range(1, total_pages + 1))
    pages = []
    for part in pages_str.split(","):
        part = part.strip()
        if "-" in part:
            start, end = part.split("-", 1)
            start, end = int(start), int(end)
            if start < 1 or end > total_pages or start > end:
                raise ValueError(
                    f"Invalid page range: {start}-{end} (total: {total_pages})"
                )
            pages.extend(range(start, end + 1))
        else:
            p = int(part)
            if p < 1 or p > total_pages:
                raise ValueError(f"Invalid page: {p} (total: {total_pages})")
            pages.append(p)
    return pages


def _get_page_count(src: Path) -> int:
    try:
        import fitz
        doc = fitz.open(src)
        count = doc.page_count
        doc.close()
        return count
    except Exception:
        from pdf2image import convert_from_path
        from pdf2image.pdf2image import pdfinfo_from_path
        info = pdfinfo_from_path(str(src))
        return info["Pages"]


def convert_pdf_to_image(
    src: Path, dest: Path, output_format: str = "jpg",
    pages: str | None = None, dpi: int = 200,
) -> Path | list[Path]:
    output_format = output_format.lower().lstrip(".")
    fmt = "JPEG" if output_format in ("jpg", "jpeg") else "PNG"

    if _pdf2image_available():
        from pdf2image import convert_from_path
        images = convert_from_path(src, dpi=dpi)
    else:
        import fitz
        doc = fitz.open(src)
        images = []
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        for i in range(doc.page_count):
            page = doc[i]
            pix = page.get_pixmap(matrix=mat)
            from PIL import Image
            samples = pix.samples
            if not isinstance(samples, bytes):
                samples = bytes(samples)
            img = Image.frombytes("RGB", [pix.width, pix.height], samples)
            images.append(img)
        doc.close()

    page_numbers = _parse_page_range(pages, len(images))

    if len(page_numbers) == 1:
        out_path = dest.parent / f"{dest.stem}.{output_format}"
        images[page_numbers[0] - 1].save(out_path, fmt)
        return out_path

    results = []
    for i, p in enumerate(page_numbers):
        out_path = dest.parent / f"{dest.stem}_{i + 1}.{output_format}"
        images[p - 1].save(out_path, fmt)
        results.append(out_path)

    if len(results) > 1:
        zip_path = dest.parent / f"{dest.stem}.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for r in results:
                zf.write(r, r.name)
        return zip_path
    return results[0] if results else None
