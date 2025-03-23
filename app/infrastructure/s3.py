import boto3
import os
import logging
from botocore.exceptions import ClientError

from app.core.config import settings
from app.core.exceptions import S3UploadException

logger = logging.getLogger(__name__)

# Initialize S3 client
s3_client = boto3.client(
    's3',
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_REGION
)

def upload_file_to_s3(file_path: str, object_name: str = None) -> str:
    """
    Upload a file to an S3 bucket
    
    Args:
        file_path: Path to the file to upload
        object_name: S3 object name (if None, file_path's basename will be used)
        
    Returns:
        S3 URI of the uploaded file
    
    Raises:
        S3UploadException: If upload fails
    """
    # If S3 object_name was not specified, use file_path's basename
    if object_name is None:
        object_name = os.path.basename(file_path)
    
    bucket_name = settings.S3_BUCKET_NAME
    
    try:
        # Check if bucket exists, create if not
        try:
            s3_client.head_bucket(Bucket=bucket_name)
        except ClientError:
            logger.info(f"Creating S3 bucket: {bucket_name}")
            # Create the bucket in the specified region
            s3_client.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={'LocationConstraint': settings.AWS_REGION}
            )
        
        # Upload file
        logger.info(f"Uploading file {file_path} to S3 bucket {bucket_name} as {object_name}")
        s3_client.upload_file(file_path, bucket_name, object_name)
        
        s3_uri = f"s3://{bucket_name}/{object_name}"
        logger.info(f"File uploaded successfully to {s3_uri}")
        
        return s3_uri
    
    except ClientError as e:
        error_message = f"Error uploading file to S3: {str(e)}"
        logger.error(error_message)
        raise S3UploadException(error_message)