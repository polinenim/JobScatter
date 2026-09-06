from __future__ import annotations

from datetime import datetime
from html import escape
from io import BytesIO
from typing import Iterable, Protocol

from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


class ReportJob(Protocol):
    company_name: str
    job_title: str
    posted_at: datetime
    job_link: str


def generate_job_report(jobs: Iterable[ReportJob]) -> bytes:
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.65 * inch,
        leftMargin=0.65 * inch,
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch,
        title="JobScatter Job Report",
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        alignment=TA_LEFT,
        spaceAfter=14,
    )
    job_style = ParagraphStyle(
        "JobEntry",
        parent=styles["BodyText"],
        leading=15,
        spaceAfter=12,
    )
    story = [Paragraph("JobScatter Job Report", title_style)]
    for job in jobs:
        posted = job.posted_at.isoformat()
        link = escape(job.job_link, quote=True)
        story.extend(
            [
                Paragraph(f"<b>Company:</b> {escape(job.company_name)}", job_style),
                Paragraph(f"<b>Job title:</b> {escape(job.job_title)}", job_style),
                Paragraph(f"<b>Posted:</b> {escape(posted)}", job_style),
                Paragraph(f'<b>Link:</b> <link href="{link}" color="blue">{link}</link>', job_style),
                Spacer(1, 8),
            ]
        )
    document.build(story)
    return buffer.getvalue()