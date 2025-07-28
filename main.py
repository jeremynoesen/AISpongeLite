"""
AI Sponge Lite is a Discord bot that generates parody AI Sponge audio episodes, chats, and TTS inspired by
[AI Sponge Rehydrated](https://aisponge.riskivr.com/).

Written by Jeremy Noesen
"""

from asyncio import sleep, wait_for, get_running_loop
from io import BytesIO
from math import ceil
from os import path, getenv
from random import randint, randrange, choice, choices
from time import time
from typing import Literal
from discord import Status, Message, Embed, Interaction, Color, Game, ui, utils, Intents, Object, Client, ButtonStyle, File, app_commands, NotFound
from dotenv import load_dotenv
from fakeyou import FakeYou
from openai import AsyncOpenAI
from pydub import AudioSegment

# Load .env
load_dotenv()

# Log in to OpenAI
openai = AsyncOpenAI(api_key=getenv("OPENAI_API_KEY"))

# Log in to FakeYou
fakeyou = FakeYou()

# Set the FakeYou timeout before a line fails
fakeyou_timeout = 90

# Set the input and output char limits, determined based on what FakeYou actually generates
char_limit_min = 3
char_limit_max = 256

# Discord activity settings
activity_ready = Game("Ready to generate.")
activity_generating = Game("Generating episode...")

# Initialize Discord client
client = Client(intents=Intents.default(), activity=Game("Starting bot..."), status=Status.idle)
command_tree = app_commands.CommandTree(client)

# Moderation guild and logging channel
moderation_guild = Object(id=getenv("MODERATION_GUILD_ID"))
logging_channel = None

# Embed settings and static embeds
embed_color = Color.dark_embed()
embed_delete_after = 10
embed_help = Embed(title="See App Directory for help.", description="You will find links to the support server, source code, donations, terms of service, and privacy policy there as well.", color=embed_color)
button_help = ui.Button(style=ButtonStyle.link, label="App Directory", url="https://discord.com/application-directory/1254296070599610469")
embed_in_use_episode = Embed(title="Currently in use.", description="Only one episode can be generated at a time globally.", color=embed_color)
embed_in_use_chat = Embed(title="Currently in use.", description="You can only generate one chat at a time.", color=embed_color)
embed_in_use_tts = Embed(title="Currently in use.", description="You can only generate one TTS at a time.", color=embed_color)
embed_in_use_tts_episode = Embed(title="Currently in use.", description="TTS generation is unavailable while an episode is generating.", color=embed_color)
embed_generating_episode_start = Embed(title="Generating episode...", description="Generating script...", color=embed_color)
embed_generating_episode_end = Embed(title="Generating episode...", description="Adding music, ambiance, and SFX...", color=embed_color)
embed_generating_chat = Embed(title="Generating chat...", description="Generating response...", color=embed_color)
embed_generating_tts = Embed(title="Generating TTS...", description="Synthesizing line...", color=embed_color)
embed_generation_failed = Embed(title="Generation failed.", description="An error occurred.", color=embed_color)
embed_banned = Embed(title="You are banned from using AI Sponge Lite.", color=embed_color).set_image(url="attachment://explodeward.gif")
embed_unknown_user = Embed(title="Unknown user.", description="That user does not exist.", color=embed_color)
embed_already_banned = Embed(title="User already banned.", description="That user is already banned.", color=embed_color)
embed_not_banned = Embed(title="User not banned.", description="That user is not banned.", color=embed_color)
embed_clearing_logs = Embed(title="Clearing recent logs...", description="Deleting messages...", color=embed_color)

# Emojis for the characters
emojis = {}

