"""
LLM module using OpenRouter for text generation.
This is separate to allow for easy swapping of LLM providers.

Written by Jeremy Noesen
"""

from os import getenv
from openrouter import OpenRouter

# Log in to OpenRoter
openrouter = OpenRouter(api_key=getenv("OPENROUTER_API_KEY"))


async def write(prompt: str):
    """
    Respond to a prompt using OpenRouter nousresearch/hermes-4-70b
    :param prompt: Input text prompt
    :return: Model response string
    """

    # Get response to prompt
    response = await openrouter.chat.send_async(
        model="nousresearch/hermes-4-70b",
        max_tokens=700,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    return response.choices[0].message.content