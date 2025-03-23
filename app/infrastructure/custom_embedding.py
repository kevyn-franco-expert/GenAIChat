from chromadb.utils.embedding_functions import EmbeddingFunction
import logging
from typing import List, Union

logger = logging.getLogger(__name__)


class CustomOpenAIEmbeddingFunction(EmbeddingFunction):
    """
    Custom implementation of OpenAI embedding function that works with the latest OpenAI SDK
    """

    def __init__(
        self,
        api_key: str,
        model_name: str = "text-embedding-ada-002",
        dimensions: int = 1536,
    ):
        """
        Initialize the OpenAI embedding function

        Args:
            api_key: OpenAI API key
            model_name: Name of the embedding model to use
            dimensions: Dimensions of the embedding vectors
        """
        self.api_key = api_key
        self.model_name = model_name
        self.dimensions = dimensions

        try:
            from openai import OpenAI

            self.client = OpenAI(api_key=api_key)
            logger.info(f"Initialized OpenAI client with model {model_name}")
        except ImportError:
            raise ImportError(
                "The OpenAI package is required to use the OpenAI embedding function"
            )
        except Exception as e:
            logger.error(f"Error initializing OpenAI client: {str(e)}")
            raise

    def __call__(self, input: List[str]) -> List[List[float]]:
        """
        Generate embeddings for the given input texts

        Args:
            input: List of texts to generate embeddings for

        Returns:
            List of embedding vectors
        """
        # Ensure input is a list
        if isinstance(input, str):
            input = [input]

        try:

            try:
                response = self.client.embeddings.create(
                    model=self.model_name, input=input
                )
            except Exception as dim_error:
                logger.warning(f"No dimetions supported: {str(dim_error)}")

            embeddings = [data.embedding for data in response.data]
            return embeddings

        except Exception as e:
            logger.error(f"Error generating embeddings with OpenAI: {str(e)}")
            return [[0.0] * self.dimensions for _ in input]
