"""
AI Sponge Lite is a Discord bot that generates parody AI Sponge audio episodes, chats, and TTS inspired by
[AI Sponge Rehydrated](https://aisponge.riskivr.com/).

Written by Jeremy Noesen
"""

from typing import Literal
from random import randint, randrange, choice, choices
from re import sub, fullmatch, split
from math import ceil
from io import BytesIO
from os import getenv, listdir
from dotenv import load_dotenv
from discord import Status, Embed, Interaction, Color, Game, Intents, Client, File
from discord.utils import escape_markdown
from discord.app_commands import CommandTree, Range, describe, allowed_installs, allowed_contexts
from pydub import AudioSegment

# Load .env
load_dotenv()

# Load TTS and GPT modules
from tts import speak, allow_parallel, char_limit_min, char_limit_max, bitrate
from llm import write

# Discord activity settings
activity_ready = Game("Ready!")
activity_generating = Game("Generating...")

# Initialize Discord client
client = Client(intents=Intents.default(), activity=Game("Initializing..."), status=Status.idle)
command_tree = CommandTree(client)

# Logging channel
logging_channel = None

# Embed settings and static embeds
embed_color = Color.dark_theme()
embed_delete_after = 5
embed_episode_start = Embed(title="Generating...", description="Writing script...", color=embed_color)
embed_episode_end = Embed(title="Generating...", description="Mixing audio...", color=embed_color)
embed_tts = Embed(title="Generating...", description="Speaking text...", color=embed_color)
embed_chat = Embed(title="Generating...", description="Writing response...", color=embed_color)
embed_failed = Embed(title="Failed.", description="An error occurred.", color=embed_color)
embed_in_use = Embed(title="Busy.", description="Currently in use.", color=embed_color)

# Regex patterns for script modification
regex_actions = r"^[*<([][^:@#]+?[])>*]\s+"

# Emojis for the characters
emojis = {}

# Characters dictionary with their embed colors
characters = {
    "SpongeBob": 0xc3ac30,
    "Patrick": 0xeea68b,
    "Squidward": 0x9abab2,
    "Sandy": 0xc6b4ab,
    "Mr. Krabs": 0xde280d,
    "Plankton": 0x0f4708,
    "Gary": 0xc18d86,
    "Mrs. Puff": 0xcc9c64,
    "Larry": 0xd55b06,
    "Squilliam": 0xd4ecd7,
    "Karen": 0x778bb0,
    "Narrator": 0x8f7c69,
    "Bubble Buddy": 0x788b94,
    "Bubble Bass": 0xc0ae6b,
    "Perch": 0x987cb4,
    "Pearl": 0xa7b2b3,
    "DoodleBob": 0x9a94a0,
    "Mr. Fish": 0x999072,
    "Dutchman": 0x11c304,
    "King Neptune": 0x82f386,
    "Man Ray": 0x0b4881,
    "Dirty Bubble": 0x7c522d
}

# Characters literal type for command arguments
characters_literal = Literal["SpongeBob", "Patrick", "Squidward", "Sandy", "Mr. Krabs", "Plankton", "Gary", "Mrs. Puff", "Larry", "Squilliam", "Karen", "Narrator", "Bubble Buddy", "Bubble Bass", "Perch", "Pearl", "DoodleBob", "Mr. Fish", "Dutchman", "King Neptune", "Man Ray", "Dirty Bubble"]

# Gain settings for audio segments
gain_ambiance = -45
gain_music = -35
gain_sfx = -25
gain_voice = -15
gain_voice_loud = -10
gain_voice_distort = 20

# Ambiance audio segments
ambiance_time = {
    "Day": AudioSegment.from_wav("ambiance/day.wav"),
    "Night": AudioSegment.from_wav("ambiance/night.wav")
}
ambiance_rain = AudioSegment.from_wav("ambiance/rain.wav")
fade_ambiance = 500
time_literal = Literal["Day", "Night"]
weather_literal = Literal["Stormy", "Rainy", "Clear"]


