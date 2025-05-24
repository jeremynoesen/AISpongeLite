import asyncio
import math
import random
import re
import time
import discord
import os

import pydub.effects
from dotenv import load_dotenv
from discord import app_commands
from io import BytesIO
from fakeyou import FakeYou
from openai import AsyncOpenAI
from pydub import AudioSegment


def load_wav(path, gain=None):
    seg = AudioSegment.from_wav(path)
    if gain is not None:
        seg = seg.apply_gain(gain - seg.dBFS)
    return seg


load_dotenv()
openai = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
fakeyou = FakeYou()
fakeyou.login(os.getenv("FAKEYOU_USERNAME"), os.getenv("FAKEYOU_PASSWORD"))
fakeyou_timeout = 120
client = discord.Client(intents=discord.Intents.default(), activity=discord.Game("Ready"), status=discord.Status.online)
command_tree = app_commands.CommandTree(client)
embed_color_dark = 0x7f9400
embed_color_light = 0xf5f306
embed_delete_after = 10
embed_ready = discord.Embed(title="Ready", description="# 📺", color=embed_color_light).set_footer(text="Ready to generate.")
embed_help = discord.Embed(title="See the App Directory for bot help.", description="You will also find links to the support server and source code there.", color=embed_color_light)
help_button = discord.ui.Button(style=discord.ButtonStyle.link, label="App Directory", url="https://discord.com/application-directory/1254296070599610469")
embed_generating_chat = discord.Embed(title="Generating...", description="# 💬", color=embed_color_light).set_footer(text=f"Sending message...")
embed_generating_tts = discord.Embed(title="Generating...", description="# 🔊", color=embed_color_light).set_footer(text=f"Synthesizing speech...")
embed_error_permissions = discord.Embed(title="Generating...", description="# Failed", color=embed_color_dark).set_footer(text="Missing permissions.")
embed_error_failed = discord.Embed(title="Generating...", description="# Failed", color=embed_color_dark).set_footer(text="An error occurred.")
embed_error_character = discord.Embed(title="Generating...", description="# Failed", color=embed_color_dark).set_footer(text="Invalid character.")
embed_error_busy = discord.Embed(title="Generating...", description="# Failed", color=embed_color_dark).set_footer(text="Unavailable during episode generation.")
remove_cooldown_sku = int(os.getenv("REMOVE_COOLDOWN_SKU"))
remove_cooldown_button = discord.ui.Button(style=discord.ButtonStyle.premium, sku_id=remove_cooldown_sku)
characters = {"spongebob": ("weight_5by9kjm8vr8xsp7abe8zvaxc8", os.getenv("EMOJI_SPONGEBOB"), False),
              "freakbob": ("weight_5by9kjm8vr8xsp7abe8zvaxc8", os.getenv("EMOJI_FREAKBOB"), True),
              "sadbob": ("weight_5by9kjm8vr8xsp7abe8zvaxc8", os.getenv("EMOJI_SADBOB"), True),
              "nerdbob": ("weight_5by9kjm8vr8xsp7abe8zvaxc8", os.getenv("EMOJI_NERDBOB"), True),
              "patrick": ("weight_154man2fzg19nrtc15drner7t", os.getenv("EMOJI_PATRICK"), False),
              "shortrick": ("weight_154man2fzg19nrtc15drner7t", os.getenv("EMOJI_SHORTRICK"), True),
              "widerick": ("weight_154man2fzg19nrtc15drner7t", os.getenv("EMOJI_WIDERICK"), True),
              "pinhead": ("weight_154man2fzg19nrtc15drner7t", os.getenv("EMOJI_PINHEAD"), True),
              "squidward": ("TM:3psksme51515", os.getenv("EMOJI_SQUIDWARD"), False),
              "loudward": ("TM:3psksme51515", os.getenv("EMOJI_LOUDWARD"), True),
              "schizoward": ("TM:3psksme51515", os.getenv("EMOJI_SCHIZOWARD"), True),
              "shadeward": ("TM:3psksme51515", os.getenv("EMOJI_SHADEWARD"), True),
              "skodwarde": ("TM:3psksme51515", os.getenv("EMOJI_SKODWARDE"), True),
              "spinward": ("TM:3psksme51515", os.getenv("EMOJI_SPINWARD"), True),
              "gary": ("weight_ak3kb7kvye39r6c63tydsveyy", os.getenv("EMOJI_GARY"), False),
              "plankton": ("weight_ahxbf2104ngsgyegncaefyy6j", os.getenv("EMOJI_PLANKTON"), False),
              "loudton": ("weight_ahxbf2104ngsgyegncaefyy6j", os.getenv("EMOJI_LOUDTON"), True),
              "dickton": ("weight_ahxbf2104ngsgyegncaefyy6j", os.getenv("EMOJI_DICKTON"), True),
              "servedton": ("weight_ahxbf2104ngsgyegncaefyy6j", os.getenv("EMOJI_SERVEDTON"), True),
              "suston": ("weight_ahxbf2104ngsgyegncaefyy6j", os.getenv("EMOJI_SUSTON"), True),
              "dr. jr.": ("weight_ahxbf2104ngsgyegncaefyy6j", os.getenv("EMOJI_DR_JR"), True),
              "mr. krabs": ("weight_5bxbp9xqy61svfx03b25ezmwx", os.getenv("EMOJI_MR_KRABS"), False),
              "shadowkrabs": ("weight_5bxbp9xqy61svfx03b25ezmwx", os.getenv("EMOJI_SHADOWKRABS"), True),
              "karen": ("weight_eckp92cd68r4yk68n6re3fwcb", os.getenv("EMOJI_KAREN"), False),
              "sandy": ("weight_tzgp5df2xzwz7y7jzz7at96jf", os.getenv("EMOJI_SANDY"), False),
              "mrs. puff": ("weight_129qhgze57zhndkkcq83e6b2a", os.getenv("EMOJI_MRS_PUFF"), False),
              "squilliam": ("weight_zmjv8223ed6wx1fp234c79v9s", os.getenv("EMOJI_SQUILLIAM"), False),
              "larry": ("weight_k7qvaffwsft6vxbcps4wbyj58", os.getenv("EMOJI_LARRY"), False),
              "bubble bass": ("weight_h9g7rh6tj2hvfezrz8gjs4gwa", os.getenv("EMOJI_BUBBLE_BASS"), False),
              "bubble buddy": ("weight_sbr0372ysxbdahcvej96axy1t", os.getenv("EMOJI_BUBBLE_BUDDY"), False),
              "doodlebob": (None, os.getenv("EMOJI_DOODLEBOB"), False),
              "french narrator": ("weight_edzcfmq6y0vj7pte9pzhq5b6j", os.getenv("EMOJI_FRENCH_NARRATOR"), False),
              "all": (None, os.getenv("EMOJI_ALL"), True)}
