# FileConverter

Open source web-based file converter. Supports image, document, and PDF conversions. All processing is in-memory — files are never stored.

## Features

- **Image Convert** — JPG, PNG, WebP, HEIF, SVG, BMP, TIFF to JPG, PNG, WebP
- **PDF to Image** — PDF to JPG or PNG (single page or all pages)
- **Image to PDF** — One or multiple images combined into a PDF
- **PDF Toolkit** — Compress, merge, split, reorder, rotate, delete pages, edit text
- **Office to PDF** — DOCX, XLSX, PPTX to PDF (requires LibreOffice)

## Quick Start

### Prerequisites

- Python 3.11+
- poppler-utils (for PDF to image)
- LibreOffice (optional, for Office to PDF)

```bash
# Ubuntu/Debian
sudo apt install poppler-utils libreoffice-core

# macOS
brew install poppler libreoffice

# Windows
# Install poppler from: https://github.com/oschwartz10612/poppler-windows/releases/
```

### Install & Run

```bash
git clone https://github.com/NyChieng/File-converter-Open-source-.git
cd File-converter-Open-source-
pip install -r backend/requirements.txt
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Open http://localhost:8000

## API

```
POST /api/convert       — Convert files between formats
POST /api/pdf/toolkit   — PDF operations (compress, merge, split, etc.)
GET  /api/formats       — List supported formats
```

## Architecture

FastAPI monorepo — backend serves both the API and static frontend. Files are written to `/tmp`, processed, served via FileResponse, then cleaned up via background tasks. No persistent storage, no CORS.

## Hosting

Runs on any VPS ($4-6/month on Hetzner/DigitalOcean). Recommended: uvicorn behind Caddy for auto-HTTPS.

## Security

- Files processed in `/tmp`, deleted after response
- File type validated by magic bytes (not extension)
- Rate limiting (20 req/min per IP)
- No persistent storage, no user accounts

## License

MIT
