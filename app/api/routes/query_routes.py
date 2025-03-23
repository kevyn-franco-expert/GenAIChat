from fastapi import APIRouter, HTTPException

from app.api.models.query import QuestionRequest, QuestionResponse
from app.services.query_service import process_question
from app.core.exceptions import BadRequestException, InternalServerException

router = APIRouter()

@router.post("/ask", response_model=QuestionResponse, summary="Ask a question about CVs")
async def ask_question(request: QuestionRequest):
    """Ask a question about the uploaded CVs"""
    
    # Validate request
    if not request.question:
        raise BadRequestException(detail="Question is required")
    
    try:
        # Process the question
        answer = process_question(request.question)
        
        return {"question": request.question, "answer": answer}
    except Exception as e:
        raise InternalServerException(detail=f"Error processing your question: {str(e)}")