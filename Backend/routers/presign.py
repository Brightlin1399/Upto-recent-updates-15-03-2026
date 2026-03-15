"""Presigned upload for MinIO so the frontend can upload attachment files (Summary, Escalation)."""
import time
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

# MinIO / S3-compatible config. Port 9000 = API (uploads); 9001 = Web Console (browser UI).
# Override via env if your MinIO uses different ports.
import os
BUCKET = os.environ.get("MINIO_BUCKET", "price-tool-attachments")
REGION = os.environ.get("MINIO_REGION", "us-east-1")
MINIO_API_ENDPOINT = os.environ.get("MINIO_ENDPOINT", "http://127.0.0.1:9000")  # API port (boto3 + presigned URLs)
ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
SECRET_KEY = os.environ.get("MINIO_SECRET_KEY", "minioadmin")

try:
    import boto3
    _s3 = boto3.client(
        "s3",
        endpoint_url=MINIO_API_ENDPOINT,
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
        region_name=REGION,
    )
except Exception:
    _s3 = None


class PresignRequest(BaseModel):
    filename: str
    content_type: str = "application/octet-stream"


class PresignResponse(BaseModel):
    uploadUrl: str
    fileUrl: str


@router.post("/presign-upload", response_model=PresignResponse)
def presign_upload(body: PresignRequest):
    """Return a presigned PUT URL and the final file URL. Frontend PUTs the file to uploadUrl, then sends fileUrl in PCR submit."""
    if _s3 is None:
        raise RuntimeError("boto3 not installed or MinIO client failed. pip install boto3.")
    key = f"pcr-attachments/{int(time.time())}-{body.filename}"
    upload_url = _s3.generate_presigned_url(
        "put_object",
        Params={"Bucket": BUCKET, "Key": key, "ContentType": body.content_type},
        ExpiresIn=600,
    )
    file_url = f"{MINIO_API_ENDPOINT}/{BUCKET}/{key}"
    return PresignResponse(uploadUrl=upload_url, fileUrl=file_url)
