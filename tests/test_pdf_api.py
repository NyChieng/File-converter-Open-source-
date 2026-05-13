import io
from pathlib import Path


def _make_test_pdf():
    from reportlab.pdfgen import canvas
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    c.drawString(100, 500, "Test page 1")
    c.showPage()
    c.drawString(100, 500, "Test page 2")
    c.showPage()
    c.save()
    buf.seek(0)
    return buf


class TestPdfToImageEndpoint:
    def test_convert_pdf_to_jpg(self, client):
        pdf = _make_test_pdf()
        response = client.post(
            "/api/convert",
            files={"file": ("test.pdf", pdf, "application/pdf")},
            data={"output_format": "jpg"},
        )
        assert response.status_code == 200, f"Body: {response.text}"
        assert response.headers["content-type"] in ("image/jpeg", "image/jpg")

    def test_convert_pdf_to_png(self, client):
        pdf = _make_test_pdf()
        response = client.post(
            "/api/convert",
            files={"file": ("test.pdf", pdf, "application/pdf")},
            data={"output_format": "png"},
        )
        assert response.status_code == 200, f"Body: {response.text}"
        assert response.headers["content-type"] == "image/png"
