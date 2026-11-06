"""
Module that uses OpenRouter for text generation.
"""

from os import getenv
from openrouter import OpenRouter

# Log in to OpenRoter
openrouter = OpenRouter(api_key=getenv("OPENROUTER_API_KEY"))


async def write(prompt: str):
    """
    Respond to a prompt using OpenRouter
    :param prompt: Input text prompt
    :return: Model response string
    """

    # Get response to prompt
    response = await openrouter.chat.send_async(
        model="sao10k/l3-lunaris-8b",
        max_tokens=700,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    return response.choices[0].message.content