# Music audio segments
music_closing_theme = AudioSegment.from_wav("music/closing_theme.wav")
music_tip_top_polka = AudioSegment.from_wav("music/tip_top_polka.wav")
music_rake_hornpipe = AudioSegment.from_wav("music/rake_hornpipe.wav")
music_seaweed = AudioSegment.from_wav("music/seaweed.wav")
music_hello_sailor_b = AudioSegment.from_wav("music/hello_sailor_b.wav")
music_drunken_sailor = AudioSegment.from_wav("music/drunken_sailor.wav")
music_stars_and_games = AudioSegment.from_wav("music/stars_and_games.wav")
music_comic_walk = AudioSegment.from_wav("music/comic_walk.wav")
music_gator = AudioSegment.from_wav("music/gator.wav")
music_rock_bottom = AudioSegment.from_wav("music/rock_bottom.wav")
music_just_breaking_softer = AudioSegment.from_mp3("music/just_breaking_softer.mp3")
music_grass_skirt_chase = AudioSegment.from_wav("music/grass_skirt_chase.wav")
fade_music = 5000

# Locations with their assigned music segments and embed colors
locations = {
    "SpongeBob's House": ({
        music_stars_and_games: 5,
        music_seaweed: 1,
        music_closing_theme: 1
    }, 0xd87c02, "SpongeBob, Patrick, Gary"),
    "Patrick's House": ({
        music_gator: 5,
        music_seaweed: 1,
        music_closing_theme: 1
    }, 0x561e1f, "SpongeBob, Patrick"),
    "Squidward's House": ({
        music_comic_walk: 5,
        music_seaweed: 1,
        music_closing_theme: 1
    }, 0x193f51, "SpongeBob, Patrick, Squidward"),
    "Sandy's Treedome": ({
        music_seaweed: 1,
        music_closing_theme: 1
    }, 0x2b6f00, "SpongeBob, Patrick, Sandy"),
    "Krusty Krab": ({
        music_tip_top_polka: 5,
        music_rake_hornpipe: 5,
        music_drunken_sailor: 5,
        music_seaweed: 1,
        music_closing_theme: 1
    }, 0x62390f, "SpongeBob, Patrick, Squidward, Mr. Krabs, Plankton"),
    "Chum Bucket": ({
        music_seaweed: 1,
        music_closing_theme: 1
    }, 0x2a3644, "Plankton, Karen"),
    "Boating School": ({
        music_hello_sailor_b: 5,
        music_seaweed: 1,
        music_closing_theme: 1
    }, 0xcab307, "SpongeBob, Patrick, Mrs. Puff"),
    "News Studio": ({
        music_just_breaking_softer: 1
    }, 0x316ec3, "Perch, Mr. Fish"),
    "Rock Bottom": ({
        music_rock_bottom: 1
    }, 0x101027, "SpongeBob, Patrick, Squidward"),
    "Bikini Bottom": ({
        music_closing_theme: 5,
        music_grass_skirt_chase: 1,
        music_gator: 1
    }, 0xddba8b, "SpongeBob, Patrick, Squidward, Mr. Krabs, Plankton, Squilliam")
}

# Locations literal type for command arguments
locations_literal = Literal["SpongeBob's House", "Patrick's House", "Squidward's House", "Sandy's Treedome", "Krusty Krab", "Chum Bucket", "Boating School", "News Studio", "Rock Bottom", "Bikini Bottom"]

