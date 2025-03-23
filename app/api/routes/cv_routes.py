from fastapi import APIRouter, File, UploadFile, HTTPException, BackgroundTasks
from typing import List

from app.core.exceptions import BadRequestException, InternalServerException
from app.api.models.cv import CVUploadResponse, CVDocument
from app.services.cv_processor import process_cv_file
from app.infrastructure.vector_db import get_all_cvs

router = APIRouter()

@router.post("/upload", response_model=CVUploadResponse, summary="Upload a CV")
async def upload_cv(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """Upload a CV file (PDF) to be processed and indexed"""
    
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise BadRequestException(detail="Only PDF files are supported")
    
    try:
        # Process the CV in the background
        background_tasks.add_task(process_cv_file, file)
        
        return {"message": f"CV uploaded and being processed: {file.filename}"}
    except Exception as e:
        raise InternalServerException(detail=f"Error processing CV: {str(e)}")

@router.get("/cv", response_model=List[CVDocument], summary="Get all CVs")
async def get_cvs():
    """Get all uploaded CVs"""
    try:
        return get_all_cvs()
    except Exception as e:
        raise InternalServerException(detail=f"Error retrieving CVs: {str(e)}")
    