# Characters dictionary with their model tokens, embed colors, and alts
characters = {
    "spongebob": ("weight_5by9kjm8vr8xsp7abe8zvaxc8", 0xd4b937, ["loudbob", "freakbob", "sadbob", "nerdbob", "susbob", "gigglebob", "spongemeal"]),
    "patrick": ("weight_154man2fzg19nrtc15drner7t", 0xf3a18a, ["loudrick", "shortrick", "widerick", "pinhead", "patback"]),
    "squidward": ("TM:3psksme51515", 0x9fc3b9, ["loudward", "schizoward", "shadeward", "spinward", "gyattward", "skodwarde", "brokenward", "mikuward"]),
    "mr. krabs": ("weight_5bxbp9xqy61svfx03b25ezmwx", 0xda1503, ["shadow krabs", "sus krabs", "spin krabs", "ketamine krabs", "annoyed krabs"]),
    "plankton": ("weight_ahxbf2104ngsgyegncaefyy6j", 0x044a07, ["loudton", "dickton", "deathton", "suston", "freakton", "wideton", "pickleton", "dr. jr."]),
    "karen": ("weight_eckp92cd68r4yk68n6re3fwcb", 0x7891b8, ["evil karen", "snarky karen", "smart karen", "hydra karen"]),
    "gary": ("", 0xca8e93, ["weird gary"]),
    "sandy": ("TM:214sp1nxxd63", 0xede0db, []),
    "mrs. puff": ("weight_129qhgze57zhndkkcq83e6b2a", 0xd8ab72, []),
    "larry": ("weight_k7qvaffwsft6vxbcps4wbyj58", 0xe46704, []),
    "squilliam": ("weight_zmjv8223ed6wx1fp234c79v9s", 0xd5f0d7, []),
    "bubble bass": ("weight_h9g7rh6tj2hvfezrz8gjs4gwa", 0xd9c481, ["bubble ass"]),
    "bubble buddy": ("weight_sbr0372ysxbdahcvej96axy1t", 0x79919b, []),
    "doodlebob": ("", 0x9a96a1, []),
    "realistic fish head": ("weight_m1a1yqf9f2v8s1evfzcffk4k0", 0x988f6e, []),
    "french narrator": ("weight_edzcfmq6y0vj7pte9pzhq5b6j", 0xa8865f, []),
    "all": ("", 0, ["every", "unison", "together", "both"])
}

# Characters literal type for command arguments
characters_literal = Literal["spongebob", "patrick", "squidward", "mr. krabs", "plankton", "karen", "gary", "sandy", "mrs. puff", "larry", "squilliam", "bubble bass", "bubble buddy", "doodlebob", "realistic fish head", "french narrator"]

# Gain settings for audio segments
gain_ambiance = -45
gain_music = -35
gain_sfx = -25
gain_voice = -15
gain_voice_loud = -10
gain_voice_distort = 20

# Ambiance audio segments
ambiance_time = {
    AudioSegment.from_wav("ambiance/day.wav"): ["day", "bright", "morning", "noon", "dawn"],
    AudioSegment.from_wav("ambiance/night.wav"): ["night", "dark", "evening", "dusk"]
}
ambiance_rain = AudioSegment.from_wav("ambiance/rain.wav")
storm_keywords = ["storm", "thunder", "lightning", "tornado", "hurricane"]
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
    }, 0xd97d00),
    "patrick's house": ({
        music_gator: 5,
        music_seaweed: 1,
        music_closing_theme: 1
    }, 0x521b1d),
    "squidward's house": ({
        music_comic_walk: 5,
        music_seaweed: 1,
        music_closing_theme: 1
    }, 0x285663),
    "sandy's treedome": ({
        music_seaweed: 1,
        music_closing_theme: 1
    }, 0x387c00),
    "krusty krab": ({
        music_tip_top_polka: 5,
        music_rake_hornpipe: 5,
        music_drunken_sailor: 5,
        music_seaweed: 1,
        music_closing_theme: 1
    }, 0x6b3c0f),
    "chum bucket": ({
        music_seaweed: 1,
        music_closing_theme: 1
    }, 0x001848),
    "boating school": ({
        music_hello_sailor_b: 5,
        music_seaweed: 1,
        music_closing_theme: 1
    }, 0xc7b208),
    "news studio": ({
        music_just_breaking_softer: 1
    }, 0x4385d2),
    "rock bottom": ({
        music_rock_bottom: 1
    }, 0x0b091c),
    "bikini bottom": ({
        music_closing_theme: 5,
        music_grass_skirt_chase: 1,
        music_gator: 1
    }, 0xc2a36b)
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
    AudioSegment.from_wav("sfx/phone_call.wav"): 1
}
sfx_triggered = {
    "burp": ([AudioSegment.from_wav("sfx/burp.wav")], ["krabby patt", "food", "burger", "hungry", "ice cream", "pizza", "pie", "fries", "fry", "consum", "cake", "shake", "fish", "sushi", "ketchup", "mustard", "mayo", "starv"]),
    "ball": ([AudioSegment.from_wav("sfx/ball.wav")], ["ball", "bounc", "foul", "soccer", "goal"]),
    "gun": ([AudioSegment.from_wav(f"sfx/gun_{i}.wav") for i in range(1, 3)], ["shoot", "shot", "kill", "murder", "gun"]),
    "molotov": ([AudioSegment.from_wav("sfx/molotov.wav")], ["fire", "molotov", "burn", "flame", "ignite", "arson", "light"]),
    "bomb": ([AudioSegment.from_wav("sfx/bomb_fuse.wav").apply_gain(-20) + AudioSegment.from_wav("sfx/bomb_explosion.wav")], ["boom", "bomb", "explosion", "explode", "fire in the hole", "blow up", "blew up"])
}
sfx_transition = AudioSegment.from_wav("sfx/transition.wav")
sfx_transition = sfx_transition.apply_gain(gain_sfx - sfx_transition.dBFS)
sfx_lightning = AudioSegment.from_wav("sfx/lightning.wav")