# SFX audio segments
sfx_random = {
    AudioSegment.from_wav("sfx/steel_sting.wav"): 5,
    AudioSegment.from_wav("sfx/boowomp.wav"): 5,
    AudioSegment.from_wav("sfx/kiss.wav"): 5,
    AudioSegment.from_mp3("sfx/car.mp3"): 5,
    AudioSegment.from_wav("sfx/my_leg_1.wav"): 5,
    AudioSegment.from_wav("sfx/my_leg_2.wav"): 5,
    AudioSegment.from_wav("sfx/glass_shatter.wav"): 5,
    AudioSegment.from_wav("sfx/foghorn.wav"): 1,
    AudioSegment.from_wav("sfx/vibe_link_b.wav"): 1,
    AudioSegment.from_wav("sfx/this_guy_stinks.wav"): 1,
    AudioSegment.from_wav("sfx/you_what.wav"): 1,
    AudioSegment.from_wav("sfx/dolphin.wav"): 1,
    AudioSegment.from_wav("sfx/boo_you_stink.wav"): 1,
    AudioSegment.from_wav("sfx/bonk.wav"): 1,
    AudioSegment.from_wav("sfx/fling_1.wav"): 1,
    AudioSegment.from_wav("sfx/fling_2.wav"): 1,
    AudioSegment.from_wav("sfx/kick.wav"): 1,
    AudioSegment.from_wav("sfx/squish_1.wav"): 1,
    AudioSegment.from_wav("sfx/squish_2.wav"): 1,
    AudioSegment.from_wav("sfx/dramatic_cue_a.wav"): 1,
    AudioSegment.from_wav("sfx/dramatic_cue_d.wav"): 1,
    AudioSegment.from_wav("sfx/alarm.wav"): 1,
    AudioSegment.from_wav("sfx/phone_call.wav"): 1,
    AudioSegment.from_wav("sfx/explosion.wav"): 1,
    AudioSegment.from_wav("sfx/anchor.wav"): 1,
    AudioSegment.from_wav("sfx/train.wav"): 1
}
sfx_triggered = {
    "bomb": ([AudioSegment.from_wav("sfx/bomb_fuse.wav").apply_gain(-20) + AudioSegment.from_wav("sfx/bomb_explosion.wav")], ["boom", "bomb", "explosion", "explode", "exploding", "fire in the hole", "blow", "blew", "blast", "firework", "dynamite", "grenade", "detonate", "detonating"]),
    "gun": ([AudioSegment.from_wav(f"sfx/gun_{i}.wav") for i in range(1, 3)], ["shoot", "shot", "kill", "murder", "gun", "firing", "firearm", "bullet", "pistol", "rifle"]),
    "molotov": ([AudioSegment.from_wav("sfx/molotov.wav")], ["fire", "molotov", "burn", "flame", "flaming", "ignite", "igniting", "arson", "light", "hot", "blaze", "blazing", "combust"]),
    "ball": ([AudioSegment.from_wav("sfx/ball.wav")], ["ball", "bounce", "bouncing", "bouncy", "foul", "soccer", "goal", "catch", "throw", "toss", "kick"]),
    "burp": ([AudioSegment.from_wav("sfx/burp.wav")], ["krabby patty", "krabby patties", "food", "burger", "hungry", "hungrier", "ice cream", "pizza", "pie", "fries", "fry", "consume", "consuming", "consumption", "cake", "shake", "sushi", "ketchup", "mustard", "mayo", "starve", "starving", "snack", "burp", "sandwich"])
}
sfx_transition = AudioSegment.from_wav("sfx/transition.wav")
sfx_transition = sfx_transition.apply_gain(gain_sfx - sfx_transition.dBFS)
sfx_lightning = AudioSegment.from_wav("sfx/lightning.wav")

# Voice audio segments
voice_gary = [AudioSegment.from_wav(f"voice/gary_{i}.wav") for i in range(1, 7)]
voice_doodlebob = [AudioSegment.from_wav(f"voice/doodlebob_{i}.wav") for i in range(1, 19)]
voice_failed = AudioSegment.from_wav("voice/failed.wav")

# Silence audio segments
silence_line = AudioSegment.silent(200)
silence_transition = AudioSegment.silent(600)
silence_music = AudioSegment.silent(3000)

