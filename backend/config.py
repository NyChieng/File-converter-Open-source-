import os

MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 250 * 1024 * 1024))
RATE_LIMIT = os.getenv("RATE_LIMIT", "20/minute")
TEMP_DIR = os.getenv("TEMP_DIR", "/tmp")

ALLOWED_IMAGE_INPUT = {
    "image/jpeg", "image/png", "image/webp", "image/heif", "image/heic",
    "image/svg+xml", "image/bmp", "image/tiff",
}
ALLOWED_IMAGE_OUTPUT = {"jpg", "jpeg", "png", "webp", "pdf"}
ALLOWED_PDF_INPUT = {"application/pdf"}
ALLOWED_OFFICE_INPUT = {
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
}
