from dotenv import load_dotenv
import os
import base64
from io import StringIO
import snowflake.connector as sf
from dotenv import load_dotenv
import json
import pandas as pd
load_dotenv()

def sf_client():
    conn = sf.connect(
    user=os.getenv('SF_USER'),
    password=os.getenv('SF_PASSWORD'),
    account=os.getenv('SF_ACCOUNT'),
    warehouse=os.getenv('SF_WAREHOUSE'),
    database=os.getenv('SF_DATABASE'),
    schema=os.getenv('SF_SCHEMA'),
    role='FRED_ROLE',
    private_key_file = 'rsa_key.p8'
    )
    return conn

def write_to_csv(sql):
    conn = sf_client()
    cursor = conn.cursor()
    df = cursor.execute(sql).fetch_pandas_all()
    os.makedirs('local', exist_ok=True)
    df.to_csv(f'local/data.csv', index=False)
    return df
    