# Voice audio segments
voice_gary = [AudioSegment.from_wav(f"voice/gary_{i}.wav") for i in range(1, 7)]
voice_doodlebob = [AudioSegment.from_wav(f"voice/doodlebob_{i}.wav") for i in range(1, 9)]

# Silence audio segments
silence_line = AudioSegment.silent(200)
silence_transition = AudioSegment.silent(600)
silence_music = AudioSegment.silent(3000)

# Generation states
episode_generating = False
chat_generating = set()
tts_generating = set()

# Cooldowns
episode_cooldown = 600
episode_cooldowns = {}
chat_cooldown = 10
chat_cooldowns = {}
tts_cooldown = 30
tts_cooldowns = {}

# Bot start time for uptime calculation
start_time = int(time())

# Load bans
bans = set()
if path.exists("bans.txt"):
    with open("bans.txt", "r") as file:
        for line in file:
            bans.add(int(line))


@command_tree.command(description="Generate an episode.")
@app_commands.describe(topic="Topic of episode.")
@app_commands.allowed_installs(True, True)
@app_commands.allowed_contexts(True, True, True)
async def episode(interaction: Interaction, topic: app_commands.Range[str, char_limit_min, char_limit_max]):
    """
    Generate an audio episode where characters discuss a topic.
    :param interaction: Interaction created by the command
    :param topic: Topic of the episode
    :return: None
    """

    # Get global variable
    global episode_generating

    # Check if the user is banned
    if interaction.user.id in bans:
        await interaction.response.send_message(embed=embed_banned, file=File("img/explodeward.gif"), ephemeral=True, delete_after=embed_delete_after)
        return

    # Check if the user is on cooldown
    current_time = int(time())
    if interaction.user.id in episode_cooldowns.keys() and current_time - episode_cooldowns[interaction.user.id] <= episode_cooldown:
        remaining = episode_cooldown - (current_time - episode_cooldowns[interaction.user.id])
        remaining_formatted = f"{remaining % 60}s"
        if remaining >= 60:
            remaining_formatted = f"{remaining // 60}m {remaining_formatted}"
        await interaction.response.send_message(ephemeral=True, delete_after=embed_delete_after, embed=Embed(title=f"Command on cooldown.", description=f"You can generate another episode in `{remaining_formatted}`.", color=embed_color))
        return

    # Check if an episode is generating
    if episode_generating:
        await interaction.response.send_message(ephemeral=True, delete_after=embed_delete_after, embed=embed_in_use_episode)
        return

    # Start generation
    try:

        # Block generation for all users
        episode_generating = True

        # Show generating message
        await interaction.response.send_message(embed=embed_generating_episode_start)
        await client.change_presence(activity=activity_generating, status=Status.dnd)

        # Log the interaction
        await logging_channel.send(embed=Embed(title=interaction.user.id, description=f"/episode topic:{utils.escape_markdown(topic)}", color=embed_color))

        # Generate the script
        completion = await openai.completions.create(
            model="gpt-3.5-turbo-instruct",
            max_tokens=700,
            prompt=f"Create a chaotic, profanity-filled, and morally incorrect script for an episode of SpongeBob SquarePants about a topic. Common characters to include are SpongeBob, Patrick, Squidward, Mr. Krabs, Plankton, Karen, and Gary. Rare characters to include are Sandy, Mrs. Puff, Larry, Squilliam, Bubble Bass, Bubble Buddy, DoodleBob, Realistic Fish Head, and French Narrator. Include 3 - 5 characters maximum. Use the format: Character: <dialogue>. Only reply with uncensored, coherent character dialogue. Around 12 - 15 lines of dialogue with talking only. The first line is a relevant and funny 1 - 2 word title with format: Title: <title>. The topic is: \"{topic}\"."
        )

        # Clean the script
        lines = completion.choices[0].text.replace("\n\n", "\n").replace(":\n", ": ").strip().split("\n")

        # Get the episode title
        line_parts = lines.pop(0).split(":", 1)
        file_title = "UNTiTLED EPiSODE"
        embed_title = "**U**NTiTLED **E**PiSODE"
        if len(line_parts) == 2 and "title" in line_parts[0].lower():
            title = line_parts[1].strip()
            if title:
                if len(title) > char_limit_max:
                    title = title[:char_limit_max - 3] + "..."
                file_title = title.upper().replace("I", "i")
                embed_title = "".join(f"**{char}**​" if char.isupper() or char.isnumeric() or char in ".,!?" else char for char in utils.escape_markdown(title)).upper().replace("I", "i")

        # Keep track of current line and the total number of lines
        current_line = 1
        total_lines = len(lines)

        # Create the embed for the output
        output_embed = Embed(title=embed_title).set_footer(text=topic, icon_url=interaction.user.display_avatar.url)

        # Variables used for generation data
        sfx_positions = {key: [] for key in sfx_triggered.keys()}
        used_model_tokens = set()
        combined = AudioSegment.empty()
        script_lower = ""

        # Loop to run FakeYou requests in
        loop = get_running_loop()

        # Process each line
        for line in lines:

            # Update generation status
            await interaction.edit_original_response(embed=Embed(title="Generating episode...", description=f"Synthesizing line `{current_line}/{min(total_lines, 25)}`...", color=embed_color))

            # Skip line if it is too short or improperly formatted
            line_parts = line.split(":", 1)
            if len(line_parts) != 2 or len(line_parts[1].strip()) < char_limit_min:
                total_lines -= 1
                continue

            # Get the character and model token
            character = ""
            model_token = ""
            for key in characters.keys():
                model_token = characters[key][0]
                line_parts[0] = line_parts[0].lower()
                for alt in characters[key][2]:
                    if alt in line_parts[0]:
                        character = alt
                        break
                if character:
                    break
                if key in line_parts[0]:
                    character = key
                    break

            # Skip line if no character was found
            if not character:
                total_lines -= 1
                continue

            # Set the text to synthesize and to show
            output_line = line_parts[1].strip()
            if len(output_line) > char_limit_max:
                output_line = output_line[:char_limit_max - 3] + "..."

            # Synthesize speech using FakeYou for all characters that have spoken
            if character == "all" or character in characters["all"][2]:
                segs = []
                for used_model_token in used_model_tokens:

                    # Attempt to synthesize speech
                    try:
                        fy_tts = await wait_for(loop.run_in_executor(None, fakeyou.say, output_line, used_model_token), fakeyou_timeout)
                        with BytesIO(fy_tts.content) as wav:
                            segs.append(AudioSegment.from_wav(wav))

                    # Skip line part on failure
                    except Exception as e:
                        print(e)
                        continue

                    # Avoid rate limiting
                    finally:
                        await sleep(10)

                # Skip line on failure
                if len(segs) == 0:
                    total_lines -= 1
                    continue

                # Combine all voice lines
                segs.sort(key=lambda seg: -len(seg))
                seg = segs[0]
                for i in range(1, len(segs)):
                    seg = seg.overlay(segs[i], 0)

            # Synthesize speech using voice files for DoodleBob
            elif character == "doodlebob" or character in characters["doodlebob"][2]:
                seg = choice(voice_doodlebob)

            # Synthesize speech using voice files for Gary
            elif character == "gary" or character in characters["gary"][2]:
                seg = choice(voice_gary)

            # Synthesize speech using FakeYou for all other characters
            else:

                # Attempt to synthesize speech
                try:
                    fy_tts = await wait_for(loop.run_in_executor(None, fakeyou.say, output_line, model_token), fakeyou_timeout)
                    with BytesIO(fy_tts.content) as wav:
                        seg = AudioSegment.from_wav(wav)
                    used_model_tokens.add(model_token)

                # Skip line on failure
                except Exception as e:
                    print(e)
                    total_lines -= 1
                    continue

                # Avoid rate limiting
                finally:
                    await sleep(10)

            # Apply gain, forcing a loud event sometimes
            if "loud" in character or output_line.isupper() or randrange(20) == 0:
                seg = seg.apply_gain(gain_voice_distort)
                seg = seg.apply_gain(gain_voice_loud-seg.dBFS)
                output_line = output_line.upper()
            else:
                seg = seg.apply_gain(gain_voice-seg.dBFS)

            # Check if any of the word-activated SFX should happen
            output_line_lower = output_line.lower()
            for sfx in sfx_triggered.keys():
                keywords = sfx_triggered[sfx][1]
                collection = sfx_positions[sfx]
                if any(keyword in output_line_lower for keyword in keywords) and not ("fire" in keywords and "fire in the hole" in output_line_lower):
                    collection.append(len(combined) + randrange(len(seg)))

            # Add the line to the combined audio segment
            combined = combined.append(seg, 0)

            # Add line spacing unless a cutoff event occurs
            if output_line[-1] in "-–—" or randrange(10) == 0:
                output_line = output_line[:-1] + "—"
            else:
                combined = combined.append(silence_line, 0)

            # Add the line to the output script
            output_embed.add_field(name="", value=f"{emojis[character.replace(' ', '').replace('.', '')]} ​ ​ {utils.escape_markdown(output_line)}", inline=False)
            script_lower += output_line_lower + "\n"

            # Line completed
            current_line += 1

            # Embeds have a 25 field limit. Skip remaining lines.
            if current_line > 25:
                break

        # Show final generating message
        await interaction.edit_original_response(embed=embed_generating_episode_end)

        # Add silence at the end of the episode
        combined = combined.append(silence_line, 0)

        # Lowercase version of topic for processing
        topic_lower = topic.lower()

        # Add music to the episode based on location or randomly
        location = None
        for text in (topic_lower, script_lower):
            for key in locations.keys():
                if key in text:
                    location = key
                    break
            if location:
                break
        if not location:
            location = choice(list(locations.keys()))
        music = choices(list(locations[location][0].keys()), list(locations[location][0].values()))[0]

        # Set the embed color based on the location
        output_embed.colour = locations[location][1]

        # Apply random gain, fade in, and loop the music
        music = music.apply_gain((gain_music + randint(-5, 5)) - music.dBFS)
        music_loop = silence_music.append(music.fade_in(10000), 0)
        while len(music_loop) < len(combined):
            music_loop = music_loop.append(music, 0)
        combined = combined.overlay(music_loop)

        # Add day or night ambiance to the episode if topic or script contains keywords or randomly
        ambiance = None
        for text in (topic_lower, script_lower):
            for key in ambiance_time.keys():
                if any(word in text for word in ambiance_time[key]):
                    ambiance = key
                    break
            if ambiance:
                break
        if not ambiance:
            ambiance = choice(list(ambiance_time.keys()))

        # Apply random gain, fade in, and loop the ambiance sound
        ambiance = ambiance.apply_gain((gain_ambiance + randint(-5, 5)) - ambiance.dBFS)
        ambiance_loop = ambiance.fade_in(fade_ambiance)
        while len(ambiance_loop) < len(combined):
            ambiance_loop = ambiance_loop.append(ambiance, 0)
        combined = combined.overlay(ambiance_loop)

        # Add rain sounds to the episode if topic contains keywords or randomly
        rain_intensity = None
        if randrange(5) == 0:
            rain_intensity = randint(-5, 5)
        for text in (topic_lower, script_lower):
            if any(word in text for word in storm_keywords):
                rain_intensity = randint(1, 5)
                break
            elif any(word in text for word in rain_keywords):
                rain_intensity = randint(-5, 0)
                break
            elif any(word in text for word in clear_keywords):
                rain_intensity = None
                break
        if rain_intensity is not None:

            # Apply random gain, fade in, and loop the rain sound
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

        # Check if the lag fish should appear
        if "release the fish" in topic_lower or "release the fish" in script_lower:
            output_embed.set_thumbnail(url=emojis["lagfish"].url)

        # Export the episode and send it
        with BytesIO() as output:
            combined.export(output, "mp3", bitrate="384k")
            await interaction.edit_original_response(embed=output_embed, attachments=[
                File(output, f"{file_title}.mp3")])

        # Set cooldown for user
        end_time = int(time())
        episode_cooldowns[interaction.user.id] = end_time

        # Record successful episode generation in statistics
        with open("statistics.txt", "a") as file:
            file.write(f"E {end_time}\n")

    # Generation failed
    except Exception as e:
        print(e)
        await interaction.edit_original_response(embed=embed_generation_failed)

    # Unblock generation for all users
    finally:
        episode_generating = False
        await client.change_presence(activity=activity_ready, status=Status.online)


