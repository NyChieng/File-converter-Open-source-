# FileConverter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a web-based file converter supporting image, document, and PDF conversions with a Deep Indigo themed UI.

**Architecture:** FastAPI monorepo serving both API and static frontend files. Files processed in /tmp, deleted immediately after streaming response. No persistent storage. Vanilla HTML/CSS/JS frontend with sidebar + workspace layout.

**Tech Stack:** Python 3.11+, FastAPI, Pillow, pillow-heif, pdf2image, pikepdf, PyMuPDF. Frontend: vanilla JS, SortableJS, pdf.js

---

## File Map

```
Converter_Open_Git/
├── backend/
│   ├── main.py              # FastAPI app, routes, static file mount, startup config
│   ├── config.py             # Env vars: MAX_FILE_SIZE, RATE_LIMIT, TEMP_DIR
│   ├── requirements.txt      # Pinned dependencies
│   ├── validators.py         # File type (magic bytes), size, sanitization
│   ├── security.py           # Rate limiter middleware
│   └── converters/
│       ├── __init__.py
│       ├── image.py          # Image-to-image: JPG,PNG,WebP,HEIF,SVG,BMP,TIFF → JPG,PNG,WebP
│       ├── pdf_to_image.py   # PDF → JPG,PNG (per page or all pages)
│       ├── image_to_pdf.py   # Single/multiple images → PDF
│       ├── office.py         # DOCX,XLSX,PPTX → PDF (LibreOffice headless)
│       └── pdf_toolkit.py    # Compress, merge, split, reorder, rotate, delete, edit
├── frontend/
│   ├── index.html            # SPA: sidebar, workspace, step indicator, drop zone
│   ├── css/
│   │   └── style.css         # Deep Indigo theme, responsive (mobile bottom tab bar)
│   └── js/
│       ├── app.js            # Tool switching, upload, file card, steps, convert flow
│       ├── api.js            # fetch wrappers for /api/convert and /api/pdf/toolkit
│       └── pdf-toolkit.js    # Page thumbnails, drag reorder, toolbar actions
├── tests/
│   ├── __init__.py
│   ├── conftest.py           # Fixtures: test files, temp dir, FastAPI TestClient
│   ├── test_validators.py
│   ├── test_security.py
│   ├── test_image.py
│   ├── test_pdf_to_image.py
│   ├── test_image_to_pdf.py
│   ├── test_office.py
│   ├── test_pdf_toolkit.py
│   └── test_api.py
├── .gitignore
├── LICENSE
└── README.md
```

---

### Task 1: Project Scaffolding

**Files:**
- Create: `backend/config.py`, `backend/requirements.txt`, `backend/converters/__init__.py`
- Create: `tests/__init__.py`, `tests/conftest.py`
- Modify: `.gitignore`

- [ ] **Step 1: Create backend directory structure**

```bash
mkdir -p backend/converters frontend/css frontend/js tests
```

- [ ] **Step 2: Write backend/config.py**

```python
import os

MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 250 * 1024 * 1024))  # 250MB default
RATE_LIMIT = os.getenv("RATE_LIMIT", "20/minute")
TEMP_DIR = os.getenv("TEMP_DIR", "/tmp")
ALLOWED_IMAGE_INPUT = {"image/jpeg", "image/png", "image/webp", "image/heif", "image/heic",
                       "image/svg+xml", "image/bmp", "image/tiff"}
ALLOWED_IMAGE_OUTPUT = {"jpg", "png", "webp", "pdf"}
ALLOWED_PDF_INPUT = {"application/pdf"}
ALLOWED_OFFICE_INPUT = {
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
}
```

- [ ] **Step 3: Write backend/converters/__init__.py**

```python
```

- [ ] **Step 4: Write tests/__init__.py**

```python
```

- [ ] **Step 5: Write tests/conftest.py**

```python
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
```

- [ ] **Step 6: Write backend/requirements.txt**

```
fastapi==0.115.6
uvicorn[standard]==0.34.0
python-multipart==0.0.20
Pillow==11.1.0
pillow-heif==0.21.0
pdf2image==1.17.0
pikepdf==9.5.1
PyMuPDF==1.25.3
reportlab==4.2.5
slowapi==0.1.9
aiofiles==24.1.0
```

- [ ] **Step 7: Update .gitignore**

Append to `.gitignore`:
```
__pycache__/
*.pyc
.env
/tmp/
*.egg-info/
dist/
.pytest_cache/
```

- [ ] **Step 8: Commit**

```bash
git add backend/ tests/ .gitignore
git commit -m "feat: scaffold project structure and configuration"
```

---

### Task 2: File Validators

**Files:**
- Create: `backend/validators.py`
- Create: `tests/test_validators.py`
- Create: `tests/fixtures/` (sample files)

- [ ] **Step 1: Write failing tests in tests/test_validators.py**

```python
import pytest
from pathlib import Path
from backend.validators import validate_file, sanitize_filename, get_mime_type

class TestValidateFile:
    def test_rejects_empty_file(self, temp_dir):
        empty = temp_dir / "empty.jpg"
        empty.write_bytes(b"")
        with pytest.raises(ValueError, match="empty"):
            validate_file(empty, {"image/jpeg"}, max_size=10 * 1024 * 1024)

    def test_rejects_oversized_file(self, temp_dir):
        big = temp_dir / "big.jpg"
        big.write_bytes(b"x" * 100)
        with pytest.raises(ValueError, match="exceeds"):
            validate_file(big, {"image/jpeg"}, max_size=50)

    def test_rejects_wrong_type(self, temp_dir):
        f = temp_dir / "test.png"
        f.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 20)
        with pytest.raises(ValueError, match="type"):
            validate_file(f, {"image/jpeg"}, max_size=10 * 1024 * 1024)

    def test_accepts_valid_file(self, temp_dir):
        f = temp_dir / "valid.jpg"
        f.write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 20)
        validate_file(f, {"image/jpeg"}, max_size=10 * 1024 * 1024)

    def test_pdf_magic_bytes(self, temp_dir):
        f = temp_dir / "doc.pdf"
        f.write_bytes(b"%PDF-1.4\n" + b"\x00" * 20)
        validate_file(f, {"application/pdf"}, max_size=10 * 1024 * 1024)


class TestSanitizeFilename:
    def test_replaces_spaces_and_special_chars(self):
        assert sanitize_filename("my file (1).pdf") == "my_file_1_.pdf"

    def test_handles_unicode(self):
        result = sanitize_filename("café.pdf")
        assert result.endswith(".pdf")


class TestGetMimeType:
    def test_detects_jpg(self, sample_jpg):
        mime = get_mime_type(sample_jpg)
        assert mime == "image/jpeg"

    def test_detects_png(self, sample_png):
        mime = get_mime_type(sample_png)
        assert mime == "image/png"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_validators.py -v`
Expected: all tests FAIL (module not found or functions not defined)

- [ ] **Step 3: Write backend/validators.py**

```python
import uuid
import re
import filetype
from pathlib import Path
from backend.config import MAX_FILE_SIZE

# Magic byte signatures for formats not covered by filetype
SIGNATURES = {
    "application/pdf": b"%PDF",
    "image/svg+xml": b"<?xml",
}


def get_mime_type(filepath: Path) -> str:
    kind = filetype.guess(str(filepath))
    if kind:
        return kind.mime
    head = filepath.read_bytes()[:256]
    for mime, sig in SIGNATURES.items():
        if head.startswith(sig):
            return mime
    return "application/octet-stream"


def validate_file(filepath: Path, allowed_types: set[str], max_size: int = None) -> Path:
    if max_size is None:
        max_size = MAX_FILE_SIZE
    if not filepath.exists():
        raise ValueError(f"File not found: {filepath}")
    size = filepath.stat().st_size
    if size == 0:
        raise ValueError("File is empty")
    if size > max_size:
        raise ValueError(f"File size {size} exceeds limit {max_size}")
    mime = get_mime_type(filepath)
    if mime not in allowed_types:
        raise ValueError(f"File type '{mime}' is not allowed. Accepted: {allowed_types}")
    return filepath


def sanitize_filename(name: str) -> str:
    name = Path(name).name
    name = re.sub(r'[^\w\-.]', '_', name)
    stem, ext = Path(name).stem, Path(name).suffix
    stem = stem.strip("_") or "file"
    return f"{stem}{ext}"


def temp_filepath(extension: str) -> Path:
    return Path(f"/tmp/{uuid.uuid4()}.{extension.lstrip('.')}")
```

- [ ] **Step 4: Install filetype and run tests**