# Generation state
generating = False


@command_tree.command(description="Generate an episode.")
@describe(topic="Topic of episode.", location="Location of episode.", weather="Weather of episode.", time="Time of episode.", chaos="Whether to simulate chaos hour or not.")
@allowed_installs(True, False)
@allowed_contexts(True, False, True)
async def episode(interaction: Interaction, topic: Range[str, char_limit_min, char_limit_max], location: locations_literal = None, weather: weather_literal = None, time: time_literal = None, chaos: bool = False):
    """
    Generate an audio episode about a topic.
    :param interaction: Interaction created by the command
    :param topic: Topic of the episode
    :param location: Location of the episode
    :param weather: Weather of the episode
    :param time: Time of the episode
    :param chaos: Whether to simulate chaos hour or not
    :return: None
    """

    # Get global variable
    global generating

    # Check if something is generating
    if generating:
        await interaction.response.send_message(ephemeral=True, delete_after=embed_delete_after, embed=embed_in_use)
        return

    # Start generation
    try:

        # Show generating message
        await interaction.response.send_message(embed=embed_episode_start)

        # Block generation
        if not allow_parallel:
            generating = True
            await client.change_presence(activity=activity_generating, status=Status.dnd)

        # Log the interaction
        if logging_channel:
            await logging_channel.send(embed=Embed(title=interaction.user.id, description=f"/episode topic:{escape_markdown(topic, as_needed=True)} location:{location} weather:{weather} time:{time} chaos:{chaos}", color=embed_color))

        # Get random location if none provided
        if location is None:
            location = choice(list(locations.keys()))

        # Get random time if none provided
        if time is None:
            ambiance = choice(list(ambiance_time.values()))
        else:
            ambiance = ambiance_time[time]

        # Get rain intensity
        if weather == "Stormy":
            rain_intensity = randint(1, 5)
        elif weather == "Rainy":
            rain_intensity = randint(-5, 0)
        elif weather == "Clear":
            rain_intensity = None
        elif randrange(5) == 0:
            rain_intensity = randint(-5, 5)
            weather = "Rainy" if rain_intensity <= 0 else "Stormy"
        else:
            rain_intensity = None
            weather = "Clear"

        # Generate the script
        script = await write(f"Write a fucking chaotic, profanity-filled, and morally incorrect script for a spongebob episode about a topic that takes place on a {weather} {time} in {location} and features {locations[location][2]}, and any characters mentioned in the topic. Only respond with a two-word, spongebob-style title using the format: title: <title> followed by ten lines of brief character dialogue using the format: <character>: <dialogue>. The topic is: \"{topic}\".")

        # Clean the script
        lines = script.replace("\n\n", "\n").replace(":\n", ": ").strip().split("\n")

        # Get the episode title
        line_parts = lines.pop(0).split(":", 1)
        title_formatted = "No Title"
        if len(line_parts) == 2 and "title" in line_parts[0].casefold():
            title = line_parts[1].strip()[:char_limit_max].strip()
            if title:
                title_formatted = title

        # Keep track of current line and the total number of lines
        current_line = 1
        total_lines = len(lines)

        # Create the embed for the output
        embed_output = Embed(title=escape_markdown(title_formatted, as_needed=True), color=locations[location][1])

        # Variables used for generation data
        sfx_positions = {key: [] for key in sfx_triggered.keys()}
        combined = AudioSegment.empty()

        # Process each line
        for line in lines:

            # Update generation status
            await interaction.edit_original_response(embed=Embed(title="Generating...", description=f"Speaking line `{current_line}/{min(total_lines, 25)}`...", color=embed_color))

            # Skip line if it is improperly formatted
            line_parts = line.split(":", 1)
            if len(line_parts) != 2:
                total_lines -= 1
                continue

            # Skip line if it is too short
            output_line = sub(regex_actions, "", line_parts[1].strip())[:char_limit_max].strip()
            if len(output_line) < char_limit_min:
                total_lines -= 1
                continue

            # Get the character
            character = ""
            for key in characters.keys():
                if key.casefold() in line_parts[0].casefold():
                    character = key
                    break

            # Skip line if no character was found
            if not character:
                total_lines -= 1
                continue

            # Speak line using voice files for DoodleBob
            if character == "DoodleBob":
                seg = choice(voice_doodlebob)

            # Speak line using voice files for Gary
            elif character == "Gary":
                seg = choice(voice_gary)

            # Speak line for all other characters
            else:

                # Attempt to speak line
                try:
                    seg = await speak(character, output_line)

                # Failed sound effect on failure
                except:
                    seg = voice_failed

            # Check if any of the word-activated SFX should happen
            for sfx in sfx_triggered.keys():
                if any(keyword in output_line.casefold() for keyword in sfx_triggered[sfx][1]):
                    sfx_positions[sfx].append(len(combined) + randrange(len(seg)))
                    break

            # Apply gain, forcing a loud event sometimes
            if randrange(20) == 0:
                seg = seg.apply_gain(gain_voice_distort)
                seg = seg.apply_gain(gain_voice_loud-seg.dBFS)
            else:
                seg = seg.apply_gain(gain_voice-seg.dBFS)

            # Add the line to the combined audio segment
            combined = combined.append(seg, 0)

            # Add line spacing unless a cutoff event occurs
            if output_line[-1] not in "-–—":
                combined = combined.append(silence_line, 0)

            # Add the line to the output script
            embed_output.add_field(name="", value=f"{emojis[character.replace(' ', '').replace('.', '')]} ​ ​ {escape_markdown(output_line, as_needed=True)}", inline=False)

            # Line completed
            current_line += 1

            # Embeds have a 25 field limit. Skip remaining lines.
            if current_line > 25:
                break

        # Show final generating message
        await interaction.edit_original_response(embed=embed_episode_end)

        # Add silence at the end of the episode
        combined = combined.append(silence_line, 0)

        # Add music to the episode based on location
        music = choices(list(locations[location][0].keys()), list(locations[location][0].values()))[0]
        if music == music_just_breaking_softer or music == music_grass_skirt_chase:
            music = music.apply_gain((gain_music + randint(-5, 5)) - music.dBFS)
            music_loop = music
        else:
            music = music.apply_gain((gain_music + randint(-5, 5)) - music.dBFS)
            music_loop = silence_music.append(music.fade_in(fade_music), 0)
        while len(music_loop) < len(combined):
            music_loop = music_loop.append(music, 0)
        combined = combined.overlay(music_loop)

        # Add day or night ambiance to the episode
        ambiance = ambiance.apply_gain((gain_ambiance + randint(-5, 5)) - ambiance.dBFS)
        ambiance_loop = ambiance.fade_in(fade_ambiance)
        while len(ambiance_loop) < len(combined):
            ambiance_loop = ambiance_loop.append(ambiance, 0)
        combined = combined.overlay(ambiance_loop)

        # Add rain sounds to the episode
        if rain_intensity is not None:
            rain_randomized = ambiance_rain.apply_gain((gain_ambiance + rain_intensity) - ambiance_rain.dBFS)
            rain_loop = rain_randomized.fade_in(fade_ambiance)
            while len(rain_loop) < len(combined):
                rain_loop = rain_loop.append(rain_randomized, 0)
            combined = combined.overlay(rain_loop)

            # Add lightning if rain is intense
            if rain_intensity > 0:
                for i in range(ceil(len(combined) / 1000) if chaos else randint(1, ceil(min(total_lines, 25) / (10 - rain_intensity)))):
                    combined = combined.overlay(sfx_lightning.apply_gain((gain_sfx + randint(-10 + rain_intensity, 0)) - sfx_lightning.dBFS), randrange(len(combined)))

        # Add word-activated SFX to the episode
        for sfx in sfx_triggered.keys():
            for position in sfx_positions[sfx]:
                if randrange(5) > 0:
                    variant = choice(sfx_triggered[sfx][0])
                    combined = combined.overlay(variant.apply_gain((gain_sfx + randint(-10, 0)) - variant.dBFS), position)

        # Add random SFX to the episode
        for sfx in choices(list(sfx_random.keys()), list(sfx_random.values()), k=(ceil(len(combined) / 1000) if chaos else randint(1, ceil(min(total_lines, 25) / 5)))):
            combined = combined.overlay(sfx.apply_gain((gain_sfx + randint(-5, 5)) - sfx.dBFS), randrange(len(combined)))

        # Add the transition SFX to the beginning of the episode and fade out the end
        combined = silence_transition.append(combined, 0).overlay(sfx_transition).fade_out(len(silence_line))

        # Export the episode and send it
        with BytesIO() as output:
            combined.export(output, "mp3", bitrate=bitrate)
            await interaction.edit_original_response(embed=embed_output, attachments=[
                File(output, title_formatted.replace("/", "\\").replace("\n", " ") + ".mp3")])

    # Generation failed
    except:
        with BytesIO() as output:
            voice_failed.export(output, "wav")
            await interaction.edit_original_response(embed=embed_failed, attachments=[File(output, "Failed.wav")])

    # Unblock generation
    finally:
        if not allow_parallel:
            generating = False
            await client.change_presence(activity=activity_ready, status=Status.online)