ambiance_gain = -45
ambiance_time = [load_wav("ambiance/day.wav", gain=ambiance_gain),
                 load_wav("ambiance/night.wav", gain=ambiance_gain)]
ambiance_rain = load_wav("ambiance/rain.wav")
music_gain = -35
songs = {load_wav("music/closing_theme.wav", gain=music_gain): 10,
         load_wav("music/tip_top_polka.wav", gain=music_gain): 10,
         load_wav("music/rake_hornpipe.wav", gain=music_gain): 10,
         load_wav("music/seaweed.wav", gain=music_gain): 10,
         load_wav("music/hello_sailor_b.wav", gain=music_gain): 5,
         load_wav("music/stars_and_games.wav", gain=music_gain): 5,
         load_wav("music/comic_walk.wav", gain=music_gain): 5,
         load_wav("music/rock_bottom.wav", gain=music_gain): 5,
         load_wav("music/grass_skirt_chase.wav", gain=music_gain): 1,
         load_wav("music/gator.wav", gain=music_gain): 1,
         load_wav("music/sneaky_snitch.wav", gain=music_gain): 1,
         load_wav("music/better_call_saul.wav", gain=music_gain): 1}
sfx_gain = -20
sfx = {AudioSegment.from_mp3("sfx/car.mp3"): 10,
       load_wav("sfx/steel_sting.wav"): 5,
       load_wav("sfx/boowomp.wav"): 5,
       load_wav("sfx/foghorn.wav"): 1,
       load_wav("sfx/vibe_link_b.wav"): 1,
       load_wav("sfx/this_guy_stinks.wav"): 1,
       load_wav("sfx/my_leg_1.wav"): 1,
       load_wav("sfx/my_leg_2.wav"): 1,
       load_wav("sfx/you_what.wav"): 1,
       load_wav("sfx/dolphin.wav"): 1,
       load_wav("sfx/boo_you_stink.wav"): 1,
       load_wav("sfx/bonk.wav"): 1,
       load_wav("sfx/fling_1.wav"): 1,
       load_wav("sfx/fling_2.wav"): 1,
       load_wav("sfx/kick.wav"): 1,
       load_wav("sfx/kiss.wav"): 1,
       load_wav("sfx/squish_1.wav"): 1,
       load_wav("sfx/squish_2.wav"): 1,
       load_wav("sfx/dramatic_cue.wav"): 1}
