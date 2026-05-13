<p align="center">
  <img src="https://img.shields.io/badge/license-MIT-blue" alt="License MIT">
  <img src="https://img.shields.io/badge/PRs-welcome-brightgreen" alt="PRs Welcome">
  <img src="https://img.shields.io/badge/processing-in--memory-%234f46e5" alt="In-Memory">
</p>

<h1 align="center">FileConverter</h1>
<p align="center"><em>Convert anything. Keep nothing.</em></p>

---

Drag a file in. Pick a format. Hit convert. **That's it.**

No accounts. No uploads sitting on a server somewhere. No "your file will be ready in 5 minutes." Every file is processed in RAM and gone the moment your download finishes.

<br>

## What it does

| Tool | Turns this | Into this |
|------|-----------|-----------|
| **Image Convert** | JPG · PNG · WebP · HEIF · SVG · BMP · TIFF | JPG · PNG · WebP |
| **PDF to Image** | PDF | JPG · PNG (per page or whole doc) |
| **Image to PDF** | JPG · PNG · WebP · HEIF · etc | a clean PDF |
| **PDF Toolkit** | any PDF | compressed · split · reordered · rotated · trimmed |
| **Office to PDF** | DOCX · XLSX · PPTX | PDF |

<br>

## &#9654; One click to run

Windows? Double-click **`run.bat`**. It checks Python, creates a venv, installs everything, and opens the browser. Done.

Everyone else:

```bash
pip install -r backend/requirements.txt
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Then open **http://localhost:8000**.

> **Need LibreOffice?** It's only required for Office-to-PDF. Everything else works without it.

<br>

## &#9654; Docker (also one click)

```bash
docker build -t fileconverter .
docker run -p 8000:8000 fileconverter
```

Or let GitHub do the work:

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://github.com/NyChieng/File-converter-Open-source-/codespaces)

<br>

## What's inside

```
frontend/          vanilla HTML/CSS/JS — no frameworks, no build step
backend/
  main.py          FastAPI app — serves API + static frontend
  config.py        allowed formats, file size limits
  validators.py    magic-byte file type checking (no extension spoofing)
  security.py      rate limiter (20 req/min per IP)
  converters/
    image.py         Pillow-based image conversion
    pdf_to_image.py  PDF → JPG/PNG (pdftoppm or PyMuPDF fallback)
    image_to_pdf.py  images → single PDF
    pdf_toolkit.py   compress, split, merge, reorder, rotate, delete pages
    office.py        DOCX/XLSX/PPTX → PDF via LibreOffice headless
tests/             pytest suite for every endpoint
```

<br>

## API at a glance

```http
POST /api/convert        file + output_format → converted file
POST /api/pdf/toolkit    file + action → result
GET  /api/formats        supported input/output formats
```

**No API keys. No rate limits on localhost.** The built-in limiter only kicks in for remote IPs.

<br>

## Host it yourself

This is a single Python process. It needs:

- Python 3.11+
- `poppler-utils` (for PDF rendering — `apt install poppler-utils`)
- LibreOffice (optional — only for office docs)

Throw it on any VPS (Hetzner $4/mo, Fly.io free tier, Render free tier). Stick Caddy or Nginx in front if you want HTTPS.

```bash
# Behind Caddy (auto-HTTPS):
uvicorn backend.main:app --host 127.0.0.1 --port 8000
# caddy reverse-proxy --from yourdomain.com --to :8000
```

<br>

## Contributing

Found a bug? Want a format added? **PRs are genuinely welcome.**

```bash
git clone https://github.com/NyChieng/File-converter-Open-source-.git
cd File-converter-Open-source-

# Run the tests
pip install pytest httpx
pytest tests/ -v
```

Open an issue before writing big features so we can talk it through first.

<br>

## License

MIT — use it, fork it, ship it, sell it. Just keep the license notice.
