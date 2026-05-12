import zipfile
from pathlib import Path
from pdf2image import convert_from_path


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


def convert_pdf_to_image(
    src: Path, dest: Path, output_format: str = "jpg",
    pages: str | None = None, dpi: int = 200,
) -> Path | list[Path]:
    output_format = output_format.lower().lstrip(".")
    fmt = "JPEG" if output_format in ("jpg", "jpeg") else "PNG"

    images = convert_from_path(src, dpi=dpi)
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
