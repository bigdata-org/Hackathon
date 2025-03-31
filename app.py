from fastapi import FastAPI
from starlette.responses import StreamingResponse
import asyncio
import json
from utils.langgraph.core import entry_point, generate_report_with_streaming
import logging

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

app = FastAPI()

async def event_generator():
    messages = ["hi", "how are you"]
    for msg in messages:
        yield f"data: {msg}\n\n"  # SSE format
        await asyncio.sleep(1)  # Simulate delay

@app.get("/stream")
async def stream():
    with open('links.json', 'r', encoding='utf-8') as file:
        links_data = json.load(file)

    logger.info('app.py -> calling generate report')
    # llm_ready_data = entry_point(links_data)
    with open('llm_ready_data.json', 'r', encoding='utf-8') as file:
        llm_ready_data = json.load(file)
    # return llm_ready_data
    return StreamingResponse(generate_report_with_streaming(llm_ready_data), media_type="text/event-stream")