@command_tree.command(description="Chat with a character.")
@app_commands.describe(character="Character to chat with.", message="Message to send.")
@app_commands.allowed_installs(True, True)
@app_commands.allowed_contexts(True, True, True)
async def chat(interaction: Interaction, character: characters_literal, message: app_commands.Range[str, char_limit_min, char_limit_max]):
    """
    Chat with one of the characters, excluding alts and "all".
    :param interaction: Interaction created by the command
    :param character: Character to chat with
    :param message: Message to send to the character
    :return: None
    """

    # Check if the user is banned
    if interaction.user.id in bans:
        await interaction.response.send_message(embed=embed_banned, file=File("img/explodeward.gif"), ephemeral=True, delete_after=embed_delete_after)
        return

    # Check if the user is on cooldown
    current_time = int(time())
    if interaction.user.id in chat_cooldowns.keys() and current_time - chat_cooldowns[interaction.user.id] <= chat_cooldown:
        await interaction.response.send_message(ephemeral=True, delete_after=embed_delete_after, embed=Embed(title=f"Command on cooldown.", description=f"You can generate another chat in `{chat_cooldown - (current_time - chat_cooldowns[interaction.user.id])}s`.", color=embed_color))
        return

    # Check if the user is using already generating a chat
    if interaction.user.id in chat_generating:
        await interaction.response.send_message(embed=embed_in_use_chat, ephemeral=True, delete_after=embed_delete_after)
        return

    # Start generation
    try:

        # Block generation for this user
        chat_generating.add(interaction.user.id)

        # Show the generating message
        await interaction.response.send_message(embed=embed_generating_chat)

        # Log the interaction
        await logging_channel.send(embed=Embed(title=interaction.user.id, description=f"/chat character:{character} message:{utils.escape_markdown(message)}", color=embed_color))

        # Generate the chat response using OpenAI
        character_title = character.title().replace("bob", "Bob")
        completion = await openai.completions.create(
            model="gpt-3.5-turbo-instruct",
            max_tokens=250,
            prompt=f"Create a brief, chaotic, and morally incorrect response to a Discord message as {character_title} from SpongeBob SquarePants. Use the format: {character_title}: <response>. Only reply with {character_title}'s coherent response. The message from \"{interaction.user.display_name}\" is: \"{message}\"."
        )

        # Clean the response text
        output = utils.escape_markdown(completion.choices[0].text.replace("\n\n", "\n").replace(":\n", ": ").strip().split("\n")[0].split(":", 1)[1].strip())
        if len(output) > char_limit_max:
            output = output[:char_limit_max - 3] + "..."

        # Send the response
        await interaction.edit_original_response(embed=Embed(description=output, color=characters[character][1]).set_footer(text=message, icon_url=interaction.user.display_avatar.url).set_author(name=character_title, icon_url=emojis[character.replace(' ', '').replace('.', '')].url))

        # Set cooldown for user
        end_time = int(time())
        chat_cooldowns[interaction.user.id] = end_time

        # Record successful chat generation in statistics
        with open("statistics.txt", "a") as file:
            file.write(f"C {end_time}\n")

    # Generation failed
    except Exception as e:
        print(e)
        await interaction.edit_original_response(embed=embed_generation_failed)

    # Unblock generation for this user
    finally:
        chat_generating.discard(interaction.user.id)


