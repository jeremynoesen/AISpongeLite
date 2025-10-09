"""
GPT module using OpenAI for text generation.
This is separate to allow for easy swapping of GPT providers.

Written by Jeremy Noesen
"""

from os import getenv
from openai import AsyncOpenAI

# Log in to OpenAI
openai = AsyncOpenAI(api_key=getenv("OPENAI_API_KEY"))


async def respond(prompt: str):
    """
    Respond to a prompt using OpenAI gpt-3.5-turbo-instruct.
    :param prompt: Input text prompt
    :return: Model response string
    """

    # Get response to prompt
    completion = await openai.completions.create(
        model="gpt-3.5-turbo-instruct",
        max_tokens=700,
        prompt=prompt
    )
    return completion.choices[0].text