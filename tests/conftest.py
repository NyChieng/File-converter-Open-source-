import os
import tempfile
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

TEST_DIR = Path(__file__).parent


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as d:
        original = os.getenv("TEMP_DIR")
        os.environ["TEMP_DIR"] = d
        yield Path(d)
        if original:
            os.environ["TEMP_DIR"] = original


@pytest.fixture
def sample_jpg():
    path = TEST_DIR / "fixtures" / "sample.jpg"
    path.parent.mkdir(exist_ok=True)
    if not path.exists():
        from PIL import Image
        img = Image.new("RGB", (100, 100), color="red")
        img.save(path, "JPEG")
    return path


@pytest.fixture
def sample_png():
    path = TEST_DIR / "fixtures" / "sample.png"
    path.parent.mkdir(exist_ok=True)
    if not path.exists():
        from PIL import Image
        img = Image.new("RGBA", (100, 100), color="blue")
        img.save(path, "PNG")
    return path


@pytest.fixture
def client():
    from backend.main import app
    with TestClient(app) as c:
        yield c
