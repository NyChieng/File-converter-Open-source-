import pytest
from pathlib import Path
from PIL import Image
from backend.converters.pdf_to_image import convert_pdf_to_image


def _make_test_pdf(path: Path, pages: int = 2):
    from reportlab.pdfgen import canvas
    c = canvas.Canvas(str(path))
    for i in range(pages):
        c.drawString(100, 500, f"Page {i + 1}")
        c.showPage()
    c.save()
    return path


class TestConvertPdfToImage:
    def test_pdf_to_jpg_all_pages(self, temp_dir):
        src = _make_test_pdf(temp_dir / "test.pdf", pages=2)
        dest = temp_dir / "output.jpg"
        result = convert_pdf_to_image(src, dest, "jpg")
        assert result.exists()

    def test_pdf_to_png_single_page(self, temp_dir):
        src = _make_test_pdf(temp_dir / "test.pdf", pages=2)
        dest = temp_dir / "output.png"
        result = convert_pdf_to_image(src, dest, "png", pages="1")
        assert result.exists()
        img = Image.open(result)
        assert img.format == "PNG"

    def test_pdf_to_multiple_images(self, temp_dir):
        src = _make_test_pdf(temp_dir / "test.pdf", pages=3)
        dest_dir = temp_dir / "output"
        dest_dir.mkdir()
        result = convert_pdf_to_image(src, dest_dir / "page", "jpg", pages="1-2")
        assert result.suffix == ".zip"

    def test_invalid_page_range(self, temp_dir):
        src = _make_test_pdf(temp_dir / "test.pdf", pages=2)
        dest = temp_dir / "output.jpg"
        with pytest.raises(ValueError):
            convert_pdf_to_image(src, dest, "jpg", pages="10-20")
