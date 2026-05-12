import uuid
import re
import filetype
from pathlib import Path
from backend.config import MAX_FILE_SIZE

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
        raise ValueError(
            f"File size {size} exceeds limit {max_size}"
        )
    mime = get_mime_type(filepath)
    if mime not in allowed_types:
        raise ValueError(
            f"File type '{mime}' is not allowed. Accepted: {allowed_types}"
        )
    return filepath


def sanitize_filename(name: str) -> str:
    name = Path(name).name
    name = re.sub(r"[^\w\-.]", "_", name)
    stem, ext = Path(name).stem, Path(name).suffix
    stem = stem.strip("_") or "file"
    return f"{stem}{ext}"


def temp_filepath(extension: str) -> Path:
    return Path(f"/tmp/{uuid.uuid4()}.{extension.lstrip('.')}")
