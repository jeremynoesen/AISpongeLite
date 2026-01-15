"""
TTS module using FakeYou for text-to-speech synthesis.
This is separate to allow for easy swapping of TTS providers.

Written by Jeremy Noesen
"""

from os import getenv
from asyncio import sleep, wait_for, get_running_loop
from io import BytesIO
from fakeyou import FakeYou
from pydub import AudioSegment

# Log in to FakeYou
fakeyou = FakeYou()
fakeyou_username = getenv("FAKEYOU_USERNAME")
fakeyou_password = getenv("FAKEYOU_PASSWORD")
if fakeyou_username and fakeyou_password:
    fakeyou.login(fakeyou_username, fakeyou_password)

# Set the FakeYou timeout before a line fails
fakeyou_timeout = 90

# Characters dictionary with their model tokens
characters = {
    "SpongeBob": "weight_5by9kjm8vr8xsp7abe8zvaxc8",
    "Patrick": "weight_154man2fzg19nrtc15drner7t",
    "Squidward": "TM:3psksme51515",
    "Sandy": "TM:214sp1nxxd63",
    "Mr. Krabs": "weight_5bxbp9xqy61svfx03b25ezmwx",
    "Plankton": "weight_ahxbf2104ngsgyegncaefyy6j",
    "Mrs. Puff": "weight_129qhgze57zhndkkcq83e6b2a",
    "Larry": "weight_k7qvaffwsft6vxbcps4wbyj58",
    "Squilliam": "weight_zmjv8223ed6wx1fp234c79v9s",
    "Karen": "weight_eckp92cd68r4yk68n6re3fwcb",
    "Narrator": "weight_edzcfmq6y0vj7pte9pzhq5b6j",
    "Bubble Buddy": "weight_sbr0372ysxbdahcvej96axy1t",
    "Bubble Bass": "weight_h9g7rh6tj2hvfezrz8gjs4gwa",
    "Mr. Fish": "weight_m1a1yqf9f2v8s1evfzcffk4k0",
    "King Neptune": "weight_hmf2eqzj1zja1yww4zeya0cnm",
    "Dirty Bubble": "weight_f7nm9e4sx49gjjknc2mgb9ggs"
}

# Whether to allow parallel requests
allow_parallel = False

# Character limits for input and output
char_limit_min = 3
char_limit_max = 256

# Bitrate for compressed output audio
bitrate = "256k"


async def speak(character: str, text: str):
    """
    Speak a line of text as a character using FakeYou TTS.
    :param character: Character voice to use
    :param text: Text to speak
    :return: AudioSegment of spoken text
    """

    # Attempt to speak line
    try:
        output = await wait_for(get_running_loop().run_in_executor(None, fakeyou.say, text, characters[character]), fakeyou_timeout)
        with BytesIO(output.content) as wav:
            return AudioSegment.from_wav(wav)

    # Line failed to generate
    except Exception as e:
        raise e

    # Avoid rate limiting
    finally:
        await sleep(10)