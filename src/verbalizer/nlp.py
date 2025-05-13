import logging
from abc import ABC, abstractmethod
from typing import Optional

try:
    from openai import OpenAI

    logging.getLogger("openai").setLevel(logging.ERROR)
    logging.getLogger("httpx").setLevel(logging.ERROR)
except ModuleNotFoundError as err:
    OpenAI = None


class ParaphraseLanguageModel(ABC):

    @abstractmethod
    def pseudo_to_text(self, pseudo_text: str, extra: str = None) -> str:
        """
        Given a pseudo text or controlled natural language, return a rephrased version of that same text.
        :param pseudo_text: The CNL set of statements,
        :param extra: Additional context to include as part of the prompt.
        :return: Paraphrased text.
        """
        return pseudo_text

    @property
    def cost(self) -> float:
        """
        The usage cost so far of the model.
        """
        return 0.0

    @property
    def name(self) -> str:
        """
        The name of the model used.
        """
        return 'Unknown'


def get_messages(pseudo_text: str, extra_context: Optional[str] = None):
    """
    Get messages (system, assistant, user)
    """
    extra = extra_context if extra_context else ""
    return [
        {
            "role": "system",
            "content": f"You are an extremely specific data expert capable of converting pseudo English sentences "
                       f"into a meaningful and casual paragraph without losing information. Avoid repeating "
                       f"information. Spell out everything don't be lazy! {extra}"
        },
        {
            "role": "user", "content":
            """
            x relation 1 y
            z relation 2 x
            m relation 3 n
            """
        },
        {
            "role": "assistant", "content":
            """
            X has this relation 1 with Y, Z shares a relation 2 with X.
            Moreover, m has relation 3 with n.
            """
        },
        {"role": "user", "content": "X is same as something that intersection of something that something that has at "
                                    "least 3 N and M."},
        {"role": "assistant", "content": "X is the same as M which has at least three N"},
        {"role": "user", "content":
            """
            X is a type of at least has Y relation some a M.
            X is a type of at least has Y relation some a N.
            X is a type of only has Y relation any of (a M and a N)
            """
         },
        {"role": "assistant", "content": "X has Y relation with M and N and nothing else."},
        {"role": "user", "content": pseudo_text},
    ]


class ChatGptModelParaphrase(ParaphraseLanguageModel):
    """
    OpenAI wrapper implementation.
    """

    models = {
        "gpt-4o": {
            "input": 0.005,
            "output": 0.015
        },
        "gpt-4-0125-preview": {
            "input": 0.01,
            "output": 0.03
        },
        "gpt-4-1106-preview": {
            "input": 0.01,
            "output": 0.03
        },
        "gpt-4-1106-vision-preview": {
            "input": 0.01,
            "output": 0.03
        },
        "gpt-4": {
            "input": 0.03,
            "output": 0.06
        },
        "gpt-4-0613": {
            "input": 0.03,
            "output": 0.06
        },
        "gpt-4-32k": {
            "input": 0.06,
            "output": 0.12
        },
        "gpt-3.5-turbo-0125": {
            "input": 0.0005,
            "output": 0.0015
        },
        "gpt-3.5-turbo-instruct": {
            "input": 0.0015,
            "output": 0.0020
        },
        "gpt-3.5-turbo-16k-0613": {
            "input": 0.0030,
            "output": 0.0040
        },
        "gpt-3.5-turbo-1106": {
            "input": 0.0010,
            "output": 0.0020
        },
        "gpt-3.5-turbo-0613": {
            "input": 0.0015,
            "output": 0.0020
        },
        "gpt-3.5-turbo-0301": {
            "input": 0.0015,
            "output": 0.0020
        }
    }

    def __init__(self, api_key: str, model: str = 'gpt-3.5-turbo-0613', temperature=0.5):
        if not OpenAI:
            raise ModuleNotFoundError("OpenAI is not installed. Please install it with `pip install openai`")

        self.model = model
        self.temperature = temperature
        self.client = OpenAI(api_key=api_key)
        self._in_token_usage = 0
        self._out_token_usage = 0

    def pseudo_to_text(self, pseudo_text: str, extra: str = None) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=get_messages(pseudo_text, extra),
            temperature=self.temperature
        )
        self._in_token_usage += response.usage.prompt_tokens
        self._out_token_usage += response.usage.completion_tokens
        return response.choices[0].message.content

    @property
    def cost(self) -> float:
        model_pricing = self.models.get(self.model) or {'input': 0.0, 'output': 0.0}

        in_tokens = self._in_token_usage / 1000
        out_tokens = self._out_token_usage / 1000

        return in_tokens * model_pricing['input'] + out_tokens * model_pricing["output"]

    @property
    def name(self) -> str:
        return self.model
