# FileConverter — Design Spec

**Date:** 2026-05-12
**Status:** Approved

## Overview

Web-based file converter supporting image, document, and PDF conversions. Open source (MIT). All processing is in-memory — files are never stored on disk beyond the temp directory and are wiped immediately after conversion.

## Architecture

```
Monorepo: backend/ + frontend/ served by a single FastAPI process.

User Browser  ──POST /api/convert──>  FastAPI Server
  (file + target format)              │
                                      ├─ Validate: type, size, extension
                                      ├─ Write to /tmp
                                      ├─ Run converter module
                                      ├─ Stream FileResponse
                                      └─ Delete /tmp files immediately

                                     No persistent storage.
```

Frontend is served as static files by FastAPI — no separate web server, no CORS.

## Tech Stack

- **Backend:** Python 3.11+ / FastAPI
  - Pillow (image conversion)
  - pillow-heif (HEIF support)
  - pdf2image + poppler (PDF → image)
  - reportlab (image → PDF)
  - pikepdf / PyPDF2 (PDF merge, split, compress, reorder)
  - PyMuPDF/fitz (PDF text/image editing)
  - unoserver + LibreOffice (Office → PDF)
  - python-multipart (file uploads)
  - uvicorn (ASGI server)

- **Frontend:** Vanilla HTML/CSS/JS (no framework, no build step)
  - SortableJS (drag-and-drop page reordering in PDF Toolkit)
  - pdf.js (PDF page thumbnail previews)

## Feature Set

### Image Conversion
| From                        | To                          |
|-----------------------------|-----------------------------|
| JPG, PNG, WebP, HEIF, SVG, BMP, TIFF | JPG, PNG, WebP, PDF |

### Document Conversion
| From          | To            |
|---------------|---------------|
| PDF           | JPG, PNG      |
| JPG, PNG, WebP| PDF           |
| DOCX, XLSX, PPTX | PDF        |

### PDF Toolkit
- Compress (Ghostscript via pikepdf)
- Merge multiple PDFs
- Split by page ranges
- Reorder pages (drag-and-drop)
- Rotate pages (left/right)
- Delete pages
- Edit text content (PyMuPDF)
- Edit/replace images (PyMuPDF)

## UI Design

**Layout:** Sidebar + Workspace with Deep Indigo color scheme (`#4f46e5` accent).

**Sidebar** (200px, collapses to bottom tab bar on mobile):
- Image Convert
- PDF to Image
- Image to PDF
- PDF Toolkit
- Office to PDF

**Workspace** — shared across all tools:
1. File card: thumbnail icon, filename, auto-detected format badge, file size, dimensions/page count
2. Step indicator: Upload → Convert → Download (active step highlighted in indigo)
3. Format selector: chip-style buttons for output formats
4. Convert button: full indigo, primary CTA
5. Result panel: preview + green Download button

**PDF Toolkit workspace** adds:
- Toolbar: Compress, Rotate Left, Rotate Right, Delete, Export
- Page thumbnail strip: film-strip layout, click to select, drag to reorder, red badge for deleted pages

**Mobile:** Sidebar becomes a bottom tab bar with icons + short labels. Vertical stacking for workspace content.

## Security

- File type validation by magic bytes, not extension
- File size limit configurable (default 250MB)
- Rate limiting per IP (20 requests/minute)
- Filenames sanitized (uuid-based temp names)
- Files processed in `/tmp`, deleted in `finally` block
- No shell injection — all external tool calls use subprocess with list args, no shell=True
- CORS restricted to same origin
- Input validation on all API parameters

## API Design

```
POST /api/convert
  Content-Type: multipart/form-data
  Body:
    file: File          (required)
    output_format: str  (required, e.g. "jpg", "png", "pdf")
    options: JSON       (optional, e.g. {"quality": 85, "pages": "1-3"})
  Response:
    Content-Type: application/octet-stream
    Content-Disposition: attachment; filename="converted.ext"
```

```
POST /api/pdf/toolkit
  Content-Type: multipart/form-data
  Body:
    file: File          (required)
    action: str         (required: compress, merge, split, reorder, rotate, delete, edit_text, edit_image)
    options: JSON       (action-specific params)
  Response: FileResponse or JSON with action result
```

## Hosting

**Recommended:** Single VPS ($4-6/month on Hetzner/DigitalOcean) with:
- uvicorn behind Caddy (auto HTTPS)
- LibreOffice headless for Office conversions
- poppler-utils for PDF processing

**Free alternative:** Railway.app free tier (512MB RAM, shared CPU) for everything except Office conversions. GitHub Pages for the frontend if splitting.

## File Size Limits

No hardcoded 50MB limit. Configurable via env var, default 250MB. Actual limit depends on available server RAM since conversions happen in memory.

## What This Project Does Not Do

- No user accounts or authentication
- No persistent file storage
- No conversion history
- No batch/queue processing (one file at a time)
- No OCR or AI-based features
