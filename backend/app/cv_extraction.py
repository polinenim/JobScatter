from io import BytesIO

import fitz

MAX_CV_UPLOAD_BYTES = 10 * 1024 * 1024


class CvExtractionError(ValueError):
    pass


def extract_pdf_text(data: bytes) -> str:
    if len(data) > MAX_CV_UPLOAD_BYTES:
        raise CvExtractionError("PDF exceeds the 10 MiB upload limit")
    if not data.startswith(b"%PDF-"):
        raise CvExtractionError("Uploaded file is not a PDF")

    try:
        with fitz.open(stream=BytesIO(data), filetype="pdf") as document:
            text = "\n".join(page.get_text() for page in document).strip()
    except (fitz.FileDataError, RuntimeError) as exc:
        raise CvExtractionError("Uploaded PDF could not be read") from exc

    if not text:
        raise CvExtractionError("PDF contains no usable extractable text")
    return text
