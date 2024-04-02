import json

from typing import List

from src.config import FEW_SHOT_PATH

few_shot_examples = {}
with open(FEW_SHOT_PATH, "r") as f:
    few_shot_examples = json.load(f)

def get_few_shot_example_messages(mode: str = "table_selection", n=-1) -> List[dict]:
    examples = few_shot_examples.get("USA", {}).get(mode, [])
    if n > 0:
        examples = examples[:n]
    if n == 0:
        examples = []
    messages = []
    for example in examples:
        messages.append({
            "role": "user",
            "content": example["user"],
        })
        messages.append({
            "role": "assistant",
            "content": example["assistant"],
        })
    return messages