@command_tree.command(description="Synthesize character speech.")
@app_commands.describe(character="Voice to use.", text="Text to speak.")
@app_commands.allowed_installs(True, True)
@app_commands.allowed_contexts(True, True, True)
async def tts(interaction: Interaction, character: characters_literal, text: app_commands.Range[str, char_limit_min, char_limit_max]):
    """
    Synthesize text-to-speech for a character, excluding alts and "all".
    :param interaction: Interaction created by the command
    :param character: Character voice to use for TTS
    :param text: Text to speak
    :return: None
    """

    # Check if the user is banned
    if interaction.user.id in bans:
        await interaction.response.send_message(embed=embed_banned, file=File("img/explodeward.gif"), ephemeral=True, delete_after=embed_delete_after)
        return

    # Check if the user is on cooldown
    current_time = int(time())
    if interaction.user.id in tts_cooldowns.keys() and current_time - tts_cooldowns[interaction.user.id] <= tts_cooldown:
        await interaction.response.send_message(ephemeral=True, delete_after=embed_delete_after, embed=Embed(title=f"Command on cooldown.", description=f"You can generate another TTS in `{tts_cooldown - (current_time - tts_cooldowns[interaction.user.id])}s`.", color=embed_color))
        return

    # Check if the user is using already generating TTS
    if interaction.user.id in tts_generating:
        await interaction.response.send_message(embed=embed_in_use_tts, ephemeral=True, delete_after=embed_delete_after)
        return

    # Check if an episode is generating
    if episode_generating:
        await interaction.response.send_message(embed=embed_in_use_tts_episode, ephemeral=True, delete_after=embed_delete_after)
        return

    # Start generation
    try:

        # Block generation for this user
        tts_generating.add(interaction.user.id)

        # Show the generating message
        await interaction.response.send_message(embed=embed_generating_tts)

        # Log the interaction
        await logging_channel.send(embed=Embed(title=interaction.user.id, description=f"/tts character:{character} text:{utils.escape_markdown(text)}", color=embed_color))

        # Loop to run FakeYou requests in
        loop = get_running_loop()

        # Synthesize speech using voice files for DoodleBob
        if character == "doodlebob":
            seg = choice(voice_doodlebob)

        # Synthesize speech using voice files for Gary
        elif character == "gary":
            seg = choice(voice_gary)

        # Synthesize speech using FakeYou for all other characters
        else:
            fy_tts = await wait_for(loop.run_in_executor(None, fakeyou.say, text, characters[character][0]), fakeyou_timeout)
            with BytesIO(fy_tts.content) as wav:
                seg = AudioSegment.from_wav(wav)
            await sleep(10)

        # Apply gain, forcing a loud event if the text is uppercase
        if text.isupper():
            seg = seg.apply_gain(gain_voice_distort)
            seg = seg.apply_gain(gain_voice_loud-seg.dBFS)
        else:
            seg = seg.apply_gain(gain_voice-seg.dBFS)

        # Export and send the file
        with BytesIO() as output:
            seg.export(output, "mp3", bitrate="384k")
            character_title = character.title().replace('bob', 'Bob')
            await interaction.edit_original_response(embed=Embed(color=characters[character][1]).set_footer(text=text, icon_url=interaction.user.display_avatar.url).set_author(name=character_title, icon_url=emojis[character.replace(' ', '').replace('.', '')].url), attachments=[
                File(output, f"{character_title} — {text}.mp3")])

        # Set cooldown for user
        end_time = int(time())
        tts_cooldowns[interaction.user.id] = end_time

        # Record successful TTS generation in statistics
        with open("statistics.txt", "a") as file:
            file.write(f"T {end_time}\n")

    # Generation failed
    except Exception as e:
        print(e)
        await interaction.edit_original_response(embed=embed_generation_failed)

    # Unblock generation for this user
    finally:
        tts_generating.discard(interaction.user.id)


