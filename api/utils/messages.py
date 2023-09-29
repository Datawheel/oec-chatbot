import json
import re
import time
from typing import List, Dict

import openai

from api.utils.logs import log_apicall


def get_assistant_message_from_openai(
        messages: List[Dict[str, str]],
        temperature: int = 0,
        model: str = "gpt-3.5-turbo",
        scope: str = "USA",
        purpose: str = "Generic",
        session_id: str = None,
        test_failure: bool = False,
        # model: str = "gpt-4",
):
    # alright, it looks like gpt-3.5-turbo is ignoring the user messages in history
    # let's go and re-create the chat in the last message!
    final_payload = messages

    start = time.time()
    try:
        if test_failure:
            raise Exception("Test failure")
        res = openai.ChatCompletion.create(
            model = model,
            temperature = 0,
            messages = final_payload
        )
    except Exception as e:
        duration = time.time() - start
        log_apicall(
            duration,
            'openai',
            model,
            0,
            0,
            scope,
            purpose,
            session_id = session_id,
            success=False,
            log_message = str(e),
        )
        raise e
    duration = time.time() - start

    usage = res['usage']
    input_tokens = usage['prompt_tokens']
    output_tokens = usage['completion_tokens']

    log_apicall(
        duration,
        'openai',
        model,
        input_tokens,
        output_tokens,
        scope,
        purpose,
        session_id = session_id,
    )

    # completion = res['choices'][0]["message"]["content"]
    assistant_message = res['choices'][0]
  
    return assistant_message


def call_chat(
        messages: List[Dict[str, str]],
        temperature: int = 0,
        model: str = "gpt-3.5-turbo",
        scope: str = "USA",
        purpose: str = "Generic",
        session_id: str = None,
        # model: str = "gpt-4",
):

    start = time.time()
    try:
        res = openai.ChatCompletion.create(
            model=model,
            temperature=temperature,
            messages=messages
        )
    except Exception as e:
        duration = time.time() - start
        log_apicall(
            duration,
            'openai',
            model,
            0,
            0,
            scope,
            purpose,
            session_id = session_id,
            success=False,
            log_message = str(e),
        )
        raise e

    duration = time.time() - start

    usage = res['usage']
    input_tokens = usage['prompt_tokens']
    output_tokens = usage['completion_tokens']

    log_apicall(
        duration,
        'openai',
        model,
        input_tokens,
        output_tokens,
        scope,
        purpose,
        session_id = session_id,
    )

    # completion = res['choices'][0]["message"]["content"]
    assistant_message = res['choices'][0]['message']['content']
  
    return assistant_message