sfx_transition = load_wav("sfx/transition.wav", gain=sfx_gain)
sfx_food = [load_wav("sfx/burp.wav")]
sfx_ball = [load_wav("sfx/ball.wav")]
sfx_gun = [load_wav(f"sfx/gun_{i}.wav") for i in range(1, 3)]
sfx_molotov = [load_wav("sfx/molotov.wav")]
sfx_bomb = [load_wav("sfx/bomb_fuse.wav", gain=ambiance_gain) + load_wav("sfx/bomb_explosion.wav", gain=sfx_gain)]
sfx_strike = load_wav("sfx/lightning.wav")
voice_gary = [AudioSegment.from_wav(f"voice/gary_{i}.wav") for i in range(1, 7)]
voice_doodlebob = [AudioSegment.from_wav(f"voice/doodlebob_{i}.wav") for i in range(1, 9)]
silence_line = AudioSegment.silent(200)
silence_transition = AudioSegment.silent(600)
silence_music = AudioSegment.silent(3000)
episode_generating = False
episode_progress = 0
episode_cooldown = 300
episode_cooldowns = {}
start_time = int(time.time())


@command_tree.command(name="episode", description="Generate an episode.")
@app_commands.describe(topic="Topic of episode.")
async def episode(inter: discord.Interaction, topic: str = ""):
    global episode_generating, episode_progress
    if inter.user.id in episode_cooldowns.keys() and int(time.time()) - episode_cooldowns[inter.user.id] <= episode_cooldown:
        remaining = episode_cooldown - (int(time.time()) - episode_cooldowns[inter.user.id])
        remaining_formatted = ""
        minutes = remaining // 60
        if minutes > 0:
            remaining_formatted += f"{minutes}m "
        seconds = remaining % 60
        if seconds > 0:
            remaining_formatted += f"{seconds}s"
        await inter.response.send_message(ephemeral=True, delete_after=embed_delete_after, embed=discord.Embed(title=f"Cooldown", description=f"# `{remaining_formatted}`", color=embed_color_light).set_footer(text="You're on cooldown."), view=discord.ui.View().add_item(remove_cooldown_button))
        return
    if episode_generating:
        await inter.response.send_message(ephemeral=True, delete_after=embed_delete_after, embed=discord.Embed(title="Generating", description=f"# `{episode_progress}%`", color=embed_color_light).set_footer(text="Generating an episode."))
        return
    if not topic:
        await inter.response.send_message(ephemeral=True, delete_after=embed_delete_after, embed=embed_ready)
        return
    if not inter.app_permissions.use_external_emojis:
        await inter.response.send_message(embed=embed_error_permissions)
        return
    try:
        episode_generating = True
        episode_progress = 0
        await inter.response.send_message(embed=discord.Embed(title="Generating...", description=f"# `{episode_progress}%`", color=embed_color_light).set_footer(text=f"Preparing episode..."))
        await client.change_presence(activity=discord.Game(f"Generating... {episode_progress}%"), status=discord.Status.dnd)
        completion = await openai.completions.create(
            model="gpt-3.5-turbo-instruct",
            max_tokens=700,
            prompt=f"Create a profanity-filled, morally incorrect script for a scene from SpongeBob SquarePants where characters discuss a topic. Common characters include SpongeBob, Patrick, Squidward, Mr. Krabs, Plankton, Karen, and Sandy. Rare characters include Gary, Larry, Mrs. Puff, Squilliam, Bubble Bass, Bubble Buddy, DoodleBob, and French Narrator. Include 3 - 5 characters max. Use the format: Character: <dialogue>. Only reply with uncensored, coherent character dialogue. Around 12 - 15 lines of dialogue with talking only. The first line is a relevant 1 - 2 word title with format: Title: <title>. The topic is: {topic}."
        )
        lines = re.sub(r"(^|\s+)(\(+\S[^()]+\S\)+|\[+\S[^\[\]]+\S]+|\*+\S[^*]+\S\*+|<+\S[^<>]+\S>+|\{+\S[^{}]+\S}+|-+\S[^-]+\S-+|\|+\S[^|]+\S\|+|/+\S[^/]+\S/+|\\+\S[^\\]+\S\\+)(\s+|$)", r"\3", completion.choices[0].text).replace("\n\n", "\n").replace(":\n", ": ").replace("  ", " ").strip().split("\n")
        remaining = len(lines)
        line = lines.pop(0).strip()
        title = line.split(":")[0].lower()
        if title.strip() == "title":
            line = line[len(title) + 1:].strip()
            if line[0] == line[-1] == "\"" or line[0] == line[-1] == "'":
                line = line[1:-1].strip()
            file_title = line.upper().replace("I", "i")
            embed_title = ""
            for character in discord.utils.escape_markdown(line):
                if character.isupper() or character.isnumeric() or character in ".,!?":
                    embed_title += f"**{character}**"
                else:
                    embed_title += character
            embed_title = embed_title.upper().replace("I", "i")
        else:
            file_title = "UNTiTLED EPiSODE"
            embed_title = "**U**NTiTLED **E**PiSODE"
        completed = 1
        episode_progress = int(100 * (completed / remaining))
        await inter.edit_original_response(embed=discord.Embed(title="Generating...", description=f"# `{episode_progress}%`", color=embed_color_light).set_footer(text=f"Generated script."))
        await client.change_presence(activity=discord.Game(f"Generating... {episode_progress}%"), status=discord.Status.dnd)
        transcript = []
        foods = []
        balls = []
        guns = []
        molotovs = []
        bombs = []
        spoken_characters = set()
        combined = AudioSegment.empty()
        loop = asyncio.get_running_loop()
        for line in lines:
            line = line.strip()
            character = line.split(":")[0].lower()
            character_stripped = character.strip()
            if character_stripped in characters.keys() or any(x in character_stripped for x in ["all", "every", "unison", "together"]):
                line_stripped = line[len(character) + 1:].strip()
                if any(x in character_stripped for x in ["all", "every", "unison", "together"]):
                    line = f"{characters['all'][1]} {line_stripped}"
                    segs = []
                    for character in spoken_characters:
                        fy_tts = await asyncio.wait_for(loop.run_in_executor(None, fakeyou.say, line_stripped, characters[character][0]), fakeyou_timeout)
                        with BytesIO(fy_tts.content) as wav:
                            segs.append(AudioSegment.from_wav(wav))
                        await asyncio.sleep(5)
                    segs.sort(key=lambda x: -len(x))
                    seg = segs[0]
                    for i in range(1, len(segs)):
                        seg = seg.overlay(segs[i], 0)
                elif character_stripped == "doodlebob":
                    line = f"{characters['doodlebob'][1]} {line_stripped}"
                    seg = random.choice(voice_doodlebob)
                elif character_stripped == "gary" and bool(re.fullmatch(r"(\W*m+e+o+w+\W*)+", line_stripped, re.IGNORECASE)):
                    spoken_characters.add(character_stripped)
                    line = f"{characters['gary'][1]} {line_stripped}"
                    seg = random.choice(voice_gary)
                else:
                    spoken_characters.add(character_stripped)
                    line = f"{characters[character_stripped][1]} {line_stripped}"
                    fy_tts = await asyncio.wait_for(loop.run_in_executor(None, fakeyou.say, line_stripped, characters[character_stripped][0]), fakeyou_timeout)
                    with BytesIO(fy_tts.content) as wav:
                        seg = AudioSegment.from_wav(wav)
                    await asyncio.sleep(5)
                seg = pydub.effects.strip_silence(seg, 1000, -80, 0)
                if "loud" in character_stripped or line_stripped.isupper() or random.randrange(100) == 0:
                    seg = seg.apply_gain(20)
                    seg = seg.apply_gain(-10-seg.dBFS)
                    line = line.replace(line_stripped, line_stripped.upper())
                else:
                    seg = seg.apply_gain(-15-seg.dBFS)
                line_stripped_lower = line_stripped.lower()
                for keywords, collection in [(["krabby patt", "food", "burger", "hungry", "ice cream", "pizza"], foods),
                                             (["ball"], balls),
                                             (["shoot", "shot", "kill", "murder", "gun"], guns),
                                             (["fire", "molotov", "burn", "flame"], molotovs),
                                             (["boom", "bomb", "explosion", "explode", "fire in the hole"], bombs)]:
                    if any(x in line_stripped_lower for x in keywords) and not ("fire" in keywords and "fire in the hole" in line_stripped_lower):
                        collection.append(len(combined) + random.randrange(len(seg)))
                combined = combined.append(seg, 0)
                if line[-1] in "-–—":
                    line = line[:-1] + "—"
                elif random.randrange(10) == 0:
                    while line[-1] in ".!?…":
                        line = line[:-1]
                    line += "—"
                else:
                    combined = combined.append(silence_line, 0)
                transcript.append(f"- {discord.utils.escape_markdown(line)}")
                completed += 1
                episode_progress = int(100 * (completed / remaining))
                await inter.edit_original_response(embed=discord.Embed(title="Generating...", description=f"# `{episode_progress}%`", color=embed_color_light).set_footer(text=f"Synthesized line {completed - 1}/{remaining - 1}."))
            else:
                remaining -= 1
                episode_progress = int(100 * (completed / remaining))
                await inter.edit_original_response(embed=discord.Embed(title="Generating...", description=f"# `{episode_progress}%`", color=embed_color_light).set_footer(text=f"Skipped line."))
            await client.change_presence(activity=discord.Game(f"Generating... {episode_progress}%"), status=discord.Status.dnd)
        combined = combined.append(silence_line, 0)
        if random.randrange(20) > 0:
            music = random.choices(list(songs.keys()), list(songs.values()))[0]
            music_loop = silence_music.append(music.fade_in(10000), 0)
            while len(music_loop) < len(combined):
                music_loop = music_loop.append(music, 0)
            combined = combined.overlay(music_loop)
        if random.randrange(10) > 0:
            ambiance = random.choice(ambiance_time)
            ambiance_loop = ambiance.fade_in(500)
            while len(ambiance_loop) < len(combined):
                ambiance_loop = ambiance_loop.append(ambiance, 0)
            combined = combined.overlay(ambiance_loop)
        if random.randrange(5) == 0:
            rain_intensity = random.randint(-5, 5)
            rain_randomized = ambiance_rain.apply_gain((ambiance_gain + rain_intensity) - ambiance_rain.dBFS)
            rain_loop = rain_randomized.fade_in(500)
            while len(rain_loop) < len(combined):
                rain_loop = rain_loop.append(rain_randomized, 0)
            combined = combined.overlay(rain_loop)
            if rain_intensity > 0:
                for i in range(random.randint(1, math.ceil(len(transcript) / 10))):
                    combined = combined.overlay(sfx_strike.apply_gain((sfx_gain + random.randint(-10 + rain_intensity, 0)) - sfx_strike.dBFS), random.randrange(len(combined)))
        for items, item_sfx in [(foods, sfx_food), (balls, sfx_ball), (guns, sfx_gun), (molotovs, sfx_molotov), (bombs, sfx_bomb)]:
            for item in items:
                if random.randrange(5) > 0:
                    choice = random.choice(item_sfx)
                    combined = combined.overlay(choice.apply_gain((sfx_gain + random.randint(-10, 0)) - choice.dBFS), item)
        combined = silence_transition.append(combined, 0).overlay(sfx_transition)
        for i in range(random.randint(1, math.ceil(len(transcript) / 5))):
            choice = random.choices(list(sfx.keys()), list(sfx.values()))[0]
            combined = combined.overlay(choice.apply_gain((sfx_gain + random.randint(-5, 5)) - choice.dBFS), random.randrange(len(combined)))
        combined = combined.fade_out(200)
        with BytesIO() as output:
            combined.export(output, "ogg")
            await inter.edit_original_response(embed=discord.Embed(title=embed_title, description="\n".join(transcript) + f"\n\n-# > *{discord.utils.escape_markdown(topic)}*", color=embed_color_light), attachments=[discord.File(output, f"{file_title}.ogg")])
        end_time = int(time.time())
        remove_cooldown = False
        for entitlement in inter.entitlements:
            if entitlement.sku_id == remove_cooldown_sku and not entitlement.is_expired():
                remove_cooldown = True
                break
        if not remove_cooldown:
            episode_cooldowns[inter.user.id] = end_time
        with open("statistics.txt", "a") as file:
            file.write(f"E {end_time}\n")
    except:
        try:
            await inter.edit_original_response(embed=embed_error_failed)
        except:
            pass
    await client.change_presence(activity=discord.Game("Ready"), status=discord.Status.online)
    episode_generating = False


