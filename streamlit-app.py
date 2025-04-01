import time
import json
import requests
import streamlit as st

st.title("S&P 500 Research Report")
API_URL = "https://sp500-ra-451496260635.us-central1.run.app/report"

def stream_data(mode):
    params = {'mode':mode}
    response = requests.get(API_URL, params=params, stream=True)

    if response.status_code == 200:
        text_container = st.empty()  # Create a container for updating text
        accumulated_lines = []  # Store accumulated lines instead of words

        for chunk in response.iter_lines():
            if chunk:
                chunk_text = chunk.decode("utf-8")

                # Ensure paragraph breaks are maintained
                chunk_text = chunk_text.replace("\n", "\n\n")  

                # Append chunk as a new line
                accumulated_lines.append(chunk_text)

                # Update Streamlit container with joined text
                text_container.markdown("\n".join(accumulated_lines))  

                time.sleep(0.02)  # Simulate streaming delay

def batch_data(mode):
    params = {'mode':mode}
    response = requests.get(API_URL, params=params)
    if response.status_code == 200:
        markdown = json.loads(response.content.decode("utf-8"))['markdown']
        st.write(markdown)

mode = st.selectbox("Select Mode:", ["Static", "Realtime"], index=0)

if st.button("Stream LLM Response"):
    # stream_data()
    batch_data(mode)
