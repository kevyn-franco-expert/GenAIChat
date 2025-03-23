from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class CVMetadata(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    skills: Optional[List[str]] = None
    languages: Optional[List[str]] = None
    experience_years: Optional[float] = None
    job_titles: Optional[List[str]] = None
    education: Optional[str] = None

class CVDocument(BaseModel):
    id: str
    filename: str
    content: str
    metadata: CVMetadata

class CVUploadResponse(BaseModel):
    message: str