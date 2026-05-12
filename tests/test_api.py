import io
from PIL import Image


def _make_test_jpg():
    buf = io.BytesIO()
    img = Image.new("RGB", (100, 100), color="red")
    img.save(buf, format="JPEG")
    buf.seek(0)
    return buf


class TestConvertEndpoint:
    def test_convert_jpg_to_png(self, client):
        img = _make_test_jpg()
        response = client.post(
            "/api/convert",
            files={"file": ("test.jpg", img, "image/jpeg")},
            data={"output_format": "png"},
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"

    def test_rejects_no_file(self, client):
        response = client.post("/api/convert", data={"output_format": "png"})
        assert response.status_code == 422

    def test_rejects_invalid_format(self, client):
        img = _make_test_jpg()
        response = client.post(
            "/api/convert",
            files={"file": ("test.jpg", img, "image/jpeg")},
            data={"output_format": "xyz"},
        )
        assert response.status_code == 400


class TestInfoEndpoint:
    def test_formats(self, client):
        response = client.get("/api/formats")
        assert response.status_code == 200
        data = response.json()
        assert "input" in data
        assert "output" in data


class TestStaticFiles:
    def test_serves_index(self, client):
        response = client.get("/")
        assert response.status_code == 200
