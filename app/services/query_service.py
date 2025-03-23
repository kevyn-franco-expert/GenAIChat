import logging

from app.core.config import settings
from app.core.exceptions import AIServiceException
from app.infrastructure.vector_db import query_documents
from app.infrastructure.bedrock import query_llm as bedrock_query
from app.infrastructure.openai import query_llm as openai_query

logger = logging.getLogger(__name__)

def process_question(question: str) -> str:
    """
    Process a question about CVs and generate an answer
    
    Args:
        question: The question to answer
        
    Returns:
        The answer to the question
        
    Raises:
        AIServiceException: If processing fails
    """
    logger.info(f"Processing question: {question}")
    
    # Query the vector database
    results = query_documents(question, n_results=3)
    
    if not results["ids"][0]:
        logger.warning("No CV data found to answer the question")
        return "No CV data is available. Please upload CVs to the system first."
    
    # Prepare CV data for the LLM
    cv_context = ""
    for i, doc_id in enumerate(results["ids"][0]):
        metadata = results["metadatas"][0][i]
        cv_context += f"CV ID: {doc_id}\n"
        cv_context += f"Name: {metadata.get('name', 'Unknown')}\n"
        cv_context += f"Location: {metadata.get('location', 'Unknown')}\n"
        cv_context += f"Skills: {metadata.get('skills', 'Not specified')}\n"
        cv_context += f"Languages: {metadata.get('languages', 'Not specified')}\n"
        cv_context += f"Experience: {metadata.get('experience_years', 0)} years\n"
        cv_context += f"Job Titles: {metadata.get('job_titles', 'Not specified')}\n"
        cv_context += f"Education: {metadata.get('education', 'Not specified')}\n"
        cv_context += f"Content Preview: {results['documents'][0][i][:500]}...\n\n"
    
    # Create the prompt for the LLM
    prompt = f"""
    You are an AI assistant for a Human Resources department. Answer the following question 
    about job candidates based ONLY on the CV information provided below. If the information 
    needed to answer the question is not in the provided CVs, say that you don't have that 
    information. Always cite the specific candidates by name in your answer.
    
    CV Information:
    {cv_context}
    
    Question: {question}
    """
    
    try:
        # Query the appropriate LLM
        if settings.USE_OPENAI:
            logger.info("Using OpenAI for question answering")
            answer = openai_query(prompt)
        else:
            logger.info("Using Bedrock for question answering")
            answer = bedrock_query(prompt)
        
        logger.info("Successfully generated answer")
        return answer
    
    except Exception as e:
        error_message = f"Error processing question: {str(e)}"
        logger.error(error_message)
        raise AIServiceException(error_message)