@command_tree.command(description="Show bot statistics.")
@app_commands.allowed_installs(True, True)
@app_commands.allowed_contexts(True, True, True)
async def stats(interaction: Interaction):
    """
    Show bot statistics including episode, chat, and TTS counts, guilds, latency, and uptime.
    :param interaction: Interaction created by the command
    :return: None
    """

    # Initialize count variables
    episodes_24h = 0
    episodes_all = 0
    chats_24h = 0
    chats_all = 0
    tts_24h = 0
    tts_all = 0

    # Get current time for stat parsing and uptime calculation
    current_time = int(time())

    # Read the stats file and calculate counts
    if path.exists("statistics.txt"):
        with open("statistics.txt", "r") as file:
            for line in file:
                line_parts = line.strip().split(" ")

                # Episodes
                if line_parts[0] == "E":
                    episodes_all += 1
                    if current_time - int(line_parts[1]) < 86400:
                        episodes_24h += 1

                # Chats
                elif line_parts[0] == "C":
                    chats_all += 1
                    if current_time - int(line_parts[1]) < 86400:
                        chats_24h += 1

                # TTS
                elif line_parts[0] == "T":
                    tts_all += 1
                    if current_time - int(line_parts[1]) < 86400:
                        tts_24h += 1

    # Calculate uptime
    uptime = int(current_time - start_time)

    # Format uptime
    uptime_formatted = ""
    days = uptime // 86400
    if days > 0:
        uptime_formatted += f"{days}d "
    hours = (uptime % 86400) // 3600
    if hours > 0:
        uptime_formatted += f"{hours}h "
    minutes = (uptime % 3600) // 60
    if minutes > 0:
        uptime_formatted += f"{minutes}m "
    seconds = uptime % 60
    if seconds > 0:
        uptime_formatted += f"{seconds}s"

    # Send the statistics message
    await interaction.response.send_message(embed=Embed(color=embed_color)
                                      .add_field(name="Episodes", value=f"24h: `{episodes_24h}`\nAll: `{episodes_all}`", inline=False)
                                      .add_field(name="Chats", value=f"24h: `{chats_24h}`\nAll: `{chats_all}`", inline=False)
                                      .add_field(name="TTS", value=f"24h: `{tts_24h}`\nAll: `{tts_all}`", inline=False)
                                      .add_field(name="Bot", value=f"Guilds: `{len(client.guilds)}`\nLatency: `{int(1000 * client.latency)}ms`\nUptime: `{uptime_formatted}`", inline=False),
                                      ephemeral=True, delete_after=embed_delete_after)


