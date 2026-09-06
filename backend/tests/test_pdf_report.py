from datetime import datetime, timezone
from uuid import uuid4

import fitz
from fastapi.testclient import TestClient

from app import search_api
from app.main import app
from app.pdf_report import generate_job_report


NOW = datetime(2026, 9, 5, 12, tzinfo=timezone.utc)
client = TestClient(app)


def job(company="Example Co", title="Software Engineer", link="https://jobs.example/1", posted_at=NOW):
    return search_api.UnifiedSearchResult(
        company_name=company,
        job_title=title,
        posted_at=posted_at,
        job_link=link,
    )


def test_pdf_contains_four_required_fields_and_clickable_link():
    pdf = generate_job_report([job()])
    document = fitz.open(stream=pdf, filetype="pdf")
    page = document[0]
    text = page.get_text()
    links = page.get_links()

    assert "Example Co" in text
    assert "Software Engineer" in text
    assert "2026-09-05T12:00:00+00:00" in text
    assert "https://jobs.example/1" in text
    assert any(link.get("uri") == "https://jobs.example/1" for link in links)


def test_pdf_contains_multiple_jobs_in_input_order():
    pdf = generate_job_report([
        job("First Co", "First Role", "https://jobs.example/1"),
        job("Second Co", "Second Role", "https://jobs.example/2"),
    ])
    text = "".join(page.get_text() for page in fitz.open(stream=pdf, filetype="pdf"))

    assert text.index("First Co") < text.index("Second Co")
    assert "First Role" in text
    assert "Second Role" in text


def test_pdf_empty_results_is_valid_pdf_without_job_fields():
    pdf = generate_job_report([])
    document = fitz.open(stream=pdf, filetype="pdf")

    assert len(document) == 1
    assert "JobScatter Job Report" in document[0].get_text()
    assert "Company:" not in document[0].get_text()


def test_search_pdf_endpoint_uses_stored_search_results(monkeypatch):
    candidate_id = uuid4()

    class FakeService:
        def run(self, received_id):
            assert received_id == candidate_id
            return search_api.UnifiedSearchResponse(
                candidate_id=candidate_id,
                items=[job()],
                total=1,
            )

    monkeypatch.setattr(search_api, "UnifiedSearchService", FakeService)

    response = client.post("/search/pdf", json={"candidate_id": str(candidate_id)})

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")