@command_tree.command(description="Make a character speak text.")
@describe(character="Character to speak text.", text="Text to speak.", loud="Whether to speak loud or not.")
@allowed_installs(True, False)
@allowed_contexts(True, False, True)
async def tts(interaction: Interaction, character: characters_literal, text: Range[str, char_limit_min, char_limit_max], loud: bool = False):
    """
    Make a character speak text using text-to-speech.
    :param interaction: Interaction created by the command
    :param character: Character voice to use for TTS
    :param text: Text to speak
    :param loud: Whether to make the audio loud and distorted
    :return: None
    """

    # Get global variable
    global generating

    # Check if something is generating
    if generating:
        await interaction.response.send_message(ephemeral=True, delete_after=embed_delete_after, embed=embed_in_use)
        return

    # Start generation
    try:

        # Show generating message
        await interaction.response.send_message(embed=embed_tts)

        # Block generation
        if not allow_parallel:
            generating = True
            await client.change_presence(activity=activity_generating, status=Status.dnd)

        # Log the interaction
        if logging_channel:
            await logging_channel.send(embed=Embed(title=interaction.user.id, description=f"/tts character:{character} text:{escape_markdown(text, as_needed=True)} loud:{loud}", color=embed_color))

        # Speak text using voice files for DoodleBob
        if character == "DoodleBob":
            seg = choice(voice_doodlebob)

        # Speak text using voice files for Gary
        elif character == "Gary":
            seg = choice(voice_gary)

        # Speak line for all other characters
        else:
            seg = await speak(character, text)

        # Apply gain, forcing a loud event if requested
        if loud:
            seg = seg.apply_gain(gain_voice_distort)
            seg = seg.apply_gain(gain_voice_loud-seg.dBFS)
        else:
            seg = seg.apply_gain(gain_voice-seg.dBFS)

        # Export and send the file
        with BytesIO() as output:
            seg.export(output, "wav")
            await interaction.edit_original_response(embed=Embed(color=characters[character], description=escape_markdown(text, as_needed=True)).set_author(name=character, icon_url=emojis[character.replace(' ', '').replace('.', '')].url), attachments=[
                File(output, character + ": " + text.replace("/", "\\").replace("\n", " ") + ".wav")])

    # Generation failed
    except:
        with BytesIO() as output:
            voice_failed.export(output, "wav")
            await interaction.edit_original_response(embed=embed_failed, attachments=[File(output, "Failed.wav")])

    # Unblock generation
    finally:
        if not allow_parallel:
            generating = False
            await client.change_presence(activity=activity_ready, status=Status.online)


