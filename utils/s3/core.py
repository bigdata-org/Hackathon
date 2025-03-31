import os
import boto3
from uuid import uuid4
import pandas as pd

def get_s3_client():
    try:
        s3_client = boto3.client(
        's3', 
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"), 
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_REGION")  
        )
        return s3_client
    except:
        return -1
    
def upload_png_to_s3(s3_client, key, file_bytes: bytes):
    try:
        bucket_name, aws_region = os.getenv("BUCKET_NAME"), os.getenv('AWS_REGION')
        if bucket_name is None or aws_region is None:
            return -1
        file_name = f"{key}/{uuid4()}.png"
        s3_client.put_object(Bucket=bucket_name, Key=file_name, Body=file_bytes, ContentType='image/png')
        object_url = f"https://{bucket_name}.s3.{aws_region}.amazonaws.com/{file_name}"
        return object_url
    except Exception as e:
        return e