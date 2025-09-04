"""
TTS module using FakeYou for text-to-speech synthesis. This is separate to allow for easy swapping of TTS providers.

Written by Jeremy Noesen
"""

from asyncio import sleep, wait_for, get_running_loop
from io import BytesIO
from fakeyou import FakeYou
from pydub import AudioSegment

# Log in to FakeYou
fakeyou = FakeYou()

# Set the FakeYou timeout before a line fails
fakeyou_timeout = 90

# Characters dictionary with their model tokens
characters = {
    "spongebob": "weight_5by9kjm8vr8xsp7abe8zvaxc8",
    "patrick": "weight_154man2fzg19nrtc15drner7t",
    "squidward": "TM:3psksme51515",
    "mr. krabs": "weight_5bxbp9xqy61svfx03b25ezmwx",
    "plankton": "weight_ahxbf2104ngsgyegncaefyy6j",
    "karen": "weight_eckp92cd68r4yk68n6re3fwcb",
    "sandy": "TM:214sp1nxxd63",
    "mrs. puff": "weight_129qhgze57zhndkkcq83e6b2a",
    "larry": "weight_k7qvaffwsft6vxbcps4wbyj58",
    "squilliam": "weight_zmjv8223ed6wx1fp234c79v9s",
    "bubble bass": "weight_h9g7rh6tj2hvfezrz8gjs4gwa",
    "bubble buddy": "weight_sbr0372ysxbdahcvej96axy1t",
    "realistic fish head": "weight_m1a1yqf9f2v8s1evfzcffk4k0",
    "french narrator": "weight_edzcfmq6y0vj7pte9pzhq5b6j"
}

async def speak(character: str, text: str):
    """
    Speak a line of text as a character using FakeYou TTS.
    :param character: Character voice to use
    :param text: Text to speak
    :return: AudioSegment of spoken text
    """

    # Attempt to speak line
    try:
        with BytesIO((await wait_for(get_running_loop().run_in_executor(None, fakeyou.say, text, characters[character]), fakeyou_timeout)).content) as wav:
            return AudioSegment.from_wav(wav)

    # Line failed to generate
    except Exception as e:
        raise e

    # Avoid rate limiting
    finally:
        await sleep(10)