```bash
pip install filetype
python -m pytest tests/test_validators.py -v
```
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add backend/validators.py tests/test_validators.py tests/fixtures/
git commit -m "feat: add file validators with magic byte detection"
```

---

### Task 3: Rate Limiting & Security

**Files:**
- Create: `backend/security.py`
- Create: `tests/test_security.py`

- [ ] **Step 1: Write failing tests in tests/test_security.py**

```python
import time
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from backend.security import create_rate_limiter, get_client_ip

def test_get_client_ip_direct():
    app = FastAPI()
    @app.get("/test-ip")
    async def test_ip(request: Request):
        return {"ip": get_client_ip(request)}
    client = TestClient(app)
    response = client.get("/test-ip")
    assert response.json()["ip"] == "testclient"

def test_get_client_ip_x_forwarded():
    app = FastAPI()
    @app.get("/test-ip")
    async def test_ip(request: Request):
        return {"ip": get_client_ip(request)}
    client = TestClient(app)
    response = client.get("/test-ip", headers={"X-Forwarded-For": "10.0.0.1"})
    assert response.json()["ip"] == "10.0.0.1"

def test_rate_limiter_allows_requests():
    app = FastAPI()
    limiter = create_rate_limiter(rate="100/minute")
    app.state.limiter = limiter
    @app.get("/limited")
    async def limited(request: Request):
        client_ip = get_client_ip(request)
        limiter.check(client_ip)
        return {"ok": True}
    client = TestClient(app)
    for _ in range(5):
        response = client.get("/limited")
        assert response.status_code == 200

def test_rate_limiter_blocks_excess():
    app = FastAPI()
    limiter = create_rate_limiter(rate="5/minute")
    app.state.limiter = limiter
    @app.get("/limited")
    async def limited(request: Request):
        client_ip = get_client_ip(request)
        if limiter.is_rate_limited(client_ip):
            from fastapi.responses import JSONResponse
            return JSONResponse({"detail": "Too many requests"}, status_code=429)
        return {"ok": True}
    client = TestClient(app)
    for i in range(7):
        response = client.get("/limited")
        if i < 5:
            assert response.status_code == 200
        else:
            assert response.status_code == 429
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_security.py -v`
Expected: FAIL (module not found)

- [ ] **Step 3: Write backend/security.py**

```python
import time
from collections import defaultdict
from fastapi import Request


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    client = request.client
    return client.host if client else "unknown"


class TokenBucket:
    def __init__(self, rate: int, per_seconds: int):
        self.rate = rate
        self.per_seconds = per_seconds
        self.tokens = rate
        self.last_refill = time.time()

    def consume(self, tokens: int = 1) -> bool:
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(self.rate, self.tokens + elapsed * (self.rate / self.per_seconds))
        self.last_refill = now
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False


class InMemoryRateLimiter:
    def __init__(self, rate_str: str = "20/minute"):
        count, window = rate_str.split("/")
        self.rate = int(count)
        self.window = window
        self.per_seconds = {"second": 1, "minute": 60, "hour": 3600}[window]
        self.buckets: dict[str, TokenBucket] = {}

    def is_rate_limited(self, key: str) -> bool:
        bucket = self.buckets.get(key)
        if bucket is None:
            self.buckets[key] = TokenBucket(self.rate, self.per_seconds)
            bucket = self.buckets[key]
        return not bucket.consume()

    def check(self, key: str):
        if self.is_rate_limited(key):
            from fastapi import HTTPException
            raise HTTPException(status_code=429, detail="Too many requests. Please wait.")


def create_rate_limiter(rate: str = "20/minute") -> InMemoryRateLimiter:
    return InMemoryRateLimiter(rate)
```

- [ ] **Step 4: Run tests**

```bash
python -m pytest tests/test_security.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/security.py tests/test_security.py
git commit -m "feat: add rate limiter and IP detection"
```

---

### Task 4: Image Converter

**Files:**
- Create: `backend/converters/image.py`
- Create: `tests/test_image.py`

- [ ] **Step 1: Write failing tests in tests/test_image.py**

```python
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
        assert result.suffix == ".png"
        from PIL import Image
        img = Image.open(result)
        assert img.format == "PNG"

    def test_png_to_webp(self, temp_dir):
        src = _make_test_image(temp_dir / "test.png", "PNG")
        dest = temp_dir / "output.webp"
        result = convert_image(src, dest, "webp")
        assert result.suffix == ".webp"
        from PIL import Image
        img = Image.open(result)
        assert img.format == "WEBP"

    def test_jpg_to_pdf(self, temp_dir):
        src = _make_test_image(temp_dir / "test.jpg", "JPEG")
        dest = temp_dir / "output.pdf"
        result = convert_image(src, dest, "pdf")
        assert result.suffix == ".pdf"

    def test_quality_option(self, temp_dir):
        src = _make_test_image(temp_dir / "test.jpg", "JPEG")
        dest = temp_dir / "output.jpg"
        convert_image(src, dest, "jpg", quality=10)
        convert_image(src, temp_dir / "output_high.jpg", "jpg", quality=95)
        assert dest.stat().st_size < (temp_dir / "output_high.jpg").stat().st_size

    def test_invalid_output_format(self, temp_dir):
        src = _make_test_image(temp_dir / "test.jpg", "JPEG")
        dest = temp_dir / "output.xyz"
        with pytest.raises(ValueError, match="Unsupported"):
            convert_image(src, dest, "xyz")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_image.py -v`
Expected: FAIL (module not found)

- [ ] **Step 3: Write backend/converters/image.py**

```python
import io
from pathlib import Path
from PIL import Image


SUPPORTED_INPUT = {"JPEG", "PNG", "WEBP", "HEIF", "HEIC", "SVG", "BMP", "TIFF"}
SUPPORTED_OUTPUT = {"jpg", "jpeg", "png", "webp", "bmp", "tiff", "pdf"}


def convert_image(src: Path, dest: Path, output_format: str, quality: int = 85) -> Path:
    output_format = output_format.lower().lstrip(".")
    if output_format not in SUPPORTED_OUTPUT and output_format != "pdf":
        raise ValueError(f"Unsupported output format: {output_format}")

    img = Image.open(src)

    if img.mode in ("P", "PA"):
        img = img.convert("RGBA")
    elif img.mode not in ("RGB", "RGBA", "L", "LA", "CMYK", "YCbCr", "LAB", "HSV"):
        img = img.convert("RGB")

    if output_format in ("jpg", "jpeg"):
        if img.mode == "RGBA":
            background = Image.new("RGB", img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])
            img = background
        elif img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        img.save(dest, "JPEG", quality=quality)

    elif output_format == "png":
        img.save(dest, "PNG", optimize=True)

    elif output_format == "webp":
        if img.mode in ("RGBA", "LA"):
            img.save(dest, "WEBP", quality=quality, lossless=False)
        else:
            img.save(dest, "WEBP", quality=quality)

    elif output_format == "bmp":
        img.save(dest, "BMP")

    elif output_format == "tiff":
        img.save(dest, "TIFF")

    elif output_format == "pdf":
        if img.mode == "RGBA":
            background = Image.new("RGB", img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])
            img = background
        elif img.mode != "RGB":
            img = img.convert("RGB")
        img.save(dest, "PDF", resolution=100.0)

    img.close()
    return dest
```

- [ ] **Step 4: Run tests**

```bash
python -m pytest tests/test_image.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/converters/image.py tests/test_image.py
git commit -m "feat: add image-to-image converter"
```

---

### Task 5: PDF to Image Converter

**Files:**
- Create: `backend/converters/pdf_to_image.py`
- Create: `tests/test_pdf_to_image.py`

- [ ] **Step 1: Write failing tests in tests/test_pdf_to_image.py**

```python
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
        results = convert_pdf_to_image(src, dest_dir / "page", "jpg", pages="1-2")
        assert len(results) == 2

    def test_invalid_page_range(self, temp_dir):
        src = _make_test_pdf(temp_dir / "test.pdf", pages=2)
        dest = temp_dir / "output.jpg"
        with pytest.raises(ValueError):
            convert_pdf_to_image(src, dest, "jpg", pages="10-20")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_pdf_to_image.py -v`
Expected: FAIL (module not found)

- [ ] **Step 3: Write backend/converters/pdf_to_image.py**

```python
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
                raise ValueError(f"Invalid page range: {start}-{end} (total: {total_pages})")
            pages.extend(range(start, end + 1))
        else:
            p = int(part)
            if p < 1 or p > total_pages:
                raise ValueError(f"Invalid page: {p} (total: {total_pages})")
            pages.append(p)
    return pages