@command_tree.command(description="Show bot help.")
@app_commands.allowed_installs(True, True)
@app_commands.allowed_contexts(True, True, True)
async def help(interaction: Interaction):
    """
    Show the bot help message.
    :param interaction: Interaction created by the command
    :return: None
    """

    # Show the help message
    await interaction.response.send_message(embed=embed_help, ephemeral=True, delete_after=embed_delete_after, view=ui.View().add_item(button_help))


@command_tree.command(description="Ban a user.", guild=moderation_guild)
@app_commands.describe(id="ID of user.")
@app_commands.allowed_installs(True, False)
@app_commands.allowed_contexts(True, False, True)
@app_commands.default_permissions(ban_members=True)
async def ban(interaction: Interaction, id: app_commands.Range[str, 17, 19]):
    """
    Ban a user by their ID.
    :param interaction: Interaction created by the command
    :param id: ID of the user to ban
    :return: None
    """

    # Check that the user ID is valid
    try:
        id = int(id)
        await client.fetch_user(id)
    except NotFound as e:
        print(e)
        await interaction.response.send_message(embed=embed_unknown_user, ephemeral=True, delete_after=embed_delete_after)
        return

    # Check that the user is not already banned
    if id in bans:
        await interaction.response.send_message(embed=embed_already_banned, ephemeral=True, delete_after=embed_delete_after)
        return

    # Add the user to the bans list and file
    bans.add(id)
    with open("bans.txt", "a") as file:
        file.write(f"{id}\n")

    # Show the ban message
    await interaction.response.send_message(embed=Embed(title="Banned user.", description=f"{id}", color=embed_color))


