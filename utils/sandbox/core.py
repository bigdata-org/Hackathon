from dotenv import load_dotenv
import base64
from dotenv import load_dotenv
import pandas as pd
from e2b_code_interpreter import Sandbox
import json
from utils.litellm.core import llm
from utils.helper import sql_query_generation_prompt, python_code_generation_prompt
from utils.s3.core import upload_png_to_s3, get_s3_client
from utils.snowflake.core import write_to_csv
load_dotenv()

def python_sandbox(chart_metadata):
    chart_data = []
    for _ in chart_metadata:
        try:
            write_to_csv(_['SQL'].strip(';'))
            sbx = Sandbox()
            top_5_data = pd.read_csv('local/data.csv').head(5).to_string()
            with open("local/data.csv", "rb") as file:
                sbx.files.write("/home/user/sandbox/data.csv", file)
            result = llm(model='gemini/gemini-2.5-pro-exp-03-25', system_prompt=python_code_generation_prompt, user_prompt=top_5_data, is_json=True)['answer']
            code_to_run = json.loads(result)["code_to_run"] if isinstance(result,str) else result["code_to_run"]
            execution = sbx.run_code(code_to_run)
            img_bytes = base64.b64decode(execution.results[0].text)
            img_url=upload_png_to_s3(get_s3_client(), 'charts',img_bytes)
            chart_data.append( {'title' : _['Title'], 'description' : _['Description'], 'chart_url': img_url })
        except:
            pass
    return chart_data