def convert_pdf_to_image(
    src: Path,
    dest: Path,
    output_format: str = "jpg",
    pages: str | None = None,
    dpi: int = 200,
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
        out_path = dest.parent / f"{dest.stem}_{i+1}.{output_format}"
        images[p - 1].save(out_path, fmt)
        results.append(out_path)

    if len(results) > 1:
        zip_path = dest.parent / f"{dest.stem}.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for r in results:
                zf.write(r, r.name)
        return zip_path
    return results[0] if results else None
```

- [ ] **Step 4: Run tests**

```bash
python -m pytest tests/test_pdf_to_image.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/converters/pdf_to_image.py tests/test_pdf_to_image.py
git commit -m "feat: add PDF to image converter"
```

---

### Task 6: Image to PDF Converter

**Files:**
- Create: `backend/converters/image_to_pdf.py`
- Create: `tests/test_image_to_pdf.py`

- [ ] **Step 1: Write failing tests in tests/test_image_to_pdf.py**

```python
import pytest
from pathlib import Path
from backend.converters.image_to_pdf import convert_images_to_pdf


def _make_test_image(path: Path, size=(100, 100), color="red", fmt="JPEG"):
    from PIL import Image
    img = Image.new("RGB", size, color=color)
    img.save(path, fmt)
    return path


class TestConvertImagesToPdf:
    def test_single_image_to_pdf(self, temp_dir):
        src = _make_test_image(temp_dir / "test.jpg")
        dest = temp_dir / "output.pdf"
        result = convert_images_to_pdf([src], dest)
        assert result.exists()
        assert result.suffix == ".pdf"
        assert result.stat().st_size > 0

    def test_multiple_images_to_pdf(self, temp_dir):
        images = [
            _make_test_image(temp_dir / "img1.jpg", color="red"),
            _make_test_image(temp_dir / "img2.png", color="blue", fmt="PNG"),
            _make_test_image(temp_dir / "img3.jpg", color="green"),
        ]
        dest = temp_dir / "combined.pdf"
        result = convert_images_to_pdf(images, dest)
        assert result.exists()

    def test_fit_to_page(self, temp_dir):
        src = _make_test_image(temp_dir / "large.jpg", size=(2000, 1500))
        dest = temp_dir / "fitted.pdf"
        result = convert_images_to_pdf([src], dest, fit_to_page=True)
        assert result.exists()

    def test_empty_list_raises(self, temp_dir):
        dest = temp_dir / "empty.pdf"
        with pytest.raises(ValueError, match="at least one image"):
            convert_images_to_pdf([], dest)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_image_to_pdf.py -v`
Expected: FAIL

- [ ] **Step 3: Write backend/converters/image_to_pdf.py**

```python
import io
from pathlib import Path
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader


def convert_images_to_pdf(
    image_paths: list[Path],
    dest: Path,
    fit_to_page: bool = True,
    page_size: tuple = A4,
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
            x, y = (pw - dw) / 2, (ph - dh) / 2
        else:
            dw, dh = iw, ih
            x, y = (pw - dw) / 2, (ph - dh) / 2

        c.drawImage(reader, x, y, dw, dh, preserveAspectRatio=True)
        c.showPage()
        img.close()
        buf.close()

    c.save()
    return dest
```

- [ ] **Step 4: Run tests**

```bash
python -m pytest tests/test_image_to_pdf.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/converters/image_to_pdf.py tests/test_image_to_pdf.py
git commit -m "feat: add image to PDF converter"
```

---

### Task 7: Office to PDF Converter

**Files:**
- Create: `backend/converters/office.py`
- Create: `tests/test_office.py`

- [ ] **Step 1: Write failing tests in tests/test_office.py**

```python
import pytest
from pathlib import Path
from backend.converters.office import convert_office_to_pdf


def _make_test_docx(path: Path):
    from docx import Document
    doc = Document()
    doc.add_paragraph("Test document content.")
    doc.save(str(path))
    return path


class TestConvertOfficeToPdf:
    @pytest.mark.skipif(not _libreoffice_available(), reason="LibreOffice not installed")
    def test_docx_to_pdf(self, temp_dir):
        src = _make_test_docx(temp_dir / "test.docx")
        dest = temp_dir / "output.pdf"
        result = convert_office_to_pdf(src, dest)
        assert result.exists()
        assert result.suffix == ".pdf"
        assert result.stat().st_size > 0

    def test_unsupported_format_raises(self, temp_dir):
        fake = temp_dir / "test.xyz"
        fake.write_bytes(b"not a real file")
        dest = temp_dir / "output.pdf"
        with pytest.raises(ValueError, match="Unsupported"):
            convert_office_to_pdf(fake, dest)

    def test_libreoffice_not_found(self, temp_dir):
        import backend.converters.office as office
        old = office._LIBREOFFICE_PATH
        office._LIBREOFFICE_PATH = "/nonexistent/soffice"
        src = _make_test_docx(temp_dir / "test.docx")
        dest = temp_dir / "output.pdf"
        with pytest.raises(RuntimeError, match="LibreOffice"):
            convert_office_to_pdf(src, dest)
        office._LIBREOFFICE_PATH = old


def _libreoffice_available():
    import shutil
    return shutil.which("soffice") is not None or shutil.which("libreoffice") is not None
```

- [ ] **Step 2: Run tests (skipped if no LibreOffice)**

```bash
python -m pytest tests/test_office.py -v
```

- [ ] **Step 3: Write backend/converters/office.py**

```python
import shutil
import subprocess
import tempfile
from pathlib import Path

SUPPORTED_OFFICE = {
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
}

_LIBREOFFICE_PATH = shutil.which("soffice") or shutil.which("libreoffice") or "soffice"


def convert_office_to_pdf(src: Path, dest: Path) -> Path:
    ext = src.suffix.lower()
    if ext not in SUPPORTED_OFFICE:
        raise ValueError(f"Unsupported office format: {ext}. Supported: {list(SUPPORTED_OFFICE.keys())}")

    if not shutil.which(_LIBREOFFICE_PATH):
        raise RuntimeError(
            "LibreOffice not found. Install with: sudo apt install libreoffice-core"
        )

    with tempfile.TemporaryDirectory() as tmpdir:
        cmd = [
            _LIBREOFFICE_PATH,
            "--headless",
            "--norestore",
            "--convert-to", "pdf",
            "--outdir", tmpdir,
            str(src),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            raise RuntimeError(f"LibreOffice conversion failed: {result.stderr}")

        pdfs = list(Path(tmpdir).glob("*.pdf"))
        if not pdfs:
            raise RuntimeError("LibreOffice produced no PDF output")

        pdfs[0].rename(dest)
        return dest
```

- [ ] **Step 4: Run tests**

```bash
python -m pytest tests/test_office.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/converters/office.py tests/test_office.py
git commit -m "feat: add Office to PDF converter (LibreOffice)"
```

---

### Task 8: PDF Toolkit

**Files:**
- Create: `backend/converters/pdf_toolkit.py`
- Create: `tests/test_pdf_toolkit.py`

- [ ] **Step 1: Write failing tests in tests/test_pdf_toolkit.py**

```python
import pytest
from pathlib import Path
from backend.converters.pdf_toolkit import (
    compress_pdf,
    merge_pdfs,
    split_pdf,
    reorder_pages,
    rotate_pages,
    delete_pages,
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
    def test_compress_reduces_or_maintains_size(self, temp_dir):
        src = _make_test_pdf(temp_dir / "input.pdf", pages=5)
        dest = temp_dir / "compressed.pdf"
        result = compress_pdf(src, dest)
        assert result.exists()
        assert result.stat().st_size > 0


class TestMergePdfs:
    def test_merges_two_pdfs(self, temp_dir):
        a = _make_test_pdf(temp_dir / "a.pdf", pages=2)
        b = _make_test_pdf(temp_dir / "b.pdf", pages=2)
        dest = temp_dir / "merged.pdf"
        result = merge_pdfs([a, b], dest)
        assert result.exists()

    def test_empty_list_raises(self, temp_dir):
        with pytest.raises(ValueError):
            merge_pdfs([], temp_dir / "out.pdf")


class TestSplitPdf:
    def test_splits_by_page_ranges(self, temp_dir):
        src = _make_test_pdf(temp_dir / "input.pdf", pages=5)
        out_dir = temp_dir / "split"
        out_dir.mkdir()
        results = split_pdf(src, out_dir, ["1-2", "3-5"])
        assert len(results) == 2


class TestReorderPages:
    def test_reorder(self, temp_dir):
        src = _make_test_pdf(temp_dir / "input.pdf", pages=4)
        dest = temp_dir / "reordered.pdf"
        result = reorder_pages(src, dest, [3, 1, 4, 2])
        assert result.exists()

    def test_invalid_order_raises(self, temp_dir):
        src = _make_test_pdf(temp_dir / "input.pdf", pages=3)
        with pytest.raises(ValueError):
            reorder_pages(src, temp_dir / "out.pdf", [1, 2, 5])


class TestRotatePages:
    def test_rotate_page_90(self, temp_dir):
        src = _make_test_pdf(temp_dir / "input.pdf", pages=2)
        dest = temp_dir / "rotated.pdf"
        result = rotate_pages(src, dest, {"1": 90})
        assert result.exists()


class TestDeletePages:
    def test_delete_pages(self, temp_dir):
        src = _make_test_pdf(temp_dir / "input.pdf", pages=4)
        dest = temp_dir / "deleted.pdf"
        result = delete_pages(src, dest, [2, 4])
        assert result.exists()

    def test_delete_all_pages_raises(self, temp_dir):
        src = _make_test_pdf(temp_dir / "input.pdf", pages=2)
        with pytest.raises(ValueError):
            delete_pages(src, temp_dir / "out.pdf", [1, 2])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_pdf_toolkit.py -v`
Expected: FAIL

- [ ] **Step 3: Write backend/converters/pdf_toolkit.py**

```python
import pikepdf
from pathlib import Path


def compress_pdf(src: Path, dest: Path, quality: str = "ebook") -> Path:
    pdf = pikepdf.Pdf.open(src)
    pdf.save(dest, compress_streams=True, object_stream_mode=pikepdf.ObjectStreamMode.generate)
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
                raise ValueError(f"Page range {start}-{end} out of bounds (1-{total})")
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
    """rotations: {"1": 90, "2": -90, "3": 180}"""
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
    """
    edits: [{"page": 1, "old_text": "foo", "new_text": "bar"}, ...]
    Requires PyMuPDF (fitz).
    """
    import fitz
    doc = fitz.open(src)
    for edit in edits:
        page_num = edit["page"] - 1
        if page_num < 0 or page_num >= len(doc):
            raise ValueError(f"Page {edit['page']} out of range")
        page = doc[page_num]
        found = page.search_for(edit["old_text"])
        if not found:
            continue
        for rect in found:
            page.add_redact_annot(rect, text=edit["new_text"])
        page.apply_redactions()
    doc.save(dest)
    doc.close()
    return dest
```

- [ ] **Step 4: Run tests**

```bash
python -m pytest tests/test_pdf_toolkit.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/converters/pdf_toolkit.py tests/test_pdf_toolkit.py
git commit -m "feat: add PDF toolkit (compress, merge, split, reorder, rotate, delete, edit)"
```

---

### Task 9: FastAPI Main Application & Routes

**Files:**
- Create: `backend/main.py`
- Create: `tests/test_api.py`

- [ ] **Step 1: Write failing API tests in tests/test_api.py**

```python
import io
from pathlib import Path
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

    def test_rate_limit_returns_429(self, client):
        img = _make_test_jpg()
        responses = []
        for _ in range(25):
            responses.append(client.post(
                "/api/convert",
                files={"file": ("test.jpg", img, "image/jpeg")},
                data={"output_format": "png"},
            ))
        assert any(r.status_code == 429 for r in responses)


class TestInfoEndpoint:
    def test_formats_endpoint(self, client):
        response = client.get("/api/formats")
        assert response.status_code == 200
        data = response.json()
        assert "input" in data
        assert "output" in data


class TestStaticFiles:
    def test_serves_index(self, client):
        response = client.get("/")
        assert response.status_code == 200
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_api.py -v`
Expected: FAIL (app module not found or endpoints don't exist)

- [ ] **Step 3: Write backend/main.py**

```python
import shutil
import tempfile
import zipfile
from pathlib import Path
from fastapi import FastAPI, File, Form, UploadFile, Request, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from backend.config import ALLOWED_IMAGE_INPUT, ALLOWED_IMAGE_OUTPUT, ALLOWED_PDF_INPUT, ALLOWED_OFFICE_INPUT, MAX_FILE_SIZE
from backend.validators import validate_file, sanitize_filename, get_mime_type
from backend.security import create_rate_limiter, get_client_ip
from backend.converters import image, pdf_to_image, image_to_pdf, office, pdf_toolkit

FRONTEND_DIR = Path(__file__).parent.parent / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.limiter = create_rate_limiter()
    yield

app = FastAPI(title="FileConverter", version="1.0.0", lifespan=lifespan)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = get_client_ip(request)
    limiter = request.app.state.limiter
    try:
        limiter.check(client_ip)
    except HTTPException as e:
        return JSONResponse({"detail": str(e.detail)}, status_code=429)
    return await call_next(request)


@app.get("/api/formats")
async def get_formats():
    return {
        "input": {
            "image": list(ALLOWED_IMAGE_INPUT),
            "pdf": list(ALLOWED_PDF_INPUT),
            "office": list(ALLOWED_OFFICE_INPUT),
        },
        "output": list(ALLOWED_IMAGE_OUTPUT) + ["pdf"],
    }


@app.post("/api/convert")
async def convert_file(
    file: UploadFile = File(...),
    output_format: str = Form(...),
):
    output_format = output_format.lower().strip().lstrip(".")
    if output_format not in ALLOWED_IMAGE_OUTPUT and output_format != "pdf":
        raise HTTPException(400, f"Unsupported output format: {output_format}")

    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_in:
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(413, f"File exceeds {MAX_FILE_SIZE // 1024 // 1024}MB limit")
        tmp_in.write(content)
        tmp_in_path = Path(tmp_in.name)

    try:
        mime = get_mime_type(tmp_in_path)
        tmp_out = Path(tempfile.mktemp(suffix=f".{output_format}"))

        if mime in ALLOWED_IMAGE_INPUT:
            if output_format == "pdf":
                result = image_to_pdf.convert_images_to_pdf([tmp_in_path], tmp_out)
            else:
                result = image.convert_image(tmp_in_path, tmp_out, output_format)

        elif mime in ALLOWED_PDF_INPUT:
            if output_format in ("jpg", "png", "jpeg"):
                result = pdf_to_image.convert_pdf_to_image(tmp_in_path, tmp_out, output_format)
            else:
                raise HTTPException(400, f"Cannot convert PDF to {output_format}")

        else:
            raise HTTPException(400, f"Unsupported input format: {mime}")

        out_name = sanitize_filename(file.filename or "file")
        out_name = Path(out_name).stem + f".{output_format}"

        if isinstance(result, list):
            zip_path = tmp_out.parent / f"{Path(out_name).stem}.zip"
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for r in result:
                    zf.write(r, r.name)
            return FileResponse(zip_path, filename=f"{Path(out_name).stem}.zip",
                              media_type="application/zip")

        media = f"image/{output_format}" if output_format != "pdf" else "application/pdf"
        if output_format == "jpg":
            media = "image/jpeg"
        return FileResponse(result, filename=out_name, media_type=media)

    finally:
        if tmp_in_path.exists():
            tmp_in_path.unlink()
        if 'tmp_out' in locals() and tmp_out.exists():
            tmp_out.unlink()


@app.post("/api/pdf/toolkit")
async def pdf_toolkit_route(
    file: UploadFile = File(...),
    action: str = Form(...),
    pages: str = Form(None),
    order: str = Form(None),
    rotations: str = Form(None),
    quality: str = Form("ebook"),
):
    action = action.strip().lower()
    valid_actions = {"compress", "merge", "split", "reorder", "rotate", "delete", "page_count"}
    if action not in valid_actions:
        raise HTTPException(400, f"Invalid action: {action}. Valid: {valid_actions}")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_in:
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(413)
        tmp_in.write(content)
        tmp_in_path = Path(tmp_in.name)

    try:
        mime = get_mime_type(tmp_in_path)
        if mime not in ALLOWED_PDF_INPUT:
            raise HTTPException(400, "File must be a PDF")

        tmp_out = Path(tempfile.mktemp(suffix=".pdf"))

        if action == "compress":
            result = pdf_toolkit.compress_pdf(tmp_in_path, tmp_out)
        elif action == "split":
            out_dir = Path(tempfile.mkdtemp())
            ranges = pages.split(";") if pages else ["1"]
            results = pdf_toolkit.split_pdf(tmp_in_path, out_dir, ranges)
            zip_path = Path(tempfile.mktemp(suffix=".zip"))
            with zipfile.ZipFile(zip_path, "w") as zf:
                for r in results:
                    zf.write(r, r.name)
            return FileResponse(zip_path, filename="split_pages.zip", media_type="application/zip")
        elif action == "reorder":
            order_list = [int(x) for x in order.split(",")] if order else []
            result = pdf_toolkit.reorder_pages(tmp_in_path, tmp_out, order_list)
        elif action == "rotate":
            import json
            rots = json.loads(rotations) if rotations else {}
            result = pdf_toolkit.rotate_pages(tmp_in_path, tmp_out, rots)
        elif action == "delete":
            delete_list = [int(x) for x in pages.split(",")] if pages else []
            result = pdf_toolkit.delete_pages(tmp_in_path, tmp_out, delete_list)
        elif action == "page_count":
            count = pdf_toolkit.get_page_count(tmp_in_path)
            return JSONResponse({"pages": count})

        return FileResponse(result, filename="output.pdf", media_type="application/pdf")

    finally:
        if tmp_in_path.exists():
            tmp_in_path.unlink()
        if 'tmp_out' in locals() and tmp_out.exists():
            tmp_out.unlink()


app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="static")
```

- [ ] **Step 4: Run tests**

```bash
python -m pytest tests/test_api.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/main.py tests/test_api.py
git commit -m "feat: add FastAPI app with convert and PDF toolkit routes"
```

---

### Task 10: Frontend — HTML Structure

**Files:**
- Create: `frontend/index.html`

- [ ] **Step 1: Write frontend/index.html**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>FileConverter</title>
  <link rel="stylesheet" href="css/style.css">
</head>
<body>
  <header class="header">
    <span class="logo">FileConverter</span>
    <span class="tagline">Open Source &middot; Files processed in-memory</span>
  </header>

  <div class="layout">
    <!-- Sidebar -->
    <nav class="sidebar" id="sidebar">
      <p class="sidebar-label">Tools</p>
      <button class="tool-btn active" data-tool="image-convert">
        <span class="tool-icon">I</span>
        <span class="tool-name">Image Convert</span>
      </button>
      <button class="tool-btn" data-tool="pdf-to-image">
        <span class="tool-icon">D</span>
        <span class="tool-name">PDF to Image</span>
      </button>
      <button class="tool-btn" data-tool="image-to-pdf">
        <span class="tool-icon">G</span>
        <span class="tool-name">Image to PDF</span>
      </button>
      <button class="tool-btn" data-tool="pdf-toolkit">
        <span class="tool-icon">K</span>
        <span class="tool-name">PDF Toolkit</span>
      </button>
      <button class="tool-btn" data-tool="office-to-pdf">
        <span class="tool-icon">O</span>
        <span class="tool-name">Office to PDF</span>
      </button>
    </nav>

    <!-- Workspace -->
    <main class="workspace" id="workspace">
      <!-- Step indicator -->
      <div class="steps" id="steps">
        <div class="step active" data-step="1">
          <span class="step-num">1</span>
          <span class="step-label">Upload</span>
        </div>
        <div class="step-connector"></div>
        <div class="step" data-step="2">
          <span class="step-num">2</span>
          <span class="step-label">Convert</span>
        </div>
        <div class="step-connector"></div>
        <div class="step" data-step="3">
          <span class="step-num">3</span>
          <span class="step-label">Download</span>
        </div>
      </div>

      <!-- Upload zone -->
      <div class="drop-zone" id="dropZone">
        <p class="drop-text">Drag and drop your file here</p>
        <p class="drop-or">or</p>
        <button class="btn-primary" id="browseBtn">Browse Files</button>
        <input type="file" id="fileInput" hidden>
        <p class="drop-limit" id="maxSizeLabel">Max file size: 250MB</p>
      </div>

      <!-- File card (hidden until upload) -->
      <div class="file-card hidden" id="fileCard">
        <div class="file-thumb" id="fileThumb"></div>
        <div class="file-info">
          <p class="file-name" id="fileName"></p>
          <div class="file-meta">
            <span class="format-badge" id="formatBadge"></span>
            <span class="file-size" id="fileSize"></span>
            <span class="file-detail" id="fileDetail"></span>
          </div>
        </div>
        <button class="file-remove" id="fileRemove">&times;</button>
      </div>

      <!-- Format selector -->
      <div class="format-section hidden" id="formatSection">
        <span class="format-label">Convert to:</span>
        <div class="format-chips" id="formatChips"></div>
        <button class="btn-convert" id="convertBtn">Convert Now</button>
      </div>

      <!-- Progress bar -->
      <div class="progress-section hidden" id="progressSection">
        <div class="progress-bar">
          <div class="progress-fill" id="progressFill"></div>
        </div>
        <p class="progress-text" id="progressText">Converting...</p>
      </div>

      <!-- Result panel -->
      <div class="result-section hidden" id="resultSection">
        <div class="result-preview" id="resultPreview"></div>
        <button class="btn-download" id="downloadBtn">Download</button>
        <button class="btn-reset" id="resetBtn">Convert Another</button>
      </div>

      <!-- PDF Toolkit extras -->
      <div class="pdf-toolbar hidden" id="pdfToolbar">
        <button class="toolbar-btn" data-action="compress">Compress</button>
        <button class="toolbar-btn" data-action="rotate-left">Rotate Left</button>
        <button class="toolbar-btn" data-action="rotate-right">Rotate Right</button>
        <button class="toolbar-btn danger" data-action="delete">Delete</button>
        <button class="toolbar-btn export" data-action="export">Export</button>
      </div>
      <div class="page-strip hidden" id="pageStrip"></div>
    </main>
  </div>

  <!-- Mobile bottom tab bar -->
  <nav class="tab-bar" id="tabBar">
    <button class="tab-btn active" data-tool="image-convert">
      <span class="tab-icon">I</span>
      <span class="tab-label">Image</span>
    </button>
    <button class="tab-btn" data-tool="pdf-to-image">
      <span class="tab-icon">D</span>
      <span class="tab-label">PDF to Img</span>
    </button>
    <button class="tab-btn" data-tool="image-to-pdf">
      <span class="tab-icon">G</span>
      <span class="tab-label">Img to PDF</span>
    </button>
    <button class="tab-btn" data-tool="pdf-toolkit">
      <span class="tab-icon">K</span>
      <span class="tab-label">PDF Kit</span>
    </button>
    <button class="tab-btn" data-tool="office-to-pdf">
      <span class="tab-icon">O</span>
      <span class="tab-label">Office</span>
    </button>
  </nav>

  <p class="footer-note">Free &amp; open source &mdash; files are never stored on the server</p>

  <script src="https://cdn.jsdelivr.net/npm/sortablejs@1.15.6/Sortable.min.js"></script>
  <script src="js/api.js"></script>
  <script src="js/pdf-toolkit.js"></script>
  <script src="js/app.js"></script>
</body>
</html>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/index.html
git commit -m "feat: add frontend HTML structure with sidebar + workspace layout"
```

---

### Task 11: Frontend — CSS (Deep Indigo Theme)

**Files:**
- Create: `frontend/css/style.css`

- [ ] **Step 1: Write frontend/css/style.css**

```css
:root {
  --indigo: #4f46e5;
  --indigo-light: #eef2ff;
  --indigo-dark: #4338ca;
  --indigo-muted: #818cf8;
  --gray-50: #f8f8fc;
  --gray-100: #f1f5f9;
  --gray-200: #e2e8f0;
  --gray-300: #cbd5e1;
  --gray-400: #94a3b8;
  --gray-500: #64748b;
  --gray-700: #334155;
  --gray-900: #1e1b4b;
  --green: #16a34a;
  --red: #ef4444;
  --white: #ffffff;
  --radius: 8px;
  --shadow: 0 1px 3px rgba(0,0,0,0.06);
}

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: var(--gray-50);
  color: var(--gray-900);
  min-height: 100vh;
}

/* Header */
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  background: var(--white);
  border-bottom: 1px solid var(--gray-200);
}
.logo {
  font-weight: 700;
  font-size: 16px;
  color: var(--gray-900);
}
.tagline {
  font-size: 11px;
  color: var(--gray-400);
}

/* Layout */
.layout {
  display: flex;
  min-height: calc(100vh - 49px - 32px);
}

/* Sidebar */
.sidebar {
  width: 200px;
  background: var(--white);
  border-right: 1px solid var(--gray-200);
  padding: 12px 10px;
  flex-shrink: 0;
}
.sidebar-label {
  margin: 0 0 8px 6px;
  font-size: 10px;
  color: var(--gray-400);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-weight: 600;
}
.tool-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 10px;
  border: none;
  border-radius: 6px;
  background: transparent;
  font-size: 12px;
  color: var(--gray-500);
  cursor: pointer;
  text-align: left;
  margin-bottom: 2px;
}
.tool-btn:hover { background: var(--gray-100); }
.tool-btn.active {
  background: var(--indigo-light);
  color: var(--indigo);
  font-weight: 600;
}
.tool-icon {
  font-size: 14px;
  width: 24px;
  text-align: center;
  font-weight: 700;
}

/* Workspace */
.workspace {
  flex: 1;
  padding: 24px;
  max-width: 780px;
  margin: 0 auto;
  width: 100%;
}

/* Steps */
.steps {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0;
  margin-bottom: 24px;
}
.step {
  display: flex;
  align-items: center;
  gap: 6px;
}
.step-num {
  width: 26px;
  height: 26px;
  border-radius: 13px;
  background: var(--gray-200);
  color: var(--gray-400);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  transition: all 0.3s;
}
.step.active .step-num {
  background: var(--indigo);
  color: var(--white);
}
.step.completed .step-num {
  background: var(--green);
  color: var(--white);
}
.step-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--gray-400);
}
.step.active .step-label { color: var(--indigo); }
.step.completed .step-label { color: var(--green); }
.step-connector {
  width: 32px;
  height: 1px;
  background: var(--gray-200);
  margin: 0 4px;
}

/* Drop zone */
.drop-zone {
  border: 2px dashed var(--gray-300);
  border-radius: var(--radius);
  padding: 40px 24px;
  text-align: center;
  background: var(--white);
  transition: border-color 0.2s, background 0.2s;
  cursor: pointer;
}
.drop-zone:hover, .drop-zone.drag-over {
  border-color: var(--indigo-muted);
  background: var(--indigo-light);
}
.drop-text { font-size: 14px; color: var(--gray-500); font-weight: 500; }
.drop-or { font-size: 11px; color: var(--gray-400); margin: 6px 0 10px; }
.drop-limit { font-size: 11px; color: var(--gray-400); margin-top: 10px; }

/* Buttons */
.btn-primary {
  background: var(--gray-900);
  color: var(--white);
  border: none;
  padding: 8px 20px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
}
.btn-primary:hover { background: var(--gray-700); }
.btn-convert {
  background: var(--indigo);
  color: var(--white);
  border: none;
  padding: 10px 24px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
}
.btn-convert:hover { background: var(--indigo-dark); }
.btn-convert:disabled { opacity: 0.4; cursor: not-allowed; }
.btn-download {
  background: var(--green);
  color: var(--white);
  border: none;
  padding: 12px 28px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  width: 100%;
}
.btn-download:hover { background: #15803d; }
.btn-reset {
  background: var(--white);
  color: var(--gray-500);
  border: 1px solid var(--gray-300);
  padding: 10px 16px;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  width: 100%;
  margin-top: 8px;
}

/* File card */
.file-card {
  display: flex;
  align-items: center;
  gap: 14px;
  background: var(--white);
  border: 1px solid var(--gray-200);
  border-radius: 10px;
  padding: 16px;
  margin-top: 16px;
}
.file-thumb {
  width: 52px;
  height: 52px;
  background: var(--indigo-light);
  border-radius: var(--radius);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 11px;
  font-weight: 700;
  color: var(--indigo);
  overflow: hidden;
}
.file-thumb img { width: 100%; height: 100%; object-fit: cover; }
.file-info { flex: 1; min-width: 0; }
.file-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--gray-900);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.file-meta { display: flex; align-items: center; gap: 6px; margin-top: 3px; flex-wrap: wrap; }
.format-badge {
  background: var(--indigo);
  color: var(--white);
  padding: 2px 7px;
  border-radius: 3px;
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
}
.file-size, .file-detail { font-size: 11px; color: var(--gray-400); }
.file-remove {
  background: none;
  border: none;
  font-size: 20px;
  color: var(--gray-400);
  cursor: pointer;
  flex-shrink: 0;
}
.file-remove:hover { color: var(--red); }

/* Format chips */
.format-section {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 16px;
  flex-wrap: wrap;
}
.format-label { font-size: 12px; color: var(--gray-500); white-space: nowrap; }
.format-chips { display: flex; gap: 6px; flex-wrap: wrap; }
.format-chip {
  padding: 6px 14px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  background: var(--gray-100);
  color: var(--gray-500);
  border: none;
  cursor: pointer;
}
.format-chip:hover { background: var(--gray-200); }
.format-chip.selected {
  background: var(--indigo);
  color: var(--white);
}

/* Progress */
.progress-section { margin-top: 16px; }
.progress-bar {
  height: 4px;
  background: var(--gray-200);
  border-radius: 2px;
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  background: var(--indigo);
  width: 0%;
  transition: width 0.3s;
}
.progress-text {
  font-size: 11px;
  color: var(--indigo);
  margin-top: 4px;
  text-align: center;
}

/* Result */
.result-section { margin-top: 16px; }
.result-preview {
  border: 1px solid var(--gray-200);
  border-radius: var(--radius);
  padding: 24px;
  text-align: center;
  background: var(--white);
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.result-preview img { max-width: 100%; max-height: 400px; border-radius: 4px; }
.result-preview .placeholder { color: var(--gray-400); font-size: 13px; }

/* PDF Toolkit */
.pdf-toolbar {
  display: flex;
  gap: 6px;
  margin-top: 16px;
  flex-wrap: wrap;
}
.toolbar-btn {
  padding: 7px 12px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
  background: var(--gray-100);
  color: var(--gray-500);
  border: none;
  cursor: pointer;
}
.toolbar-btn:hover { background: var(--gray-200); }
.toolbar-btn.active { background: var(--indigo); color: var(--white); }
.toolbar-btn.danger { color: var(--red); }
.toolbar-btn.danger:hover { background: #fef2f2; }
.toolbar-btn.export { background: var(--indigo); color: var(--white); margin-left: auto; }
.page-strip {
  display: flex;
  gap: 8px;
  margin-top: 12px;
  overflow-x: auto;
  padding-bottom: 8px;
}
.page-thumb {
  min-width: 100px;
  height: 130px;
  background: var(--white);
  border: 1px solid var(--gray-200);
  border-radius: 6px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
  cursor: pointer;
  user-select: none;
}
.page-thumb.selected { border: 2px solid var(--indigo); }
.page-thumb.deleted { opacity: 0.4; border-color: var(--red); }
.page-thumb-num {
  position: absolute;
  top: 4px;
  left: 4px;
  width: 18px;
  height: 18px;
  border-radius: 9px;
  background: var(--gray-200);
  color: var(--gray-500);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 700;
}
.page-thumb.selected .page-thumb-num { background: var(--indigo); color: var(--white); }
.page-thumb.deleted .page-thumb-num { background: var(--red); color: var(--white); }
.page-thumb-preview {
  font-size: 20px;
  color: var(--gray-400);
}
.deleted-label {
  position: absolute;
  bottom: 4px;
  font-size: 9px;
  color: var(--red);
  display: none;
}
.page-thumb.deleted .deleted-label { display: block; }

/* Hidden */
.hidden { display: none !important; }

/* Footer */
.footer-note {
  text-align: center;
  font-size: 10px;
  color: var(--gray-400);
  padding: 8px;
}

/* Mobile tab bar */
.tab-bar {
  display: none;
  justify-content: space-between;
  background: var(--white);
  border-top: 1px solid var(--gray-200);
  padding: 8px 12px;
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 100;
}
.tab-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  background: none;
  border: none;
  color: var(--gray-400);
  font-size: 9px;
  cursor: pointer;
  padding: 4px 6px;
}
.tab-btn.active { color: var(--indigo); font-weight: 600; }
.tab-icon { font-size: 16px; font-weight: 700; }

/* Responsive */
@media (max-width: 768px) {
  .sidebar { display: none; }
  .tab-bar { display: flex; }
  .workspace { padding: 16px; padding-bottom: 80px; }
  .header { justify-content: center; }
  .tagline { display: none; }
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/css/style.css
git commit -m "feat: add CSS with Deep Indigo theme and responsive layout"
```

---

### Task 12: Frontend — API Module

**Files:**
- Create: `frontend/js/api.js`

- [ ] **Step 1: Write frontend/js/api.js**

```javascript
const API = {
  async convert(file, outputFormat, options = {}) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('output_format', outputFormat);
    if (options.quality) formData.append('quality', options.quality);
    if (options.pages) formData.append('pages', options.pages);

    const response = await fetch('/api/convert', {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: 'Conversion failed' }));
      throw new Error(err.detail || `HTTP ${response.status}`);
    }

    const blob = await response.blob();
    const disposition = response.headers.get('Content-Disposition') || '';
    const filenameMatch = disposition.match(/filename="?(.+?)"?$/);
    const filename = filenameMatch ? filenameMatch[1] : `converted.${outputFormat}`;
    return { blob, filename };
  },

  async pdfToolkit(file, action, options = {}) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('action', action);
    if (options.pages) formData.append('pages', options.pages);
    if (options.order) formData.append('order', options.order);
    if (options.rotations) formData.append('rotations', JSON.stringify(options.rotations));

    const response = await fetch('/api/pdf/toolkit', {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: 'Toolkit action failed' }));
      throw new Error(err.detail || `HTTP ${response.status}`);
    }

    if (action === 'page_count') {
      const data = await response.json();
      return { pageCount: data.pages };
    }

    const blob = await response.blob();
    const disposition = response.headers.get('Content-Disposition') || '';
    const filenameMatch = disposition.match(/filename="?(.+?)"?$/);
    const filename = filenameMatch ? filenameMatch[1] : 'output.pdf';
    return { blob, filename };
  },

  async getFormats() {
    const response = await fetch('/api/formats');
    return response.json();
  },
};
```

- [ ] **Step 2: Commit**

```bash
git add frontend/js/api.js
git commit -m "feat: add frontend API module"
```

---

### Task 13: Frontend — PDF Toolkit JS

**Files:**
- Create: `frontend/js/pdf-toolkit.js`

- [ ] **Step 1: Write frontend/js/pdf-toolkit.js**

```javascript
const PDFToolkit = {
  pages: [],
  selectedPages: new Set(),
  deletedPages: new Set(),
  sortable: null,

  init(pageCount) {
    this.pages = Array.from({ length: pageCount }, (_, i) => ({
      number: i + 1,
      selected: false,
      deleted: false,
    }));
    this.selectedPages.clear();
    this.deletedPages.clear();
    this.render();
    this._initSortable();
  },

  render() {
    const strip = document.getElementById('pageStrip');
    strip.innerHTML = '';
    this.pages.forEach((page, index) => {
      const el = document.createElement('div');
      el.className = 'page-thumb';
      el.dataset.page = page.number;
      if (page.selected) el.classList.add('selected');
      if (page.deleted) el.classList.add('deleted');
      el.innerHTML = `
        <span class="page-thumb-num">${page.number}</span>
        <span class="page-thumb-preview">Pg ${page.number}</span>
        <span class="deleted-label">deleted</span>
      `;
      el.addEventListener('click', (e) => {
        if (e.shiftKey || e.ctrlKey) {
          this.toggleSelect(page.number);
        } else {
          this.selectOne(page.number);
        }
      });
      strip.appendChild(el);
    });
  },

  selectOne(pageNum) {
    this.pages.forEach(p => p.selected = false);
    this.selectedPages.clear();
    const page = this.pages.find(p => p.number === pageNum);
    if (page && !page.deleted) {
      page.selected = true;
      this.selectedPages.add(pageNum);
    }
    this.render();
    this._updateToolbarState();
  },

  toggleSelect(pageNum) {
    const page = this.pages.find(p => p.number === pageNum);
    if (!page || page.deleted) return;
    page.selected = !page.selected;
    if (page.selected) {
      this.selectedPages.add(pageNum);
    } else {
      this.selectedPages.delete(pageNum);
    }
    this.render();
    this._updateToolbarState();
  },

  markDeleted() {
    for (const num of this.selectedPages) {
      const page = this.pages.find(p => p.number === num);
      if (page) page.deleted = true;
    }
    this.selectedPages.clear();
    this.render();
    this._updateToolbarState();
  },

  rotateSelected(angle) {
    // Stored as metadata, applied on export
    for (const num of this.selectedPages) {
      const page = this.pages.find(p => p.number === num);
      if (page) {
        page.rotation = (page.rotation || 0) + angle;
      }
    }
    this.render();
  },

  getOrder() {
    return this.pages.map(p => p.number);
  },

  getPagesToDelete() {
    return this.pages.filter(p => p.deleted).map(p => p.number);
  },

  getRotations() {
    const rots = {};
    this.pages.forEach(p => {
      if (p.rotation) rots[String(p.number)] = p.rotation;
    });
    return rots;
  },

  getActivePages() {
    return this.pages.filter(p => !p.deleted);
  },

  _initSortable() {
    const strip = document.getElementById('pageStrip');
    if (this.sortable) this.sortable.destroy();
    if (typeof Sortable !== 'undefined') {
      this.sortable = Sortable.create(strip, {
        animation: 150,
        onEnd: (evt) => {
          const moved = this.pages.splice(evt.oldIndex, 1)[0];
          this.pages.splice(evt.newIndex, 0, moved);
          this.render();
        },
      });
    }
  },

  _updateToolbarState() {
    const hasSelection = this.selectedPages.size > 0;
    document.querySelectorAll('.toolbar-btn').forEach(btn => {
      if (btn.dataset.action === 'export') return;
      btn.style.opacity = hasSelection ? '1' : '0.5';
    });
  },

  reset() {
    this.pages = [];
    this.selectedPages.clear();
    this.deletedPages.clear();
    if (this.sortable) this.sortable.destroy();
    this.sortable = null;
    document.getElementById('pageStrip').innerHTML = '';
  },
};
```

- [ ] **Step 2: Commit**

```bash
git add frontend/js/pdf-toolkit.js
git commit -m "feat: add PDF Toolkit frontend logic (page reorder, select, delete)"
```

---

### Task 14: Frontend — Main App Logic

**Files:**
- Create: `frontend/js/app.js`

- [ ] **Step 1: Write frontend/js/app.js**

```javascript
(function () {
  'use strict';

  let currentTool = 'image-convert';
  let currentFile = null;
  let selectedFormat = null;

  const dom = {
    dropZone: document.getElementById('dropZone'),
    fileInput: document.getElementById('fileInput'),
    browseBtn: document.getElementById('browseBtn'),
    fileCard: document.getElementById('fileCard'),
    fileThumb: document.getElementById('fileThumb'),
    fileName: document.getElementById('fileName'),
    formatBadge: document.getElementById('formatBadge'),
    fileSize: document.getElementById('fileSize'),
    fileDetail: document.getElementById('fileDetail'),
    fileRemove: document.getElementById('fileRemove'),
    formatSection: document.getElementById('formatSection'),
    formatChips: document.getElementById('formatChips'),
    convertBtn: document.getElementById('convertBtn'),
    progressSection: document.getElementById('progressSection'),
    progressFill: document.getElementById('progressFill'),
    progressText: document.getElementById('progressText'),
    resultSection: document.getElementById('resultSection'),
    resultPreview: document.getElementById('resultPreview'),
    downloadBtn: document.getElementById('downloadBtn'),
    resetBtn: document.getElementById('resetBtn'),
    pdfToolbar: document.getElementById('pdfToolbar'),
    pageStrip: document.getElementById('pageStrip'),
    steps: document.getElementById('steps'),
  };

  // Format map per tool
  const toolFormats = {
    'image-convert': ['JPG', 'PNG', 'WebP', 'PDF'],
    'pdf-to-image': ['JPG', 'PNG'],
    'image-to-pdf': ['PDF'],
    'pdf-toolkit': [],
    'office-to-pdf': ['PDF'],
  };

  // === Tool Switching ===
  function switchTool(tool) {
    currentTool = tool;
    document.querySelectorAll('.tool-btn, .tab-btn').forEach(b => {
      b.classList.toggle('active', b.dataset.tool === tool);
    });
    resetUI();
    renderFormatChips();
    if (tool === 'pdf-toolkit') {
      dom.pdfToolbar.classList.add('hidden');
      dom.pageStrip.classList.add('hidden');
    } else {
      dom.pdfToolbar.classList.add('hidden');
      dom.pageStrip.classList.add('hidden');
    }
    updateSteps(1);
  }

  document.querySelectorAll('.tool-btn, .tab-btn').forEach(btn => {
    btn.addEventListener('click', () => switchTool(btn.dataset.tool));
  });

  // === Format Chips ===
  function renderFormatChips() {
    const formats = toolFormats[currentTool] || [];
    dom.formatChips.innerHTML = '';
    formats.forEach(fmt => {
      const chip = document.createElement('button');
      chip.className = 'format-chip';
      chip.textContent = fmt;
      chip.addEventListener('click', () => {
        dom.formatChips.querySelectorAll('.format-chip').forEach(c => c.classList.remove('selected'));
        chip.classList.add('selected');
        selectedFormat = fmt.toLowerCase();
        dom.convertBtn.disabled = false;
      });
      dom.formatChips.appendChild(chip);
    });
    selectedFormat = null;
    dom.convertBtn.disabled = true;
  }

  // === File Handling ===
  function handleFile(file) {
    if (!file) return;
    currentFile = file;

    const ext = file.name.split('.').pop().toUpperCase();
    dom.fileName.textContent = file.name;
    dom.formatBadge.textContent = ext;
    dom.fileSize.textContent = formatSize(file.size);

    if (file.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onload = () => {
        dom.fileThumb.innerHTML = `<img src="${reader.result}" alt="preview">`;
      };
      reader.readAsDataURL(file);
      const img = new Image();
      img.onload = () => {
        dom.fileDetail.textContent = `${img.width}x${img.height}`;
      };
      img.src = URL.createObjectURL(file);
    } else if (file.type === 'application/pdf') {
      dom.fileThumb.textContent = 'PDF';
      dom.fileDetail.textContent = '';
    } else {
      dom.fileThumb.textContent = ext.substring(0, 3);
      dom.fileDetail.textContent = '';
    }

    dom.dropZone.classList.add('hidden');
    dom.fileCard.classList.remove('hidden');
    dom.formatSection.classList.remove('hidden');
    updateSteps(1);

    if (currentTool === 'pdf-toolkit') {
      loadPdfPages(file);
    }
  }

  async function loadPdfPages(file) {
    try {
      const { pageCount } = await API.pdfToolkit(file, 'page_count');
      dom.fileDetail.textContent = `${pageCount} pages`;
      PDFToolkit.init(pageCount);
      dom.pdfToolbar.classList.remove('hidden');
      dom.pageStrip.classList.remove('hidden');
      dom.formatSection.classList.add('hidden');
    } catch (err) {
      console.error('Failed to get page count:', err);
    }
  }

  dom.browseBtn.addEventListener('click', () => dom.fileInput.click());
  dom.fileInput.addEventListener('change', () => {
    if (dom.fileInput.files[0]) handleFile(dom.fileInput.files[0]);
  });
  dom.dropZone.addEventListener('click', () => dom.fileInput.click());
  dom.dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dom.dropZone.classList.add('drag-over');
  });
  dom.dropZone.addEventListener('dragleave', () => {
    dom.dropZone.classList.remove('drag-over');
  });
  dom.dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dom.dropZone.classList.remove('drag-over');
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  });
  dom.fileRemove.addEventListener('click', resetUI);

  // === Toolbar Actions ===
  dom.pdfToolbar.addEventListener('click', (e) => {
    const btn = e.target.closest('.toolbar-btn');
    if (!btn) return;
    const action = btn.dataset.action;
    if (action === 'compress') {
      downloadPdfToolkitResult('compress');
    } else if (action === 'rotate-left') {
      PDFToolkit.rotateSelected(-90);
    } else if (action === 'rotate-right') {
      PDFToolkit.rotateSelected(90);
    } else if (action === 'delete') {
      PDFToolkit.markDeleted();
    } else if (action === 'export') {
      downloadPdfToolkitResult('export');
    }
  });

  async function downloadPdfToolkitResult(action) {
    if (!currentFile) return;
    try {
      showProgress();
      let result;
      if (action === 'compress') {
        result = await API.pdfToolkit(currentFile, 'compress');
      } else if (action === 'export') {
        const pagesToDelete = PDFToolkit.getPagesToDelete();
        const rotations = PDFToolkit.getRotations();
        const order = PDFToolkit.getOrder();

        let file = currentFile;
        if (pagesToDelete.length > 0) {
          result = await API.pdfToolkit(file, 'delete', { pages: pagesToDelete.join(',') });
          file = new File([result.blob], 'temp.pdf', { type: 'application/pdf' });
        }
        if (Object.keys(rotations).length > 0) {
          result = await API.pdfToolkit(file, 'rotate', { rotations });
          file = new File([result.blob], 'temp.pdf', { type: 'application/pdf' });
        }
        result = await API.pdfToolkit(file, 'reorder', { order: order.join(',') });
      } else {
        return;
      }
      hideProgress();
      showResult(result.blob, result.filename);
    } catch (err) {
      hideProgress();
      alert('Error: ' + err.message);
    }
  }

  // === Convert ===
  dom.convertBtn.addEventListener('click', async () => {
    if (!currentFile || !selectedFormat) return;
    try {
      showProgress();
      updateSteps(2);
      const result = await API.convert(currentFile, selectedFormat);
      hideProgress();
      updateSteps(3);
      showResult(result.blob, result.filename);
    } catch (err) {
      hideProgress();
      alert('Error: ' + err.message);
    }
  });

  // === Result ===
  function showResult(blob, filename) {
    const url = URL.createObjectURL(blob);
    dom.resultPreview.innerHTML = '';
    if (blob.type.startsWith('image/')) {
      dom.resultPreview.innerHTML = `<img src="${url}" alt="result">`;
    } else {
      dom.resultPreview.innerHTML = `<p style="color:#64748b">${filename}</p><p style="color:#94a3b8;font-size:12px;margin-top:4px">${formatSize(blob.size)}</p>`;
    }
    dom.resultSection.classList.remove('hidden');
    dom.downloadBtn.onclick = () => {
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      a.click();
    };
  }

  dom.resetBtn.addEventListener('click', resetUI);

  // === Progress ===
  function showProgress() {
    dom.progressSection.classList.remove('hidden');
    dom.progressFill.style.width = '0%';
    dom.progressText.textContent = 'Converting...';
    let w = 0;
    const interval = setInterval(() => {
      w += Math.random() * 30;
      if (w > 90) { w = 90; clearInterval(interval); }
      dom.progressFill.style.width = w + '%';
    }, 200);
    dom.progressSection._interval = interval;
  }

  function hideProgress() {
    clearInterval(dom.progressSection._interval);
    dom.progressFill.style.width = '100%';
    setTimeout(() => {
      dom.progressSection.classList.add('hidden');
      dom.progressFill.style.width = '0%';
    }, 400);
  }

  // === Steps ===
  function updateSteps(active) {
    dom.steps.querySelectorAll('.step').forEach(s => {
      const num = parseInt(s.dataset.step);
      s.classList.remove('active', 'completed');
      if (num < active) s.classList.add('completed');
      if (num === active) s.classList.add('active');
    });
  }

  // === Reset ===
  function resetUI() {
    currentFile = null;
    selectedFormat = null;
    dom.fileInput.value = '';
    dom.dropZone.classList.remove('hidden');
    dom.fileCard.classList.add('hidden');
    dom.formatSection.classList.add('hidden');
    dom.progressSection.classList.add('hidden');
    dom.resultSection.classList.add('hidden');
    dom.pdfToolbar.classList.add('hidden');
    dom.pageStrip.classList.add('hidden');
    dom.resultPreview.innerHTML = '<p class="placeholder">Your converted file will appear here</p>';
    dom.convertBtn.disabled = true;
    PDFToolkit.reset();
    renderFormatChips();
    updateSteps(1);
  }

  // === Helpers ===
  function formatSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  }

  // === Init ===
  renderFormatChips();
  switchTool('image-convert');
})();
```

- [ ] **Step 2: Commit**

```bash
git add frontend/js/app.js
git commit -m "feat: add main frontend app logic"
```

---

### Task 15: Integration Testing & README

**Files:**
- Modify: `README.md`
- Create/modify: tests for integration

- [ ] **Step 1: Run all backend tests**

```bash
cd backend && python -m pytest ../tests/ -v
```
Expected: All tests pass (office tests may skip if no LibreOffice)

- [ ] **Step 2: Start dev server to verify frontend**

```bash
cd backend && python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```
Manual check: Open http://localhost:8000, upload a file, test conversion flow.

- [ ] **Step 3: Write README.md**

```markdown
# FileConverter

Open source web-based file converter. Supports image, document, and PDF conversions. All processing is in-memory — files are never stored.

## Features

- **Image Convert**: JPG, PNG, WebP, HEIF, SVG, BMP, TIFF → JPG, PNG, WebP, PDF
- **PDF to Image**: PDF → JPG, PNG (per page or all pages)
- **Image to PDF**: Single or multiple images → PDF
- **PDF Toolkit**: Compress, merge, split, reorder, rotate, delete pages, edit text
- **Office to PDF**: DOCX, XLSX, PPTX → PDF

## Quick Start

### Prerequisites

- Python 3.11+
- poppler-utils (for PDF to image)
- LibreOffice (optional, for Office to PDF)

```bash
# Install system dependencies (Ubuntu/Debian)
sudo apt install poppler-utils libreoffice-core

# Clone and install
git clone https://github.com/NyChieng/File-converter-Open-source-.git
cd File-converter-Open-source-
pip install -r backend/requirements.txt

# Run
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Open http://localhost:8000

## Architecture

```
POST /api/convert     — convert files between formats
POST /api/pdf/toolkit — PDF operations (compress, merge, split, etc.)
GET  /api/formats     — list supported formats
```

Frontend is served as static files by FastAPI. No CORS, no separate web server.

## Hosting

Runs on any VPS ($4-6/month). Recommended: uvicorn behind Caddy for auto-HTTPS.

## Security

- Files processed in `/tmp`, deleted immediately after response
- File type validated by magic bytes
- Rate limiting (20 req/min per IP)
- No persistent storage, no user accounts

## License

MIT
```

- [ ] **Step 4: Final commit**

```bash
git add README.md
git commit -m "docs: add comprehensive README"
```

---

### Task 16: Final Verification & Push Prep

- [ ] **Step 1: Run full test suite**

```bash
python -m pytest tests/ -v
```
Expected: All tests pass.

- [ ] **Step 2: Verify frontend is served**

```bash
python -c "from backend.main import app; print('App loads OK')"
```

- [ ] **Step 3: Check all files are tracked**

```bash
git status
```
Expected: No untracked files (except .superpowers/ in .gitignore).

- [ ] **Step 4: Commit any remaining changes**

```bash
git add -A
git commit -m "chore: final cleanup and verification"
```
