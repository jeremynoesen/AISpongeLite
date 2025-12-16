"""
AI Sponge Lite is a Discord bot that generates parody AI Sponge audio episodes, chats, and TTS inspired by
[AI Sponge Rehydrated](https://aisponge.riskivr.com/).

Written by Jeremy Noesen
"""

from typing import Literal
from random import randint, randrange, choice, choices
from re import sub
from math import ceil
from io import BytesIO
from os import getenv, listdir
from dotenv import load_dotenv
from discord import Status, Embed, Interaction, Color, Game, utils, Intents, Client, File, app_commands
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
command_tree = app_commands.CommandTree(client)

# Logging channel
logging_channel = None

# Embed settings and static embeds
embed_color = Color.dark_theme()
embed_delete_after = 10
embed_episode_start = Embed(title="Generating...", description="Writing script...", color=embed_color)
embed_episode_end = Embed(title="Generating...", description="Mixing audio...", color=embed_color)
embed_tts = Embed(title="Generating...", description="Speaking text...", color=embed_color)
embed_chat = Embed(title="Generating...", description="Writing response...", color=embed_color)
embed_failed = Embed(title="Failed.", description="An error occurred.", color=embed_color)
embed_in_use = Embed(title="Busy.", description="Currently in use.", color=embed_color)

# Regex patterns for actions in script
regex_actions = r"(:\s+)(\(+\S[^()]+\S\)+|\[+\S[^\[\]]+\S]+|\*+\S[^*]+\S\*+|<+\S[^<>:]+\S>+|\{+\S[^{}]+\S}+|-+\S[^-]+\S-+|\|+\S[^|]+\S\|+|/+\S[^/]+\S/+|\\+\S[^\\]+\S\\+)([^\S\r\n]+)"
regex_replacement = r"\1"

# Emojis for the characters
emojis = {}

# Characters dictionary with their embed colors
characters = {
    "spongebob": 0xc3ac30,
    "patrick": 0xeea68b,
    "squidward": 0x9abab2,
    "sandy": 0xc6b4ab,
    "mr. krabs": 0xde280d,
    "plankton": 0x0f4708,
    "gary": 0xc18d86,
    "mrs. puff": 0xcc9c64,
    "larry": 0xd55b06,
    "squilliam": 0xd4ecd7,
    "karen": 0x778bb0,
    "narrator": 0x8f7c69,
    "bubble buddy": 0x788b94,
    "bubble bass": 0xc0ae6b,
    "perch": 0x987cb4,
    "pearl": 0xa7b2b3,
    "doodlebob": 0x9a94a0,
    "mr. fish": 0x999072,
    "dutchman": 0x11c304,
    "king neptune": 0x82f386,
    "man ray": 0x0b4881,
    "dirty bubble": 0x7c522d
}

# Characters literal type for command arguments
characters_literal = Literal["spongebob", "patrick", "squidward", "sandy", "mr. krabs", "plankton", "gary", "mrs. puff", "larry", "squilliam", "karen", "narrator", "bubble buddy", "bubble bass", "perch", "pearl", "doodlebob", "mr. fish", "dutchman", "king neptune", "man ray", "dirty bubble"]

# Gain settings for audio segments
gain_ambiance = -45
gain_music = -35
gain_sfx = -25
gain_voice = -15
gain_voice_loud = -10
gain_voice_distort = 20

# Ambiance audio segments
ambiance_time = {
    AudioSegment.from_wav("ambiance/day.wav"): ["day", "bright", "morning", "noon", "dawn", "sunrise", "early"],
    AudioSegment.from_wav("ambiance/night.wav"): ["night", "dark", "evening", "dusk", "sunset", "late"]
}
ambiance_rain = AudioSegment.from_wav("ambiance/rain.wav")
storm_keywords = ["storm", "thunder", "lightning", "downpour"]
rain_keywords = ["rain", "drizzle", "shower", "sprinkle", "wet"]
clear_keywords = ["clear", "dry"]
fade_ambiance = 500

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

