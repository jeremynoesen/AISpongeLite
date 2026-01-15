"""
TTS module using AI Sponge Rehydrated's local text-to-speech system.
This is separate to allow for easy swapping of TTS providers.

Written by Jeremy Noesen
"""

from uuid import uuid4
from json import loads
from io import BytesIO
from aiohttp import ClientSession
from websockets import connect, ConnectionClosed
from pydub import AudioSegment

# Characters dictionary with TTS system name and arpabet status
characters = {
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
    "Perch": ("Perch Perkins", False),
    "Pearl": ("Pearl Krabs", False),
    "Mr. Fish": ("MrFish-30", True),
    "Dutchman": ("Flying Dutchman", True),
    "King Neptune": ("KingNep", True),
    "Man Ray": ("Manray2025", True),
    "Dirty Bubble": ("DirtyBubble22", True)
}

# Base URLs of local TTS server
http_url = "http://localhost:8000/"
ws_url = "ws://localhost:8000/"

# Whether to allow parallel requests
allow_parallel = True

# Character limits for input and output
char_limit_min = 1
char_limit_max = 512

# Bitrate for compressed output audio
bitrate = "320k"


async def speak(character: str, text: str):
    """
    Speak a line of text as a character using async I/O.
    :param character: Character voice to use
    :param text: Text to speak
    :return: AudioSegment of spoken text
    """

    # Connect to servers
    async with ClientSession() as session:
        async with connect(ws_url, ping_interval=10, ping_timeout=90, open_timeout=90) as socket:

            # Start synthesis job
            unique_id = str(uuid4())
            async with session.post(http_url + "synthesize", json={
                "output_path": f"../Outputs/{unique_id}.wav",
                "voicemodel": characters[character][0],
                "text": text,
                "uuid": unique_id,
                "enable_arpa": characters[character][1]
            }) as resp:
                job_id = (await resp.json())["id"]

            # Wait for job to be ready via websocket
            while True:
                try:
                    msg = loads(await socket.recv())
                    if msg.get("id") == job_id:
                        if msg.get("status") == "ready":
                            await socket.close()
                            break
                        if msg.get("status") in ("failed", "removed"):
                            raise Exception()
                except ConnectionClosed:
                    raise Exception()

            # Download audio file
            async with session.get(http_url + "downloads/" + job_id) as resp:
                with BytesIO(await resp.read()) as wav:
                    seg = AudioSegment.from_wav(wav)

            # Delete file from server
            async with session.delete(http_url + "remove/" + job_id):
                pass

    # Return pydub segment
    return seg