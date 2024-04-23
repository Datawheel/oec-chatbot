import tiktoken

from typing import List, Dict, Any
from langchain.callbacks.base import BaseCallbackHandler
from langchain.schema import LLMResult

MODEL_COST_PER_1K_TOKENS = {
    # GPT-4 input
    "gpt-4": 0.03,
    "gpt-4-turbo": 0.01,
    "gpt-4-0314": 0.03,
    "gpt-4-0613": 0.03,
    "gpt-4-32k": 0.06,
    "gpt-4-32k-0314": 0.06,
    "gpt-4-32k-0613": 0.06,
    # GPT-4 output
    "gpt-4-completion": 0.06,
    "gpt-4-turbo-completion": 0.03,
    "gpt-4-0314-completion": 0.06,
    "gpt-4-0613-completion": 0.06,
    "gpt-4-32k-completion": 0.12,
    "gpt-4-32k-0314-completion": 0.12,
    "gpt-4-32k-0613-completion": 0.12,
    # GPT-3.5 input
    "gpt-3.5-turbo": 0.0015,
    "gpt-3.5-turbo-0301": 0.0015,
    "gpt-3.5-turbo-0613": 0.0015,
    "gpt-3.5-turbo-16k": 0.003,
    "gpt-3.5-turbo-16k-0613": 0.003,
    # GPT-3.5 output
    "gpt-3.5-turbo-completion": 0.002,
    "gpt-3.5-turbo-0301-completion": 0.002,
    "gpt-3.5-turbo-0613-completion": 0.002,
    "gpt-3.5-turbo-16k-completion": 0.004,
    "gpt-3.5-turbo-16k-0613-completion": 0.004,
    # Others
    "gpt-35-turbo": 0.002,  # Azure OpenAI version of ChatGPT
    "text-ada-001": 0.0004,
    "ada": 0.0004,
    "text-babbage-001": 0.0005,
    "babbage": 0.0005,
    "text-curie-001": 0.002,
    "curie": 0.002,
    "text-davinci-003": 0.02,
    "text-davinci-002": 0.02,
    "code-davinci-002": 0.02,
    "ada-finetuned": 0.0016,
    "babbage-finetuned": 0.0024,
    "curie-finetuned": 0.012,
    "davinci-finetuned": 0.12,
}

def standardize_model_name(
    model_name: str,
    is_completion: bool = False,
) -> str:
    """
    Standardize the model name to a format that can be used in the OpenAI API.

    Args:
        model_name: Model name to standardize.
        is_completion: Whether the model is used for completion or not.
            Defaults to False.

    Returns:
        Standardized model name.

    """
    model_name = model_name.lower()
    if "ft-" in model_name:
        return model_name.split(":")[0] + "-finetuned"
    elif is_completion and (
        model_name.startswith("gpt-4") or model_name.startswith("gpt-3.5")
    ):
        return model_name + "-completion"
    else:
        return model_name

def num_tokens_from_string(string: str, encoding_name: str) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.encoding_for_model(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens

def get_openai_token_cost_for_model(model_name: str, num_tokens: int, is_completion: bool = False) -> float:
    """
    Get the cost in USD for a given model and number of tokens.

    Args:
        model_name: Name of the model
        num_tokens: Number of tokens.
        is_completion: Whether the model is used for completion or not.
            Defaults to False.

    Returns:
        Cost in USD.
    """
    model_name = standardize_model_name(model_name, is_completion=is_completion)
    if model_name not in MODEL_COST_PER_1K_TOKENS:
        raise ValueError(
            f"Unknown model: {model_name}. Please provide a valid OpenAI model name."
            "Known models are: " + ", ".join(MODEL_COST_PER_1K_TOKENS.keys())
        )
    return MODEL_COST_PER_1K_TOKENS[model_name] * (num_tokens / 1000)


class TokenTrackingHandler(BaseCallbackHandler):
    total_tokens: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    successful_requests: int = 0
    total_cost: float = 0.0
    model_name: str = ""
    base_model_name: str = ""
    price_per_1k_tokens: float = 0.0
    price_per_1k_tokens_completion: float = 0.0
    prompt_tokens_increment: int = 0

    def __init__(self) -> None:
        super().__init__()

    def __repr__(self) -> str:
        return (
            f"Tokens Used: {self.total_tokens}\n"
            f"\tPrompt Tokens: {self.prompt_tokens}\n"
            f"\tCompletion Tokens: {self.completion_tokens}\n"
            f"Successful Requests: {self.successful_requests}\n"
            f"Total Cost (USD): ${self.total_cost}"
        )
    
    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str] | str | Dict[str, Any], **kwargs: Any) -> None:
        self.model_name=serialized['kwargs']['model_name']
        self.base_model_name = "gpt-4" if "gpt-4" in self.model_name else self.model_name.rpartition("-")[0]
        self.prompt_tokens_increment = num_tokens_from_string(prompts[0], self.base_model_name)
        self.prompt_tokens += self.prompt_tokens_increment
        self.price_per_1k_tokens = get_openai_token_cost_for_model(self.model_name, self.prompt_tokens)

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        if response.generations:
            for generation in response.generations[0]:
                aimessage = generation.message
                self.completion_tokens_increment =  num_tokens_from_string(aimessage.content, self.base_model_name)
                self.completion_tokens += self.completion_tokens_increment
                self.price_per_1k_tokens_completion = get_openai_token_cost_for_model(self.model_name, self.completion_tokens, is_completion=True)
        self.total_cost += self.price_per_1k_tokens + self.price_per_1k_tokens_completion
        self.total_tokens = self.prompt_tokens + self.completion_tokens
        self.successful_requests += 1