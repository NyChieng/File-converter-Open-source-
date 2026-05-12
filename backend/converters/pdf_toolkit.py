from pathlib import Path
import pikepdf


def compress_pdf(src: Path, dest: Path) -> Path:
    pdf = pikepdf.Pdf.open(src)
    pdf.save(
        dest,
        compress_streams=True,
        object_stream_mode=pikepdf.ObjectStreamMode.generate,
    )
    pdf.close()
    return dest


def merge_pdfs(paths: list[Path], dest: Path) -> Path:
    if not paths:
        raise ValueError("Need at least one PDF to merge")
    merged = pikepdf.Pdf.new()
    for path in paths:
        src = pikepdf.Pdf.open(path)
        merged.pages.extend(src.pages)
        src.close()
    merged.save(dest)
    merged.close()
    return dest


def split_pdf(src: Path, out_dir: Path, ranges: list[str]) -> list[Path]:
    pdf = pikepdf.Pdf.open(src)
    total = len(pdf.pages)
    results = []
    for i, r in enumerate(ranges):
        out = pikepdf.Pdf.new()
        for part in r.split(","):
            part = part.strip()
            if "-" in part:
                start, end = map(int, part.split("-", 1))
            else:
                start = end = int(part)
            if start < 1 or end > total:
                raise ValueError(
                    f"Page range {start}-{end} out of bounds (1-{total})"
                )
            for p in range(start - 1, end):
                out.pages.append(pdf.pages[p])
        out_path = out_dir / f"split_{i + 1}.pdf"
        out.save(out_path)
        out.close()
        results.append(out_path)
    pdf.close()
    return results


def reorder_pages(src: Path, dest: Path, order: list[int]) -> Path:
    pdf = pikepdf.Pdf.open(src)
    total = len(pdf.pages)
    if any(p < 1 or p > total for p in order):
        raise ValueError(f"Order values must be 1-{total}")
    if len(order) != total:
        raise ValueError(f"Order must include all {total} pages")
    new_pdf = pikepdf.Pdf.new()
    for p in order:
        new_pdf.pages.append(pdf.pages[p - 1])
    new_pdf.save(dest)
    new_pdf.close()
    pdf.close()
    return dest


def rotate_pages(src: Path, dest: Path, rotations: dict[str, int]) -> Path:
    pdf = pikepdf.Pdf.open(src)
    for page_str, angle in rotations.items():
        try:
            p = int(page_str) - 1
        except ValueError:
            raise ValueError(f"Invalid page number: {page_str}")
        if p < 0 or p >= len(pdf.pages):
            raise ValueError(f"Page {page_str} out of range")
        pdf.pages[p].rotate(angle, relative=True)
    pdf.save(dest)
    pdf.close()
    return dest


def delete_pages(src: Path, dest: Path, pages_to_delete: list[int]) -> Path:
    pdf = pikepdf.Pdf.open(src)
    total = len(pdf.pages)
    if len(pages_to_delete) >= total:
        raise ValueError("Cannot delete all pages")
    to_keep = [i for i in range(total) if (i + 1) not in pages_to_delete]
    new_pdf = pikepdf.Pdf.new()
    for i in to_keep:
        new_pdf.pages.append(pdf.pages[i])
    new_pdf.save(dest)
    new_pdf.close()
    pdf.close()
    return dest


def get_page_count(filepath: Path) -> int:
    pdf = pikepdf.Pdf.open(filepath)
    count = len(pdf.pages)
    pdf.close()
    return count


def edit_pdf_text(src: Path, dest: Path, edits: list[dict]) -> Path:
    import fitz
    doc = fitz.open(src)
    for edit in edits:
        page_num = edit["page"] - 1
        if page_num < 0 or page_num >= len(doc):
            raise ValueError(f"Page {edit['page']} out of range")
        page = doc[page_num]
        found = page.search_for(edit["old_text"])
        for rect in found:
            page.add_redact_annot(rect, text=edit["new_text"])
        page.apply_redactions()
    doc.save(dest)
    doc.close()
    return dest
