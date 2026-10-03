import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from app.config import settings

router = APIRouter(prefix="/media", tags=["media"])

@router.get("/{document_id}/{filename}")
def get_media_file(document_id: str, filename: str):
    file_path = os.path.join(settings.EXTRACTED_MEDIA_DIR, document_id, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Media file not found.")
    return FileResponse(file_path)