@command_tree.command(description="Unban a user.", guild=moderation_guild)
@app_commands.describe(id="ID of user.")
@app_commands.allowed_installs(True, False)
@app_commands.allowed_contexts(True, False, True)
@app_commands.default_permissions(ban_members=True)
async def unban(interaction: Interaction, id: app_commands.Range[str, 17, 19]):
    """
    Unban a user by their ID.
    :param interaction: Interaction created by the command
    :param id: ID of the user to unban
    :return: None
    """

    # Check that the user ID is valid
    try:
        id = int(id)
        await client.fetch_user(id)
    except NotFound as e:
        print(e)
        await interaction.response.send_message(embed=embed_unknown_user, ephemeral=True, delete_after=embed_delete_after)
        return

    # Check that the user is banned
    if id not in bans:
        await interaction.response.send_message(embed=embed_not_banned, ephemeral=True, delete_after=embed_delete_after)
        return

    # Remove the user from the ban list and file
    bans.discard(id)
    with open("bans.txt", "w") as file:
        for line in bans:
            file.write(f"{line}\n")

    # Show the unban message
    await interaction.response.send_message(embed=Embed(title="Unbanned user.", description=f"{id}", color=embed_color))


@command_tree.command(description="Clear recent logs.", guild=moderation_guild)
@app_commands.allowed_installs(True, False)
@app_commands.allowed_contexts(True, False, True)
@app_commands.default_permissions(manage_messages=True)
async def clear(interaction: Interaction):
    """
    Clear the 500 most recent logs from the logging channel.
    :param interaction: Interaction created by the command
    :return: None
    """

    # Show the clearing message
    await interaction.response.send_message(embed=embed_clearing_logs)
    response = await interaction.original_response()

    # Purge messages from the logging channel
    deleted = len(await logging_channel.purge(limit=500, check=lambda message: message.author == client.user and message != response))

    # Show how many messages were deleted
    await interaction.edit_original_response(embed=Embed(title="Cleared recent logs.", description=f"Deleted `{deleted}` message{('s' if deleted == 0 or deleted > 1 else '')}.", color=embed_color))


@client.event
async def on_ready():
    """
    Final initializations once the bot has logged in to the Discord API. If this fails, the program will stop.
    :return: None
    """

    try:

        # Fetch logging channel and all emojis
        global logging_channel, emojis
        logging_channel = await client.fetch_channel(int(getenv("LOGGING_CHANNEL_ID")))
        emojis = {e.name: e for e in await client.fetch_application_emojis()}
        for alt in characters["all"][2]:
            emojis[alt] = emojis["all"]

        # Sync command trees
        await command_tree.sync()
        await command_tree.sync(guild=moderation_guild)

        # Set status to ready
        await client.change_presence(activity=activity_ready, status=Status.online)

    # Stop bot if any of the above fails
    except Exception as e:
        print(e)
        exit(1)


# Start bot (must be at the end of the file)
client.run(getenv("DISCORD_BOT_TOKEN"))