async def character_autocomplete(interaction: discord.Interaction, current: str,):
    return [app_commands.Choice(name=character, value=character) for character in [character.title().replace("bob", "Bob") for character in characters.keys() if not characters[character][2]] if current.lower() in character.lower()]


@command_tree.command(name="chat", description="Chat with a character.")
@app_commands.describe(character="Character to chat with.")
@app_commands.describe(message="Message to send.")
@app_commands.autocomplete(character=character_autocomplete)
async def chat(inter: discord.Interaction, character: str, message: str):
    character = character.lower()
    if character not in characters.keys() or characters[character][2]:
        await inter.response.send_message(ephemeral=True, delete_after=embed_delete_after, embed=embed_error_character)
        return
    try:
        emoji = characters[character][1]
        character = character.title().replace("bob", "Bob")
        await inter.response.send_message(embed=embed_generating_chat)
        completion = await openai.completions.create(
            model="gpt-3.5-turbo-instruct",
            max_tokens=250,
            prompt=f"You are {character} from SpongeBob SquarePants chatting with {inter.user.display_name} on Discord. Only respond with a brief, exaggerated response. {inter.user.display_name} says: {message}."
        )
        output = discord.utils.escape_markdown(re.compile(re.escape(f"{character}:"), re.IGNORECASE).sub("", completion.choices[0].text.strip(), 1).strip())
        if output[0] == output[-1] == "\"" or output[0] == output[-1] == "'":
            output = output[1:-1].strip()
        await inter.edit_original_response(embed=discord.Embed(description=f"{output}\n\n-# > *{discord.utils.escape_markdown(message)}*", color=embed_color_light).set_author(name=character, icon_url=client.get_emoji(int(emoji.split(":")[-1][:-1])).url))
        with open("statistics.txt", "a") as file:
            file.write(f"C {int(time.time())}\n")
    except:
        try:
            await inter.edit_original_response(embed=embed_error_failed)
        except:
            pass