@command_tree.command(description="Chat with a character.")
@describe(character="Character to chat with.", message="Message to send.")
@allowed_installs(True, False)
@allowed_contexts(True, False, True)
async def chat(interaction: Interaction, character: characters_literal, message: Range[str, char_limit_min, char_limit_max]):
    """
    Chat with one of the characters.
    :param interaction: Interaction created by the command
    :param character: Character to chat with
    :param message: Message to send to the character
    :return: None
    """

    # Get global variable
    global generating

    # Check if something is generating
    if generating:
        await interaction.response.send_message(ephemeral=True, delete_after=embed_delete_after, embed=embed_in_use)
        return

    # Start generation
    try:

        # Show generating message
        await interaction.response.send_message(embed=embed_chat)

        # Block generation
        if not allow_parallel:
            generating = True
            await client.change_presence(activity=activity_generating, status=Status.dnd)

        # Log the interaction
        if logging_channel:
            await logging_channel.send(embed=Embed(title=interaction.user.id, description=f"/chat character:{character} message:{escape_markdown(message, as_needed=True)}", color=embed_color))

        # Generate the chat response
        response = await write(f"Write a response to a discord message as {character} from spongebob. Only respond with {character}'s brief response using the format: {character}: <response>. The message from \"{interaction.user.display_name}\" says: \"{message}\".")

        # Clean the response text
        output = escape_markdown(sub(regex_actions, "", response.split(":", 1)[1].strip())[:char_limit_max].strip(), as_needed=True)

        # Send the response
        await interaction.edit_original_response(embed=Embed(description=output, color=characters[character]).set_footer(text=message, icon_url=interaction.user.display_avatar.url).set_author(name=character, icon_url=emojis[character.replace(' ', '').replace('.', '')].url))

    # Generation failed
    except:
        with BytesIO() as output:
            voice_failed.export(output, "wav")
            await interaction.edit_original_response(embed=embed_failed, attachments=[File(output, "Failed.wav")])

    # Unblock generation
    finally:
        if not allow_parallel:
            generating = False
            await client.change_presence(activity=activity_ready, status=Status.online)


