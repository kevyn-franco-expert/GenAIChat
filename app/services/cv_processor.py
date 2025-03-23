import os
import uuid
import tempfile
import shutil
import logging
import pypdf
from fastapi import UploadFile

from app.core.config import settings
from app.core.exceptions import CVProcessingException
from app.infrastructure.s3 import upload_file_to_s3
from app.infrastructure.vector_db import add_document
from app.infrastructure.bedrock import extract_metadata as bedrock_extract_metadata
from app.infrastructure.openai import extract_metadata as openai_extract_metadata

logger = logging.getLogger(__name__)

def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text from a PDF file
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        Extracted text
        
    Raises:
        CVProcessingException: If text extraction fails
    """
    text = ""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = pypdf.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
                
        if not text.strip():
            logger.warning(f"Extracted empty text from {file_path}")
            
        return text
    
    except Exception as e:
        error_message = f"Error extracting text from PDF: {str(e)}"
        logger.error(error_message)
        raise CVProcessingException(error_message)

def process_cv_file(file: UploadFile):
    """
    Process an uploaded CV file
    
    Args:
        file: The uploaded file
        
    Raises:
        CVProcessingException: If processing fails
    """
    # Create a temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    temp_file_path = temp_file.name
    temp_file.close()
    
    try:
        # Save the upload file to the temporary file
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"Processing CV: {file.filename}")
        
        # Extract text from the PDF
        text = extract_text_from_pdf(temp_file_path)
        
        # Extract metadata using AI service
        if settings.USE_OPENAI:
            metadata = openai_extract_metadata(text)
        else:
            metadata = bedrock_extract_metadata(text)
        
        # Add filename to metadata
        metadata["filename"] = file.filename
        
        # Create a unique ID for the document
        doc_id = str(uuid.uuid4())
        
        # Add to vector database
        add_document(text, metadata, doc_id)
        
        # Upload to S3 (optional)
        try:
            s3_path = upload_file_to_s3(temp_file_path, file.filename)
            logger.info(f"Uploaded to S3: {s3_path}")
        except Exception as e:
            logger.warning(f"S3 upload failed, but continuing: {str(e)}")
        
        logger.info(f"Successfully processed CV: {file.filename}")
        
    except Exception as e:
        error_message = f"Error processing CV: {str(e)}"
        logger.error(error_message)
        raise CVProcessingException(error_message)
    
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            logger.debug(f"Removed temporary file: {temp_file_path}")