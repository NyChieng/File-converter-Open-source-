import shutil
import subprocess
import tempfile
from pathlib import Path

SUPPORTED_OFFICE = {
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
}

_LIBREOFFICE_PATH = (
    shutil.which("soffice") or shutil.which("libreoffice") or "soffice"
)


def convert_office_to_pdf(src: Path, dest: Path) -> Path:
    ext = src.suffix.lower()
    if ext not in SUPPORTED_OFFICE:
        raise ValueError(
            f"Unsupported office format: {ext}. "
            f"Supported: {list(SUPPORTED_OFFICE.keys())}"
        )

    lo = shutil.which(_LIBREOFFICE_PATH)
    if not lo:
        raise RuntimeError(
            "LibreOffice not found. Install with: sudo apt install libreoffice-core"
        )

    with tempfile.TemporaryDirectory() as tmpdir:
        cmd = [
            lo, "--headless", "--norestore",
            "--convert-to", "pdf", "--outdir", tmpdir, str(src),
        ]
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=120
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"LibreOffice conversion failed: {result.stderr}"
            )
        pdfs = list(Path(tmpdir).glob("*.pdf"))
        if not pdfs:
            raise RuntimeError("LibreOffice produced no PDF output")
        pdfs[0].rename(dest)
        return dest