# Locations with their assigned music segments and embed colors
locations = {
    "spongebob's house": ({
        music_stars_and_games: 5,
        music_seaweed: 1,
        music_closing_theme: 1
    }, 0xd87c02, "spongebob, patrick, gary"),
    "patrick's house": ({
        music_gator: 5,
        music_seaweed: 1,
        music_closing_theme: 1
    }, 0x561e1f, "spongebob, patrick"),
    "squidward's house": ({
        music_comic_walk: 5,
        music_seaweed: 1,
        music_closing_theme: 1
    }, 0x193f51, "spongebob, patrick, squidward"),
    "sandy's treedome": ({
        music_seaweed: 1,
        music_closing_theme: 1
    }, 0x2b6f00, "spongebob, patrick, sandy"),
    "krusty krab": ({
        music_tip_top_polka: 5,
        music_rake_hornpipe: 5,
        music_drunken_sailor: 5,
        music_seaweed: 1,
        music_closing_theme: 1
    }, 0x62390f, "spongebob, patrick, squidward, mr. krabs, plankton"),
    "chum bucket": ({
        music_seaweed: 1,
        music_closing_theme: 1
    }, 0x2a3644, "plankton, karen"),
    "boating school": ({
        music_hello_sailor_b: 5,
        music_seaweed: 1,
        music_closing_theme: 1
    }, 0xcab307, "spongebob, patrick, mrs. puff"),
    "news studio": ({
        music_just_breaking_softer: 1
    }, 0x316ec3, "perch, mr. fish"),
    "rock bottom": ({
        music_rock_bottom: 1
    }, 0x101027, "spongebob, patrick, squidward"),
    "bikini bottom": ({
        music_closing_theme: 5,
        music_grass_skirt_chase: 1,
        music_gator: 1
    }, 0xddba8b, "spongebob, patrick, squidward, mr. krabs, plankton, squilliam")
}

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
    "bomb": ([AudioSegment.from_wav("sfx/bomb_fuse.wav").apply_gain(-20) + AudioSegment.from_wav("sfx/bomb_explosion.wav")], ["boom", "bomb", "explosion", "explode", "exploding", "fire in the hole", "blow", "blew", "blast", "firework"]),
    "gun": ([AudioSegment.from_wav(f"sfx/gun_{i}.wav") for i in range(1, 3)], ["shoot", "shot", "kill", "murder", "gun", "firing", "firearm", "bullet", "pistol", "rifle"]),
    "molotov": ([AudioSegment.from_wav("sfx/molotov.wav")], ["fire", "molotov", "burn", "flame", "flaming", "ignite", "igniting", "arson", "light", "lit", "hot", "blaze", "blazing", "combust"]),
    "ball": ([AudioSegment.from_wav("sfx/ball.wav")], ["ball", "bounce", "bouncing", "bouncy", "foul", "soccer", "goal", "catch", "throw", "toss", "kick"]),
    "burp": ([AudioSegment.from_wav("sfx/burp.wav")], ["krabby patty", "krabby patties", "food", "burger", "hungry", "hungrier", "ice cream", "pizza", "pie", "fries", "fry", "consume", "consuming", "consumption", "cake", "shake", "sushi", "ketchup", "mustard", "mayo", "starve", "starving", "snack", "burp"])
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
@app_commands.describe(topic="Topic of episode.")
@app_commands.allowed_installs(True, False)
@app_commands.allowed_contexts(True, False, True)
async def episode(interaction: Interaction, topic: app_commands.Range[str, char_limit_min, char_limit_max]):
    """
    Generate an audio episode about a topic.
    :param interaction: Interaction created by the command
    :param topic: Topic of the episode
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
            await logging_channel.send(embed=Embed(title=interaction.user.id, description=f"/episode topic:{utils.escape_markdown(topic)}", color=embed_color))

        # Lowercase version of topic for processing
        topic_lower = topic.lower()

        # Get location from topic or choose a random one
        location = choice(list(locations.keys()))
        for key in locations.keys():
            if key in topic_lower:
                location = key
                break

        # Get ambiance from topic or choose a random one
        ambiance = choice(list(ambiance_time.keys()))
        for key in ambiance_time.keys():
            if any(word in topic_lower for word in ambiance_time[key]):
                ambiance = key
                break

        # Determine rain intensity from topic or randomly
        if any(word in topic_lower for word in storm_keywords):
            rain_intensity = randint(1, 5)
            weather = "stormy"
        elif any(word in topic_lower for word in rain_keywords):
            rain_intensity = randint(-5, 0)
            weather = "rainy"
        elif any(word in topic_lower for word in clear_keywords):
            rain_intensity = None
            weather = "clear"
        elif randrange(5) == 0:
            rain_intensity = randint(-5, 5)
            weather = "rainy" if rain_intensity <= 0 else "stormy"
        else:
            rain_intensity = None
            weather = "clear"

        # Generate the script
        script = await write(f"Write an insane, profanity-filled, and morally incorrect script for a spongebob episode about a topic. Characters in this episode are {locations[location][2]}, and any characters mentioned in the topic. This episode takes place on a {weather} {ambiance_time[ambiance][0]} in {location}. Use the format: character: <dialogue>. Only reply with brief and uncensored character dialogue. Around 12 - 15 lines of dialogue with talking only. The first line is a brief and insane 1 - 2 word episode title with format: title: <title>. The topic is: \"{topic}\".")

        # Clean the script
        lines = sub(regex_actions, regex_replacement, script.replace("\n\n", "\n").replace(":\n", ": ")).strip().split("\n")

        # Get the episode title
        line_parts = lines.pop(0).split(":", 1)
        title_formatted = "No Title"
        if len(line_parts) == 2 and "title" in line_parts[0].lower():
            title = line_parts[1].strip()[:char_limit_max].strip()
            if title:
                title_formatted = title

        # Keep track of current line and the total number of lines
        current_line = 1
        total_lines = len(lines)

        # Create the embed for the output
        output_embed = Embed(title=utils.escape_markdown(title_formatted), color=locations[location][1])

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
            output_line = line_parts[1].strip()[:char_limit_max].strip()
            if len(output_line) < char_limit_min:
                total_lines -= 1
                continue

            # Get the character
            character = ""
            for key in characters.keys():
                if key in line_parts[0].lower():
                    character = key
                    break

            # Skip line if no character was found
            if not character:
                total_lines -= 1
                continue

            # Speak line using voice files for DoodleBob
            if character == "doodlebob":
                seg = choice(voice_doodlebob)

            # Speak line using voice files for Gary
            elif character == "gary":
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
                if any(keyword in output_line.lower() for keyword in sfx_triggered[sfx][1]):
                    sfx_positions[sfx].append(len(combined) + randrange(len(seg)))
                    break

            # Apply gain, forcing a loud event sometimes
            if output_line.isupper() or randrange(20) == 0:
                seg = seg.apply_gain(gain_voice_distort)
                seg = seg.apply_gain(gain_voice_loud-seg.dBFS)
                output_line = output_line.upper()
            else:
                seg = seg.apply_gain(gain_voice-seg.dBFS)

            # Add the line to the combined audio segment
            combined = combined.append(seg, 0)

            # Add line spacing unless a cutoff event occurs
            if output_line[-1] in "-–—" or randrange(10) == 0:
                output_line = output_line[:-1] + "—"
            else:
                combined = combined.append(silence_line, 0)

            # Add the line to the output script
            output_embed.add_field(name="", value=f"{emojis[character.replace(' ', '').replace('.', '')]} ​ ​ {utils.escape_markdown(output_line)}", inline=False)

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
            music_loop = silence_music.append(music.fade_in(10000), 0)
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
                for i in range(randint(1, ceil(min(total_lines, 25) / (10 - rain_intensity)))):
                    combined = combined.overlay(sfx_lightning.apply_gain((gain_sfx + randint(-10 + rain_intensity, 0)) - sfx_lightning.dBFS), randrange(len(combined)))

        # Add word-activated SFX to the episode
        for sfx in sfx_triggered.keys():
            for position in sfx_positions[sfx]:
                if randrange(5) > 0:
                    variant = choice(sfx_triggered[sfx][0])
                    combined = combined.overlay(variant.apply_gain((gain_sfx + randint(-10, 0)) - variant.dBFS), position)

        # Add random SFX to the episode
        for sfx in choices(list(sfx_random.keys()), list(sfx_random.values()), k=randint(1, ceil(min(total_lines, 25) / 5))):
            combined = combined.overlay(sfx.apply_gain((gain_sfx + randint(-5, 5)) - sfx.dBFS), randrange(len(combined)))

        # Add the transition SFX to the beginning of the episode and fade out the end
        combined = silence_transition.append(combined, 0).overlay(sfx_transition).fade_out(len(silence_line))

        # Export the episode and send it
        with BytesIO() as output:
            combined.export(output, "mp3", bitrate=bitrate)
            await interaction.edit_original_response(embed=output_embed, attachments=[
                File(output, f"{title_formatted.replace('/', '\\')}.mp3")])

    # Generation failed
    except:
        await interaction.edit_original_response(embed=embed_failed)

    # Unblock generation
    finally:
        if not allow_parallel:
            generating = False
            await client.change_presence(activity=activity_ready, status=Status.online)


@command_tree.command(description="Make a character speak text.")
@app_commands.describe(character="Character to speak text.", text="Text to speak.")
@app_commands.allowed_installs(True, False)
@app_commands.allowed_contexts(True, False, True)
async def tts(interaction: Interaction, character: characters_literal, text: app_commands.Range[str, char_limit_min, char_limit_max]):
    """
    Make a character speak text using text-to-speech.
    :param interaction: Interaction created by the command
    :param character: Character voice to use for TTS
    :param text: Text to speak
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
            await logging_channel.send(embed=Embed(title=interaction.user.id, description=f"/tts character:{character} text:{utils.escape_markdown(text)}", color=embed_color))

        # Speak text using voice files for DoodleBob
        if character == "doodlebob":
            seg = choice(voice_doodlebob)

        # Speak text using voice files for Gary
        elif character == "gary":
            seg = choice(voice_gary)

        # Speak line for all other characters
        else:
            seg = await speak(character, text)

        # Apply gain, forcing a loud event if the text is uppercase
        if text.isupper():
            seg = seg.apply_gain(gain_voice_distort)
            seg = seg.apply_gain(gain_voice_loud-seg.dBFS)
        else:
            seg = seg.apply_gain(gain_voice-seg.dBFS)

        # Export and send the file
        with BytesIO() as output:
            seg.export(output, "mp3", bitrate=bitrate)
            character_title = character.title().replace('bob', 'Bob')
            await interaction.edit_original_response(embed=Embed(color=characters[character], description=utils.escape_markdown(text)).set_author(name=character_title, icon_url=emojis[character.replace(' ', '').replace('.', '')].url), attachments=[
                File(output, f"{character_title}: {text.replace('/', '\\')}.mp3")])

    # Generation failed
    except:
        await interaction.edit_original_response(embed=embed_failed)

    # Unblock generation
    finally:
        if not allow_parallel:
            generating = False
            await client.change_presence(activity=activity_ready, status=Status.online)


