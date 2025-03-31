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

def write_markdown_to_s3(s3_client, markdown_content: str):
    try:
        bucket_name, aws_region = os.getenv("BUCKET_NAME"), os.getenv("AWS_REGION")
        if bucket_name is None or aws_region is None:
            return -1  # Return error code if env variables are missing
        
        file_name = "report/static.md"
        s3_client.put_object(
            Bucket=bucket_name,
            Key=file_name,
            Body=markdown_content.encode("utf-8"),
            ContentType="text/markdown"
        )
        
        object_url = f"https://{bucket_name}.s3.{aws_region}.amazonaws.com/{file_name}"
        return object_url  # Return the uploaded file URL
    except Exception as e:
        return e  # Return the exception if an error occurs
    
def read_markdown_from_s3(s3_client, key='report/static.md'):
    try:
        bucket_name = os.getenv("BUCKET_NAME")
        if not bucket_name:
            return "Error: BUCKET_NAME environment variable not set."

        response = s3_client.get_object(Bucket=bucket_name, Key=key)
        markdown_content = response['Body'].read().decode('utf-8')  # Decode the Markdown content

        return markdown_content
    except Exception as e:
        return f"Error reading Markdown from S3: {str(e)}"