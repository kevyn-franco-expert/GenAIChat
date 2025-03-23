from fastapi import HTTPException
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND, HTTP_500_INTERNAL_SERVER_ERROR

class CVProcessingException(Exception):
    """Exception raised when processing a CV fails"""
    pass

class S3UploadException(Exception):
    """Exception raised when uploading to S3 fails"""
    pass

class AIServiceException(Exception):
    """Exception raised when AI service calls fail"""
    pass

class VectorDBException(Exception):
    """Exception raised when vector database operations fail"""
    pass

class NotFoundException(HTTPException):
    """Exception raised when a resource is not found"""
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=HTTP_404_NOT_FOUND, detail=detail)

class BadRequestException(HTTPException):
    """Exception raised for bad request errors"""
    def __init__(self, detail: str = "Bad request"):
        super().__init__(status_code=HTTP_400_BAD_REQUEST, detail=detail)

class InternalServerException(HTTPException):
    """Exception raised for internal server errors"""
    def __init__(self, detail: str = "Internal server error"):
        super().__init__(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)