@client.event
async def on_ready():
    """
    Final initializations once the bot has logged in to the Discord API. If this fails, the program will stop.
    :return: None
    """

    try:

        # Set bot avatar if it is missing
        if client.user.avatar is None:
            with open("img/Logo.gif", "rb") as file:
                await client.user.edit(avatar=file.read())

        # Set bot banner if it is missing
        if (await client.fetch_user(client.user.id)).banner is None:
            with open("img/Banner.png", "rb") as file:
                await client.user.edit(banner=file.read())

        # Fetch all application emojis
        global emojis
        emojis = {e.name: e for e in await client.fetch_application_emojis()}

        # Create missing application emojis
        for emoji_file in listdir("emoji"):
            emoji_name = emoji_file.split(".")[0]
            if emoji_name not in emojis.keys():
                with open(f"emoji/{emoji_file}", "rb") as file:
                    emojis[emoji_name] = await client.create_application_emoji(name=emoji_name, image=file.read())

        # Set logging channel if specified
        global logging_channel
        logging_channel_id = getenv("LOGGING_CHANNEL_ID")
        if logging_channel_id:
            logging_channel = await client.fetch_channel(int(logging_channel_id))

        # Sync command tree
        await command_tree.sync()

        # Set status to ready
        await client.change_presence(activity=activity_ready, status=Status.online)

    # Stop bot if any of the above fails
    except:
        exit(1)


# Start bot (must be at the end of the file)
client.run(getenv("DISCORD_BOT_TOKEN"))
