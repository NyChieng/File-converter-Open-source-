import logging
import tempfile
import zipfile
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, Form, UploadFile, Request, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fileconverter")

from backend.config import (
    ALLOWED_IMAGE_INPUT, ALLOWED_IMAGE_OUTPUT, ALLOWED_PDF_INPUT,
    ALLOWED_OFFICE_INPUT, MAX_FILE_SIZE,
)
from backend.validators import validate_file, sanitize_filename, get_mime_type
from backend.security import create_rate_limiter, get_client_ip
from backend.converters import (
    image, pdf_to_image, image_to_pdf, office, pdf_toolkit,
)

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
            "image": sorted(ALLOWED_IMAGE_INPUT),
            "pdf": sorted(ALLOWED_PDF_INPUT),
            "office": sorted(ALLOWED_OFFICE_INPUT),
        },
        "output": sorted(ALLOWED_IMAGE_OUTPUT),
    }


def _cleanup(*paths: Path):
    for p in paths:
        try:
            if p.exists():
                p.unlink()
        except Exception:
            pass


@app.post("/api/convert")
async def convert_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    output_format: str = Form(...),
):
    output_format = output_format.lower().strip().lstrip(".")
    if output_format not in ALLOWED_IMAGE_OUTPUT:
        raise HTTPException(
            400, f"Unsupported output format: {output_format}"
        )

    tmp_in = tempfile.NamedTemporaryFile(
        delete=False, suffix=Path(file.filename or "file").suffix
    )
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        tmp_in.close()
        _cleanup(Path(tmp_in.name))
        raise HTTPException(
            413, f"File exceeds {MAX_FILE_SIZE // 1024 // 1024}MB limit"
        )
    tmp_in.write(content)
    tmp_in.close()
    tmp_in_path = Path(tmp_in.name)

    mime = get_mime_type(tmp_in_path)
    tmp_out = Path(tempfile.mktemp(suffix=f".{output_format}"))
    cleanup_paths = [tmp_in_path, tmp_out]

    if mime in ALLOWED_IMAGE_INPUT:
        try:
            if output_format == "pdf":
                result = image_to_pdf.convert_images_to_pdf(
                    [tmp_in_path], tmp_out
                )
            else:
                result = image.convert_image(
                    tmp_in_path, tmp_out, output_format
                )
        except Exception as e:
            logger.exception("Image conversion failed")
            _cleanup(*cleanup_paths)
            raise HTTPException(500, f"Conversion failed: {e}")
    elif mime in ALLOWED_OFFICE_INPUT:
        if output_format != "pdf":
            _cleanup(*cleanup_paths)
            raise HTTPException(
                400, f"Office files can only be converted to PDF, not {output_format}"
            )
        try:
            result = office.convert_office_to_pdf(tmp_in_path, tmp_out)
        except Exception as e:
            logger.exception("Office to PDF conversion failed")
            _cleanup(*cleanup_paths)
            raise HTTPException(500, f"Conversion failed: {e}")
    elif mime in ALLOWED_PDF_INPUT:
        if output_format in ("jpg", "png", "jpeg"):
            try:
                result = pdf_to_image.convert_pdf_to_image(
                    tmp_in_path, tmp_out, output_format
                )
            except Exception as e:
                logger.exception("PDF to image conversion failed")
                _cleanup(*cleanup_paths)
                raise HTTPException(500, f"Conversion failed: {e}")
        elif output_format in ("webp", "pdf"):
            _cleanup(*cleanup_paths)
            raise HTTPException(
                400, f"Cannot convert PDF to {output_format}"
            )
        else:
            _cleanup(*cleanup_paths)
            raise HTTPException(
                400, f"Unsupported PDF output: {output_format}"
            )
    else:
        _cleanup(*cleanup_paths)
        raise HTTPException(400, f"Unsupported input format: {mime}")

    out_name = sanitize_filename(file.filename or "file")
    out_name = Path(out_name).stem + f".{output_format}"

    if isinstance(result, list):
        zip_path = tmp_out.parent / f"{Path(out_name).stem}.zip"
        cleanup_paths.append(zip_path)
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for r in result:
                zf.write(r, r.name)
        background_tasks.add_task(_cleanup, *cleanup_paths)
        return FileResponse(
            zip_path,
            filename=f"{Path(out_name).stem}.zip",
            media_type="application/zip",
        )

    media = (
        f"image/{output_format}"
        if output_format != "pdf"
        else "application/pdf"
    )
    if output_format in ("jpg", "jpeg"):
        media = "image/jpeg"

    background_tasks.add_task(_cleanup, *cleanup_paths)
    return FileResponse(result, filename=out_name, media_type=media)


@app.post("/api/pdf/toolkit")
async def pdf_toolkit_route(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    action: str = Form(...),
    pages: str = Form(None),
    order: str = Form(None),
    rotations: str = Form(None),
):
    action = action.strip().lower()
    valid_actions = {
        "compress", "merge", "split", "reorder", "rotate",
        "delete", "page_count",
    }
    if action not in valid_actions:
        raise HTTPException(
            400, f"Invalid action: {action}. Valid: {valid_actions}"
        )

    tmp_in = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        tmp_in.close()
        _cleanup(Path(tmp_in.name))
        raise HTTPException(413)
    tmp_in.write(content)
    tmp_in.close()
    tmp_in_path = Path(tmp_in.name)

    mime = get_mime_type(tmp_in_path)
    if mime not in ALLOWED_PDF_INPUT:
        _cleanup(tmp_in_path)
        raise HTTPException(400, "File must be a PDF")

    if action == "page_count":
        count = pdf_toolkit.get_page_count(tmp_in_path)
        _cleanup(tmp_in_path)
        return JSONResponse({"pages": count})

    tmp_out = Path(tempfile.mktemp(suffix=".pdf"))
    cleanup_paths = [tmp_in_path, tmp_out]

    if action == "compress":
        result = pdf_toolkit.compress_pdf(tmp_in_path, tmp_out)
    elif action == "split":
        out_dir = Path(tempfile.mkdtemp())
        ranges = pages.split(";") if pages else ["1"]
        results = pdf_toolkit.split_pdf(tmp_in_path, out_dir, ranges)
        zip_path = Path(tempfile.mktemp(suffix=".zip"))
        cleanup_paths.append(zip_path)
        with zipfile.ZipFile(zip_path, "w") as zf:
            for r in results:
                zf.write(r, r.name)
        background_tasks.add_task(_cleanup, *cleanup_paths)
        return FileResponse(
            zip_path,
            filename="split_pages.zip",
            media_type="application/zip",
        )
    elif action == "reorder":
        order_list = (
            [int(x) for x in order.split(",")] if order else []
        )
        result = pdf_toolkit.reorder_pages(
            tmp_in_path, tmp_out, order_list
        )
    elif action == "rotate":
        import json
        rots = json.loads(rotations) if rotations else {}
        result = pdf_toolkit.rotate_pages(tmp_in_path, tmp_out, rots)
    elif action == "delete":
        delete_list = (
            [int(x) for x in pages.split(",")] if pages else []
        )
        result = pdf_toolkit.delete_pages(
            tmp_in_path, tmp_out, delete_list
        )
    else:
        _cleanup(*cleanup_paths)
        raise HTTPException(400, f"Unknown action: {action}")

    background_tasks.add_task(_cleanup, *cleanup_paths)
    return FileResponse(
        result,
        filename="output.pdf",
        media_type="application/pdf",
    )


app.mount(
    "/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="static"
)
