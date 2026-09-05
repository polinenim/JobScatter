from io import BytesIO

import fitz
from fastapi.testclient import TestClient

from app.cv_extraction import MAX_CV_UPLOAD_BYTES
from app.main import app

client = TestClient(app)


def make_pdf(text: str | None = None) -> bytes:
    document = fitz.open()
    page = document.new_page()
    if text:
        page.insert_text((72, 72), text)
    data = document.tobytes()
    document.close()
    return data


def test_extract_cv_returns_text_from_valid_pdf():
    response = client.post(
        "/candidates/cv/extract",
        files={"file": ("cv.pdf", BytesIO(make_pdf("Python Backend Engineer")), "application/pdf")},
    )

    assert response.status_code == 200
    assert response.json()["text"] == "Python Backend Engineer"
    assert response.json()["character_count"] == len("Python Backend Engineer")


def test_extract_cv_rejects_non_pdf_content_type():
    response = client.post(
        "/candidates/cv/extract",
        files={"file": ("cv.txt", BytesIO(b"not a pdf"), "text/plain")},
    )

    assert response.status_code == 415
    assert response.json()["detail"] == "Only PDF CV uploads are supported"


def test_extract_cv_rejects_pdf_without_extractable_text():
    response = client.post(
        "/candidates/cv/extract",
        files={"file": ("scan.pdf", BytesIO(make_pdf()), "application/pdf")},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "PDF contains no usable extractable text"


def test_extract_cv_rejects_oversized_upload():
    response = client.post(
        "/candidates/cv/extract",
        files={
            "file": (
                "large.pdf",
                BytesIO(b"%PDF-" + b"x" * MAX_CV_UPLOAD_BYTES),
                "application/pdf",
            )
        },
    )

    assert response.status_code == 413
    assert response.json()["detail"] == "PDF exceeds the 10 MiB upload limit"
