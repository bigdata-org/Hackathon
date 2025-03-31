import time
import requests
import streamlit as st

st.title("Streaming from FastAPI")
API_URL = "http://127.0.0.1:8000/stream"

def stream_data():
    response = requests.get(API_URL, stream=True)

    if response.status_code == 200:
        text_container = st.empty()  # Create a container for updating text
        accumulated_lines = []  # Store accumulated lines instead of words

        for chunk in response.iter_lines():
            if chunk:
                chunk_text = chunk.decode("utf-8").strip()

                # Ensure paragraph breaks are maintained
                chunk_text = chunk_text.replace("\n", "\n\n")  

                # Append chunk as a new line
                accumulated_lines.append(chunk_text)

                # Update Streamlit container with joined text
                text_container.write("\n".join(accumulated_lines))  

                time.sleep(0.02)  # Simulate streaming delay

if st.button("Stream LLM Response"):
    stream_data()
