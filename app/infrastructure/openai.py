import json
import logging
from typing import List

from app.core.config import settings
from app.core.exceptions import AIServiceException

logger = logging.getLogger(__name__)

# Initialize OpenAI client
try:
    from openai import OpenAI

    client = OpenAI(api_key=settings.OPENAI_API_KEY)
except ImportError:
    logger.error(
        "OpenAI package not installed. Please install it with 'pip install openai'."
    )
    client = None
except Exception as e:
    logger.error(f"Error initializing OpenAI client: {str(e)}")
    client = None


def generate_embeddings(text: str) -> List[float]:
    """
    Generate embedding vectors for a text using OpenAI

    Args:
        text: The text to generate embeddings for

    Returns:
        List of embedding values

    Raises:
        AIServiceException: If the embedding generation fails
    """
    try:
        try:
            response = client.embeddings.create(
                model="text-embedding-ada-002",
                input=text,
            )
        except Exception as dim_error:
            logger.warning(
                f"Model does not support dimensions, using standard method: {str(dim_error)}"
            )

        return response.data[0].embedding

    except Exception as e:
        error_message = f"Error generating embeddings with OpenAI: {str(e)}"
        logger.error(error_message)
        raise AIServiceException(error_message)


def extract_metadata(text: str) -> dict:
    """
    Extract structured metadata from CV text using OpenAI

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
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that extracts structured information from CVs.",
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
        )

        return json.loads(response.choices[0].message.content)

    except Exception as e:
        error_message = f"Error extracting metadata with OpenAI: {str(e)}"
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
        "education": [],
    }


def query_llm(prompt: str) -> str:
    """
    Query the LLM with the given prompt using OpenAI

    Args:
        prompt: The prompt to send to the LLM

    Returns:
        The LLM's response

    Raises:
        AIServiceException: If the LLM query fails
    """
    try:
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant for HR."},
                {"role": "user", "content": prompt},
            ],
        )

        return response.choices[0].message.content

    except Exception as e:
        error_message = f"Error querying OpenAI LLM: {str(e)}"
        logger.error(error_message)
        raise AIServiceException(error_message)