@command_tree.command(name="tts", description="Synthesize character speech.")
@app_commands.describe(character="Voice to use.")
@app_commands.describe(text="Text to speak.")
@app_commands.autocomplete(character=character_autocomplete)
async def tts(inter: discord.Interaction, character: str, text: str):
    character = character.lower()
    if character not in characters.keys() or characters[character][2]:
        await inter.response.send_message(ephemeral=True, delete_after=embed_delete_after, embed=embed_error_character)
        return
    if episode_generating:
        await inter.response.send_message(ephemeral=True, delete_after=embed_delete_after, embed=embed_error_busy)
        return
    if not inter.app_permissions.use_external_emojis:
        await inter.response.send_message(embed=embed_error_permissions)
        return
    try:
        await inter.response.send_message(embed=embed_generating_tts)
        loop = asyncio.get_running_loop()
        if character == "doodlebob":
            seg = random.choice(voice_doodlebob)
        elif character == "gary" and bool(re.fullmatch(r"(\W*m+e+o+w+\W*)+", text, re.IGNORECASE)):
            seg = random.choice(voice_gary)
        else:
            fy_tts = await asyncio.wait_for(loop.run_in_executor(None, fakeyou.say, text, characters[character][0]), fakeyou_timeout)
            with BytesIO(fy_tts.content) as wav:
                seg = AudioSegment.from_wav(wav)
        seg = pydub.effects.strip_silence(seg, 1000, -80, 0)
        seg = seg.apply_gain(-15-seg.dBFS)
        with BytesIO() as output:
            seg.export(output, "ogg")
            await inter.edit_original_response(embed=discord.Embed(description=f"- {characters[character][1]} {text}", color=embed_color_light), attachments=[discord.File(output, f"{character.title().replace('bob', 'Bob')} — {text}.ogg")])
        with open("statistics.txt", "a") as file:
            file.write(f"T {int(time.time())}\n")
    except:
        try:
            await inter.edit_original_response(embed=embed_error_failed)
        except:
            pass


