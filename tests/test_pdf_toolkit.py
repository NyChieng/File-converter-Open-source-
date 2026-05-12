import pytest
from pathlib import Path
from backend.converters.pdf_toolkit import (
    compress_pdf, merge_pdfs, reorder_pages, rotate_pages, delete_pages,
    get_page_count,
)


def _make_test_pdf(path: Path, pages: int = 3):
    from reportlab.pdfgen import canvas
    c = canvas.Canvas(str(path))
    for i in range(pages):
        c.drawString(100, 500, f"Page {i + 1}")
        c.showPage()
    c.save()
    return path


class TestCompressPdf:
    def test_compress(self, temp_dir):
        src = _make_test_pdf(temp_dir / "input.pdf", pages=5)
        dest = temp_dir / "compressed.pdf"
        result = compress_pdf(src, dest)
        assert result.exists()
        assert result.stat().st_size > 0


class TestMergePdfs:
    def test_merges_two(self, temp_dir):
        a = _make_test_pdf(temp_dir / "a.pdf", pages=2)
        b = _make_test_pdf(temp_dir / "b.pdf", pages=2)
        dest = temp_dir / "merged.pdf"
        result = merge_pdfs([a, b], dest)
        assert result.exists()

    def test_empty_raises(self, temp_dir):
        with pytest.raises(ValueError):
            merge_pdfs([], temp_dir / "out.pdf")


class TestReorderPages:
    def test_reorder(self, temp_dir):
        src = _make_test_pdf(temp_dir / "input.pdf", pages=4)
        dest = temp_dir / "reordered.pdf"
        result = reorder_pages(src, dest, [3, 1, 4, 2])
        assert result.exists()

    def test_invalid_order(self, temp_dir):
        src = _make_test_pdf(temp_dir / "input.pdf", pages=3)
        with pytest.raises(ValueError):
            reorder_pages(src, temp_dir / "out.pdf", [1, 2, 5])


class TestRotatePages:
    def test_rotate(self, temp_dir):
        src = _make_test_pdf(temp_dir / "input.pdf", pages=2)
        dest = temp_dir / "rotated.pdf"
        result = rotate_pages(src, dest, {"1": 90})
        assert result.exists()


class TestDeletePages:
    def test_delete(self, temp_dir):
        src = _make_test_pdf(temp_dir / "input.pdf", pages=4)
        dest = temp_dir / "deleted.pdf"
        result = delete_pages(src, dest, [2, 4])
        assert result.exists()

    def test_delete_all_raises(self, temp_dir):
        src = _make_test_pdf(temp_dir / "input.pdf", pages=2)
        with pytest.raises(ValueError):
            delete_pages(src, temp_dir / "out.pdf", [1, 2])


class TestPageCount:
    def test_page_count(self, temp_dir):
        src = _make_test_pdf(temp_dir / "input.pdf", pages=5)
        assert get_page_count(src) == 5
