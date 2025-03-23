import boto3
import json
import logging
from botocore.exceptions import ClientError

from app.core.config import settings
from app.core.exceptions import AIServiceException

logger = logging.getLogger(__name__)

# Initialize Bedrock client
bedrock_client = boto3.client(
    'bedrock-runtime',
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_REGION
)

def generate_embeddings(text: str) -> list:
    """
    Generate embedding vectors for a text using Amazon Bedrock
    
    Args:
        text: The text to generate embeddings for
        
    Returns:
        List of embedding values
        
    Raises:
        AIServiceException: If the embedding generation fails
    """
    try:
        response = bedrock_client.invoke_model(
            modelId=settings.BEDROCK_EMBEDDING_MODEL,
            contentType="application/json",
            accept="application/json",
            body=json.dumps({
                "inputText": text
            })
        )
        
        response_body = json.loads(response['body'].read())
        return response_body['embedding']
    
    except ClientError as e:
        error_message = f"Error generating embeddings: {str(e)}"
        logger.error(error_message)
        raise AIServiceException(error_message)

def extract_metadata(text: str) -> dict:
    """
    Extract structured metadata from CV text using Bedrock
    
    Args:
        text: The CV text to extract metadata from
        
    Returns:
        Dictionary containing extracted metadata
        
    Raises:
        AIServiceException: If the metadata extraction fails
    """
    # Create prompt for metadata extraction
    prompt = f"""
    Extract the following structured information from this CV:
    - Name
    - Location (city and country)
    - Skills (technical and soft skills)
    - Languages (spoken languages and proficiency)
    - Experience (years of total professional experience)
    - Job titles (all job titles mentioned)
    - Education (degrees and institutions)

    Return the information as a JSON object with these fields.
    
    CV Text:
    {text[:4000]}  # Limit text length to avoid token limits
    """
    
    try:
        response = bedrock_client.invoke_model(
            modelId=settings.BEDROCK_MODEL_ID,
            contentType="application/json",
            accept="application/json",
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            })
        )
        
        response_body = json.loads(response['body'].read())
        
        # Extract JSON from the response
        ai_message = response_body['content'][0]['text']
        
        # Find JSON in the response
        json_start = ai_message.find('{')
        json_end = ai_message.rfind('}') + 1
        if json_start >= 0 and json_end > json_start:
            metadata_json = ai_message[json_start:json_end]
            return json.loads(metadata_json)
    
    except (ClientError, json.JSONDecodeError) as e:
        error_message = f"Error extracting metadata: {str(e)}"
        logger.error(error_message)
        
        # Return default metadata
        logger.info("Using default metadata")
        
    # Default metadata if extraction fails
    return {
        "name": "Unknown",
        "location": "Unknown",
        "skills": [],
        "languages": [],
        "experience_years": 0,
        "job_titles": [],
        "education": []
    }

def query_llm(prompt: str) -> str:
    """
    Query the LLM with the given prompt
    
    Args:
        prompt: The prompt to send to the LLM
        
    Returns:
        The LLM's response
        
    Raises:
        AIServiceException: If the LLM query fails
    """
    try:
        response = bedrock_client.invoke_model(
            modelId=settings.BEDROCK_MODEL_ID,
            contentType="application/json",
            accept="application/json",
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            })
        )
        
        response_body = json.loads(response['body'].read())
        return response_body['content'][0]['text']
    
    except ClientError as e:
        error_message = f"Error querying LLM: {str(e)}"
        logger.error(error_message)
        raise AIServiceException(error_message)