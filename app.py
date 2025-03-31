from fastapi import FastAPI
from pydantic import BaseModel
from starlette.responses import StreamingResponse
import asyncio
import json
from utils.s3.core import get_s3_client ,read_markdown_from_s3
from utils.langgraph.core import entry_point, generate_report_with_streaming, generate_report_without_streaming
import logging

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

app = FastAPI()

class modeModel(BaseModel):
    mode: str

@app.get("/report")
async def report(request: modeModel):
    mode = request.mode
    if mode=='Static':
        return {'markdown': read_markdown_from_s3(get_s3_client())}
    else: 
        with open('links.json', 'r', encoding='utf-8') as file:
            links_data = json.load(file)
        llm_ready_data = entry_point(links_data)
        with open('llm_ready_data.json', 'w') as file:
            file.write(json.dumps(llm_ready_data))
        return {'markdown': generate_report_without_streaming(llm_ready_data)}