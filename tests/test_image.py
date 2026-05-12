import pytest
from pathlib import Path
from backend.converters.image import convert_image


def _make_test_image(path: Path, fmt: str, size=(100, 100), color="red"):
    from PIL import Image
    mode = "RGBA" if fmt.upper() == "PNG" else "RGB"
    img = Image.new(mode, size, color=color)
    img.save(path, fmt.upper())
    return path


class TestConvertImage:
    def test_jpg_to_png(self, temp_dir):
        src = _make_test_image(temp_dir / "test.jpg", "JPEG")
        dest = temp_dir / "output.png"
        result = convert_image(src, dest, "png")
        assert result.exists()
        from PIL import Image
        img = Image.open(result)
        assert img.format == "PNG"

    def test_png_to_webp(self, temp_dir):
        src = _make_test_image(temp_dir / "test.png", "PNG")
        dest = temp_dir / "output.webp"
        result = convert_image(src, dest, "webp")
        assert result.suffix == ".webp"

    def test_jpg_to_pdf(self, temp_dir):
        src = _make_test_image(temp_dir / "test.jpg", "JPEG")
        dest = temp_dir / "output.pdf"
        result = convert_image(src, dest, "pdf")
        assert result.suffix == ".pdf"
        assert result.stat().st_size > 0

    def test_invalid_output_format(self, temp_dir):
        src = _make_test_image(temp_dir / "test.jpg", "JPEG")
        with pytest.raises(ValueError, match="Unsupported"):
            convert_image(src, temp_dir / "out.xyz", "xyz")
