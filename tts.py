"""
TTS module using AI Sponge Rehydrated's local text-to-speech system.
This is separate to allow for easy swapping of TTS providers.

Written by Jeremy Noesen
"""

from uuid import uuid4
from json import loads
from io import BytesIO
from aiohttp import ClientSession
from websockets import connect
from pydub import AudioSegment
from typing import Literal

# Characters dictionary with TTS system name and arpabet status for Standard and FakeYou TTS servers
characters_standard_fakeyou = {
    "SpongeBob": ("SpongeBob", True),
    "Patrick": ("Patrick", True),
    "Squidward": ("Loudward", True),
    "Sandy": ("Sandy", False),
    "Mr. Krabs": ("Mr Krabs (Clancy Brown)", False),
    "Plankton": ("Plankton v2 (Doug Lawrence)", True),
    "Mrs. Puff": ("Mrs Puff", False),
    "Larry": ("Larry", False),
    "Squilliam": ("Squilliam Fancyson", True),
    "Karen": ("Karen", True),
    "Narrator": ("The French Narrator (Tom Kenny)", True),
    "Bubble Buddy": ("BubbleBuddy-30", True),
    "Bubble Bass": ("Bubble Bass", True),
    "Perch Perkins": ("Perch Perkins", False),
    "Pearl": ("Pearl Krabs", False),
    "Mr. Fish": ("MrFish-30", True),
    "Flying Dutchman": ("Flying Dutchman", True),
    "King Neptune": ("KingNep", True),
    "Man Ray": ("Manray2025", True),
    "Dirty Bubble": ("DirtyBubble22", True)
}

# Characters dictionary with TTS system name and arpabet status for Uberduck TTS server
characters_uberduck = {
    "SpongeBob": ("Another_SpongeBob_test_Tacotron_2_model", True),
    "Patrick": ("Patrick", False),
    "Squidward": ("Squidward Tentacles_199_finalized", True),
    "Sandy": ("Sandy", False),
    "Mr. Krabs": ("Mr Krabs", False),
    "Plankton": ("Plankton v2 (Doug Lawrence)", True),
    "Mrs. Puff": ("Mrs Puff_99_finalized", True),
    "Larry": ("Larry", False),
}

# Base URLs of local TTS servers
url_http = "http://localhost"
url_ws = "ws://localhost"

# Ports for different TTS servers
port_standard = 8000
port_uberduck = 8001
port_fakeyou = 8002


async def speak(character: str, text: str, server: Literal["standard", "uberduck", "fakeyou"]):
    """
    Speak a line of text as a character using async I/O.
    :param character: Character voice to use
    :param text: Text to speak
    :param server: Which TTS server to use
    :return: AudioSegment of spoken text
    """

    # Select TTS server
    if server == "standard":
        port = port_standard
        characters = characters_standard_fakeyou
    elif server == "uberduck":
        port = port_uberduck
        characters = characters_uberduck
    elif server == "fakeyou":
        port = port_fakeyou
        characters = characters_standard_fakeyou

    # Connect to servers
    async with ClientSession() as session:
        async with connect(f"{url_ws}:{port}", ping_interval=10, ping_timeout=90, open_timeout=90) as socket:

            # Start synthesis job
            unique_id = str(uuid4())
            async with session.post(f"{url_http}:{port}/synthesize", json={
                "output_path": f"../Outputs/{unique_id}.wav",
                "voicemodel": characters[character][0],
                "text": text,
                "uuid": unique_id,
                "enable_arpa": characters[character][1]
            }) as resp:
                job_id = (await resp.json())["id"]

            # Wait for job to be ready via websocket
            while True:
                msg = loads(await socket.recv())
                if msg.get("id") == job_id:
                    if msg.get("status") == "ready":
                        await socket.close()
                        break
                    if msg.get("status") in ("failed", "removed"):
                        raise Exception(f"TTS job {job_id} status is either \"failed\" or \"removed\"")

            # Download audio file
            async with session.get(f"{url_http}:{port}/downloads/" + job_id) as resp:
                with BytesIO(await resp.read()) as wav:
                    seg = AudioSegment.from_wav(wav)

            # Delete file from server
            async with session.delete(f"{url_http}:{port}/remove/" + job_id):
                pass

    # Return pydub segment
    return seg