@command_tree.command(name="stats", description="Show bot statistics.")
async def stats(inter: discord.Interaction):
    episodes_24h = 0
    episodes_all = 0
    chats_24h = 0
    chats_all = 0
    tts_24h = 0
    tts_all = 0
    current_time = int(time.time())
    if os.path.exists("statistics.txt"):
        with open("statistics.txt", "r") as file:
            lines = file.read().strip().split("\n")
        for line in lines:
            parts = line.split(" ")
            if parts[0] == "E":
                episodes_all += 1
                if current_time - int(parts[1]) < 86400:
                    episodes_24h += 1
            elif parts[0] == "C":
                chats_all += 1
                if current_time - int(parts[1]) < 86400:
                    chats_24h += 1
            elif parts[0] == "T":
                tts_all += 1
                if current_time - int(parts[1]) < 86400:
                    tts_24h += 1
    uptime = int(current_time - start_time)
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
    await inter.response.send_message(embed=discord.Embed(color=embed_color_light)
                                      .add_field(name="📺 Episodes", value=f"- 24h: `{episodes_24h}`\n- All: `{episodes_all}`", inline=False)
                                      .add_field(name="💬 Chats", value=f"- 24h: `{chats_24h}`\n- All: `{chats_all}`", inline=False)
                                      .add_field(name="🔊 TTS", value=f"- 24h: `{tts_24h}`\n- All: `{tts_all}`", inline=False)
                                      .add_field(name="🤖 Bot", value=f"- Latency: `{int(1000 * client.latency)}ms`\n- Uptime: `{uptime_formatted}`\n- Guilds: `{len(client.guilds)}`", inline=False),
                                      ephemeral=True, delete_after=embed_delete_after)


@command_tree.command(name="help", description="Show bot help.")
async def help(inter: discord.Interaction):
    await inter.response.send_message(embed=embed_help, ephemeral=True, delete_after=embed_delete_after, view=discord.ui.View().add_item(help_button))


@client.event
async def on_ready():
    await command_tree.sync()


client.run(os.getenv("DISCORD_BOT_TOKEN"))
