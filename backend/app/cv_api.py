from fastapi import APIRouter, File, HTTPException, UploadFile, status
from pydantic import BaseModel

from app.cv_extraction import CvExtractionError, MAX_CV_UPLOAD_BYTES, extract_pdf_text

router = APIRouter(prefix="/candidates", tags=["candidate CV"])


class CvTextResponse(BaseModel):
    text: str
    character_count: int


@router.post("/cv/extract", response_model=CvTextResponse)
async def extract_cv_text(file: UploadFile = File(...)) -> CvTextResponse:
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only PDF CV uploads are supported",
        )

    data = await file.read(MAX_CV_UPLOAD_BYTES + 1)
    try:
        text = extract_pdf_text(data)
    except CvExtractionError as exc:
        status_code = (
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
            if len(data) > MAX_CV_UPLOAD_BYTES
            else status.HTTP_422_UNPROCESSABLE_ENTITY
        )
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc

    return CvTextResponse(text=text, character_count=len(text))
