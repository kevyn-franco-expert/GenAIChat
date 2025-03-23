import chromadb
import logging
from chromadb.utils import embedding_functions
from typing import List, Dict, Any

from app.core.config import settings
from app.core.exceptions import VectorDBException
from app.api.models.cv import CVDocument, CVMetadata
from app.infrastructure.bedrock import generate_embeddings as bedrock_embeddings
from app.infrastructure.custom_embedding import CustomOpenAIEmbeddingFunction

logger = logging.getLogger(__name__)

# Global variables for ChromaDB client and collection
chroma_client = None
collection = None


def init_vector_db():
    """Initialize the ChromaDB client and collection"""
    global chroma_client, collection

    try:
        logger.info(f"Initializing ChromaDB with directory: {settings.VECTOR_DB_DIR}")

        # Initialize ChromaDB client
        chroma_client = chromadb.PersistentClient(path=settings.VECTOR_DB_DIR)

        # Configure the embedding function
        if settings.USE_OPENAI:
            logger.info("Using OpenAI embedding function with custom implementation")
            embedding_function = CustomOpenAIEmbeddingFunction(
                api_key=settings.OPENAI_API_KEY, model_name="text-embedding-ada-002"
            )
        else:
            logger.info("Using Bedrock embedding function")

            # Custom embedding function for Amazon Bedrock
            class BedrockEmbeddingFunction(embedding_functions.EmbeddingFunction):
                def __init__(self):
                    pass
                
                def __call__(self, input):
                    embeddings = []
                    for text in input:
                        embedding = bedrock_embeddings(text)
                        embeddings.append(embedding)
                    return embeddings

            embedding_function = BedrockEmbeddingFunction()

        # Get or create collection
        try:
            logger.info(f"Getting collection: {settings.COLLECTION_NAME}")
            collection = chroma_client.get_collection(
                name=settings.COLLECTION_NAME, embedding_function=embedding_function
            )
            logger.info(
                f"Found existing collection with {collection.count()} documents"
            )
        except Exception as e:
            logger.info(f"Creating new collection: {settings.COLLECTION_NAME}")
            collection = chroma_client.create_collection(
                name=settings.COLLECTION_NAME, embedding_function=embedding_function
            )
            logger.info("Collection created successfully")

    except Exception as e:
        error_message = f"Error initializing vector database: {str(e)}"
        logger.error(error_message)
        raise VectorDBException(error_message)


def add_document(text: str, metadata: Dict[str, Any], doc_id: str):
    """
    Add a document to the vector database

    Args:
        text: The document text
        metadata: Document metadata
        doc_id: Unique document ID

    Raises:
        VectorDBException: If adding the document fails
    """
    global collection

    if collection is None:
        init_vector_db()

    try:
        # Format metadata for ChromaDB
        chroma_metadata = {
            "filename": metadata.get("filename", "Unknown"),
            "name": metadata.get("name", "Unknown"),
            "location": metadata.get("location", "Unknown"),
            "skills": ", ".join(metadata.get("skills", [])),
            "languages": ", ".join(metadata.get("languages", [])),
            "experience_years": metadata.get("experience_years", 0),
            "job_titles": ", ".join(metadata.get("job_titles", [])),
            "education": metadata.get("education", ""),
        }

        # Add to ChromaDB
        collection.add(documents=[text], metadatas=[chroma_metadata], ids=[doc_id])

        logger.info(f"Added document {doc_id} to vector database")

    except Exception as e:
        error_message = f"Error adding document to vector database: {str(e)}"
        logger.error(error_message)
        raise VectorDBException(error_message)


def query_documents(query_text: str, n_results: int = 5):
    """
    Query the vector database for documents matching the query

    Args:
        query_text: The query text
        n_results: Number of results to return

    Returns:
        Query results from ChromaDB

    Raises:
        VectorDBException: If querying fails
    """
    global collection

    if collection is None:
        init_vector_db()

    try:
        results = collection.query(query_texts=[query_text], n_results=n_results)

        return results

    except Exception as e:
        error_message = f"Error querying vector database: {str(e)}"
        logger.error(error_message)
        raise VectorDBException(error_message)


def get_all_cvs() -> List[CVDocument]:
    """
    Get all CVs from the vector database

    Returns:
        List of CVDocument objects

    Raises:
        VectorDBException: If retrieval fails
    """
    global collection

    if collection is None:
        init_vector_db()

    try:
        # Get all documents from ChromaDB
        results = collection.get()

        cvs = []
        for i, doc_id in enumerate(results["ids"]):
            metadata = results["metadatas"][i]

            # Parse metadata
            cv_metadata = CVMetadata(
                name=metadata.get("name", "Unknown"),
                location=metadata.get("location", "Unknown"),
                skills=(
                    metadata.get("skills", "").split(", ")
                    if metadata.get("skills")
                    else []
                ),
                languages=(
                    metadata.get("languages", "").split(", ")
                    if metadata.get("languages")
                    else []
                ),
                experience_years=float(metadata.get("experience_years", 0)),
                job_titles=(
                    metadata.get("job_titles", "").split(", ")
                    if metadata.get("job_titles")
                    else []
                ),
                education=metadata.get("education", ""),
            )

            cv = CVDocument(
                id=doc_id,
                filename=metadata.get("filename", "Unknown"),
                content=results["documents"][i],
                metadata=cv_metadata,
            )
            cvs.append(cv)

        return cvs

    except Exception as e:
        error_message = f"Error retrieving CVs from vector database: {str(e)}"
        logger.error(error_message)
        raise VectorDBException(error_message)
