from litellm import completion, acompletion
from datetime import datetime
import asyncio, os, traceback

async def allm(model, system_prompt, user_prompt):
    messages = [{"role": "system", "content": system_prompt},{"role": "user", "content": user_prompt}]
    response =  await acompletion(
        model=model,
        messages=messages,
        temperature=0.7,
        stream=True
    )
    async for part in response:
        yield (part.choices[0].delta.content or "") + "\n"
            
def llm(model, system_prompt, user_prompt, is_json=False):
    messages = [{"role": "system", "content": system_prompt},{"role": "user", "content": user_prompt}]
    response = completion(
        model=model,
        response_format={ "type": "json_object" if is_json else "text" },
        messages=messages,
        temperature=0.7
        )
    return {'id':response.id,
            'prompt': user_prompt, 
            'answer': response.choices[0].message.content,
            'model' : response.model,
            'prompt_tokens': response.usage.prompt_tokens,
            'completion_tokens' : response.usage.completion_tokens,
            'created' : datetime.fromtimestamp(response.created).strftime('%Y-%m-%d %H:%M:%S')
            }