@command_tree.command(description="Chat with a character.")
@app_commands.describe(character="Character to chat with.", message="Message to send.")
@app_commands.allowed_installs(True, False)
@app_commands.allowed_contexts(True, False, True)
async def chat(interaction: Interaction, character: characters_literal, message: app_commands.Range[str, char_limit_min, char_limit_max]):
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
            await logging_channel.send(embed=Embed(title=interaction.user.id, description=f"/chat character:{character} message:{utils.escape_markdown(message)}", color=embed_color))

        # Generate the chat response
        response = await write(f"Write an insane and morally incorrect response to a discord message as {character} from spongebob. Use the format: {character}: <response>. Only reply with {character}'s brief response. The message from \"{interaction.user.display_name}\" says: \"{message}\".")

        # Clean the response text
        output = utils.escape_markdown(sub(regex_actions, regex_replacement, response.replace("\n\n", "\n").replace(":\n", ": ")).strip().split("\n")[0].split(":", 1)[1].strip()[:char_limit_max].strip())

        # Send the response
        await interaction.edit_original_response(embed=Embed(description=output, color=characters[character]).set_footer(text=message, icon_url=interaction.user.display_avatar.url).set_author(name=character.title().replace("bob", "Bob"), icon_url=emojis[character.replace(' ', '').replace('.', '')].url))

    # Generation failed
    except:
        await interaction.edit_original_response(embed=embed_failed)

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
