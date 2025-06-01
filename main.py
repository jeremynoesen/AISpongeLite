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


load_dotenv()
openai = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
fakeyou = FakeYou()
fakeyou.login(os.getenv("FAKEYOU_USERNAME"), os.getenv("FAKEYOU_PASSWORD"))
fakeyou_timeout = 180
activity_ready = discord.Game(os.getenv("MOTD", "Ready to generate."))
activity_generating = discord.Game("Generating episode...")
client = discord.Client(intents=discord.Intents.default(), activity=discord.Game("Starting bot..."), status=discord.Status.idle)
command_tree = app_commands.CommandTree(client)
moderation_guild = discord.Object(id=os.getenv("MODERATION_GUILD_ID"))
moderation_channel = None
embed_color_command_unsuccessful = 0x04a3e7
embed_color_command_successful = 0x57f3ff
embed_color_logging = 0x1848ae
embed_delete_after = 10
embed_help = discord.Embed(title="See App Directory for bot help.", description="Support server and source code links are there as well.", color=embed_color_command_successful)
help_button = discord.ui.Button(style=discord.ButtonStyle.link, label="App Directory", url="https://discord.com/application-directory/1254296070599610469")
embed_in_use_episode = discord.Embed(title="Currently in use.", description="Another user is generating an episode.", color=embed_color_command_unsuccessful)
embed_in_use_tts = discord.Embed(title="Currently in use.", description="TTS unavailable while another user is generating an episode.", color=embed_color_command_unsuccessful)
embed_generating_episode_start = discord.Embed(title="Generating episode...", description="Generating script...", color=embed_color_command_unsuccessful)
embed_generating_episode_end = discord.Embed(title="Generating episode...", description="Adding music, ambiance, and SFX...", color=embed_color_command_unsuccessful)
embed_generating_chat = discord.Embed(title="Generating chat...", description="Generating response...", color=embed_color_command_unsuccessful)
embed_generating_tts = discord.Embed(title="Generating TTS...", description="Synthesizing line...", color=embed_color_command_unsuccessful)
embed_generation_failed = discord.Embed(title="Generation failed.", description="An error occurred.", color=embed_color_command_unsuccessful)
embed_unknown_character = discord.Embed(title="Unknown character.", description="Select a character from autocomplete list.", color=embed_color_command_unsuccessful)
embed_banned = discord.Embed(title="You are banned from using AI Sponge Lite.", color=embed_color_command_unsuccessful).set_image(url="attachment://explodeward.gif")
embed_no_file = discord.Embed(title="No episode or TTS found.", description="This can only be used on OGG files sent by this bot.", color=embed_color_command_unsuccessful)
embed_converting_file = discord.Embed(title="Converting file...", description="Converting from OGG to MP3...", color=embed_color_command_unsuccessful)
remove_cooldown_sku = int(os.getenv("REMOVE_COOLDOWN_SKU"))
remove_cooldown_button = discord.ui.Button(style=discord.ButtonStyle.premium, sku_id=remove_cooldown_sku)
emojis = {}
characters = {
    "spongebob": ("weight_5by9kjm8vr8xsp7abe8zvaxc8", ["loudbob", "freakbob", "sadbob", "nerdbob", "susbob", "gigglebob"]),
    "patrick": ("weight_154man2fzg19nrtc15drner7t", ["loudrick", "shortrick", "widerick", "pinhead", "patback"]),
    "squidward": ("TM:3psksme51515", ["loudward", "schizoward", "shadeward", "spinward", "gyattward", "skodwarde"]),
    "mr. krabs": ("weight_5bxbp9xqy61svfx03b25ezmwx", ["shadow krabs", "sus krabs", "spin krabs", "mr. crack"]),
    "plankton": ("weight_ahxbf2104ngsgyegncaefyy6j", ["loudton", "dickton", "servedton", "suston", "dr. jr."]),
    "karen": ("weight_eckp92cd68r4yk68n6re3fwcb", ["evil karen", "snarky karen", "smart karen", "hydra karen"]),
    "gary": ("weight_ak3kb7kvye39r6c63tydsveyy", []),
    "sandy": ("weight_tzgp5df2xzwz7y7jzz7at96jf", []),
    "mrs. puff": ("weight_129qhgze57zhndkkcq83e6b2a", []),
    "larry": ("weight_k7qvaffwsft6vxbcps4wbyj58", []),
    "squilliam": ("weight_zmjv8223ed6wx1fp234c79v9s", []),
    "bubble bass": ("weight_h9g7rh6tj2hvfezrz8gjs4gwa", []),
    "bubble buddy": ("weight_sbr0372ysxbdahcvej96axy1t", []),
    "doodlebob": ("", []),
    "french narrator": ("weight_edzcfmq6y0vj7pte9pzhq5b6j", []),
    "all": ("", ["every", "unison", "together", "both"])
}
ambiance_gain = -45
ambiance_time = [
    AudioSegment.from_wav("ambiance/day.wav"),
    AudioSegment.from_wav("ambiance/night.wav")
]
ambiance_rain = AudioSegment.from_wav("ambiance/rain.wav")
music_gain = -35
songs = {
    AudioSegment.from_wav("music/closing_theme.wav"): 10,
    AudioSegment.from_wav("music/tip_top_polka.wav"): 10,
    AudioSegment.from_wav("music/rake_hornpipe.wav"): 10,
    AudioSegment.from_wav("music/seaweed.wav"): 10,
    AudioSegment.from_wav("music/hello_sailor_b.wav"): 5,
    AudioSegment.from_wav("music/drunken_sailor.wav"): 5,
    AudioSegment.from_wav("music/stars_and_games.wav"): 5,
    AudioSegment.from_wav("music/comic_walk.wav"): 5,
    AudioSegment.from_wav("music/gator.wav"): 5,
    AudioSegment.from_wav("music/rock_bottom.wav"): 5,
    AudioSegment.from_wav("music/grass_skirt_chase.wav"): 1,
    AudioSegment.from_wav("music/sneaky_snitch.wav"): 1,
    AudioSegment.from_wav("music/better_call_saul.wav"): 1
}
sfx_gain = -20
sfx_random = {
    AudioSegment.from_mp3("sfx/car.mp3"): 10,
    AudioSegment.from_wav("sfx/steel_sting.wav"): 5,
    AudioSegment.from_wav("sfx/boowomp.wav"): 5,
    AudioSegment.from_wav("sfx/foghorn.wav"): 1,
    AudioSegment.from_wav("sfx/vibe_link_b.wav"): 1,
    AudioSegment.from_wav("sfx/this_guy_stinks.wav"): 1,
    AudioSegment.from_wav("sfx/my_leg_1.wav"): 1,
    AudioSegment.from_wav("sfx/my_leg_2.wav"): 1,
    AudioSegment.from_wav("sfx/you_what.wav"): 1,
    AudioSegment.from_wav("sfx/dolphin.wav"): 1,
    AudioSegment.from_wav("sfx/boo_you_stink.wav"): 1,
    AudioSegment.from_wav("sfx/bonk.wav"): 1,
    AudioSegment.from_wav("sfx/fling_1.wav"): 1,
    AudioSegment.from_wav("sfx/fling_2.wav"): 1,
    AudioSegment.from_wav("sfx/kick.wav"): 1,
    AudioSegment.from_wav("sfx/kiss.wav"): 1,
    AudioSegment.from_wav("sfx/squish_1.wav"): 1,
    AudioSegment.from_wav("sfx/squish_2.wav"): 1,
    AudioSegment.from_wav("sfx/dramatic_cue_a.wav"): 1,
    AudioSegment.from_wav("sfx/dramatic_cue_d.wav"): 1
}
sfx_triggered = {
    "burp": ([AudioSegment.from_wav("sfx/burp.wav")], ["krabby patt", "food", "burger", "hungry", "ice cream", "pizza", "pie", "fries", "fry", "consum", "cake", "shake", "fish", "sushi", "ketchup", "mustard", "mayo", "starv"]),
    "ball": ([AudioSegment.from_wav("sfx/ball.wav")], ["ball", "bounc", "foul", "soccer", "goal"]),
    "gun": ([AudioSegment.from_wav(f"sfx/gun_{i}.wav") for i in range(1, 3)], ["shoot", "shot", "kill", "murder", "gun"]),
    "molotov": ([AudioSegment.from_wav("sfx/molotov.wav")], ["fire", "molotov", "burn", "flame", "ignite", "arson", "light"]),
    "bomb": ([AudioSegment.from_wav("sfx/bomb_fuse.wav").apply_gain(-20) + AudioSegment.from_wav("sfx/bomb_explosion.wav")], ["boom", "bomb", "explosion", "explode", "fire in the hole", "blow up", "blew up"])
}
sfx_transition = AudioSegment.from_wav("sfx/transition.wav")
sfx_transition = sfx_transition.apply_gain(sfx_gain - sfx_transition.dBFS)
sfx_strike = AudioSegment.from_wav("sfx/lightning.wav")
voice_gary = [AudioSegment.from_wav(f"voice/gary_{i}.wav") for i in range(1, 7)]
voice_doodlebob = [AudioSegment.from_wav(f"voice/doodlebob_{i}.wav") for i in range(1, 9)]
silence_line = AudioSegment.silent(200)
silence_transition = AudioSegment.silent(600)
silence_music = AudioSegment.silent(3000)
episode_generating = False
episode_cooldown = 300
episode_cooldowns = {}
start_time = int(time.time())
bans = []
if os.path.exists("bans.txt"):
    with open("bans.txt", "r") as file:
        for line in file:
            bans.append(int(line))


@command_tree.command(description="Generate an episode.")
@app_commands.describe(topic="Topic of episode.")
@app_commands.allowed_installs(True, True)
@app_commands.allowed_contexts(True, True, True)
async def episode(inter: discord.Interaction, topic: str):
    global episode_generating
    if inter.user.id in episode_cooldowns.keys() and int(time.time()) - episode_cooldowns[inter.user.id] <= episode_cooldown:
        remaining = episode_cooldown - (int(time.time()) - episode_cooldowns[inter.user.id])
        remaining_formatted = ""
        minutes = remaining // 60
        if minutes > 0:
            remaining_formatted += f"{minutes}m "
        seconds = remaining % 60
        if seconds > 0:
            remaining_formatted += f"{seconds}s"
        await inter.response.send_message(ephemeral=True, delete_after=embed_delete_after, embed=discord.Embed(title=f"You are on cooldown.", description=f"`{remaining_formatted}` remaining.", color=embed_color_command_unsuccessful), view=discord.ui.View().add_item(remove_cooldown_button))
        return
    if episode_generating:
        await inter.response.send_message(ephemeral=True, delete_after=embed_delete_after, embed=embed_in_use_episode)
        return
    if inter.user.id in bans:
        await inter.response.send_message(embed=embed_banned, file=discord.File("img/explodeward.gif"), ephemeral=True, delete_after=embed_delete_after)
        return
    try:
        episode_generating = True
        await inter.response.send_message(embed=embed_generating_episode_start)
        await client.change_presence(activity=activity_generating, status=discord.Status.dnd)
        await moderation_channel.send(embed=discord.Embed(title=inter.user.id, description=f"/episode `topic:`{discord.utils.escape_markdown(topic)}", color=embed_color_logging))
        completion = await openai.completions.create(
            model="gpt-3.5-turbo-instruct",
            max_tokens=700,
            prompt=f"Create a profanity-filled, morally incorrect script for a scene from SpongeBob SquarePants where characters discuss a topic. Common characters include SpongeBob, Patrick, Squidward, Mr. Krabs, Plankton, Karen, and Gary. Rare characters include Sandy, Mrs. Puff, Larry, Squilliam, Bubble Bass, Bubble Buddy, DoodleBob, and French Narrator. Include 3 - 5 characters max. Use the format: Character: <dialogue>. Only reply with uncensored, coherent character dialogue. Around 12 - 15 lines of dialogue with talking only. The first line is a relevant 1 - 2 word title with format: Title: <title>. The topic is: {topic}."
        )
        lines = re.sub(r"(^|\s+)(\(+\S[^()]+\S\)+|\[+\S[^\[\]]+\S]+|\*+\S[^*]+\S\*+|<+\S[^<>]+\S>+|\{+\S[^{}]+\S}+|-+\S[^-]+\S-+|\|+\S[^|]+\S\|+|/+\S[^/]+\S/+|\\+\S[^\\]+\S\\+)(\s+|$)", r"\3", completion.choices[0].text.replace("\n\n", "\n").replace(":\n", ": ")).strip().split("\n")
        line_parts = lines.pop(0).split(":", 1)
        file_title = "UNTiTLED EPiSODE"
        embed_title = "**U**NTiTLED **E**PiSODE"
        if len(line_parts) == 2 and "title" in line_parts[0].lower():
            title = line_parts[1].strip(" \'\"")
            if title:
                file_title = title.upper().replace("I", "i")
                embed_title = "".join(f"**{char}**​" if char.isupper() or char.isnumeric() or char in ".,!?" else char for char in discord.utils.escape_markdown(title)).upper().replace("I", "i")
        completed = 1
        remaining = len(lines)
        transcript = []
        sfx_positions = {key: [] for key in sfx_triggered.keys()}
        used_model_tokens = set()
        combined = AudioSegment.empty()
        loop = asyncio.get_running_loop()
        for line in lines:
            await inter.edit_original_response(embed=discord.Embed(title="Generating episode...", description=f"Synthesizing line `{completed}/{remaining}`...", color=embed_color_command_unsuccessful))
            line_parts = line.split(":", 1)
            character = ""
            model_token = ""
            for key in characters.keys():
                model_token = characters[key][0]
                line_parts[0] = line_parts[0].lower()
                for alt in characters[key][1]:
                    if alt in line_parts[0]:
                        character = alt
                        break
                if character:
                    break
                if key in line_parts[0]:
                    character = key
                    break
            if len(line_parts) != 2 or not character or len(line_parts[1].strip()) < 3:
                remaining -= 1
                continue
            spoken_line = line_parts[1].strip()
            output_line = f"{emojis[character.replace(' ', '').replace('.', '')]} {spoken_line}"
            if character == "all" or character in characters["all"][1]:
                segs = []
                for used_model_token in used_model_tokens:
                    fy_tts = await asyncio.wait_for(loop.run_in_executor(None, fakeyou.say, spoken_line, used_model_token), fakeyou_timeout)
                    with BytesIO(fy_tts.content) as wav:
                        segs.append(AudioSegment.from_wav(wav))
                    await asyncio.sleep(10)
                segs.sort(key=lambda x: -len(x))
                seg = segs[0]
                for i in range(1, len(segs)):
                    seg = seg.overlay(segs[i], 0)
            elif character == "doodlebob" or character in characters["doodlebob"][1]:
                seg = random.choice(voice_doodlebob)
            elif (character == "gary" or character in characters["gary"][1]) and re.fullmatch(r"(\W*m+e+o+w+\W*)+", spoken_line, re.IGNORECASE):
                used_model_tokens.add(model_token)
                seg = random.choice(voice_gary)
            else:
                used_model_tokens.add(model_token)
                fy_tts = await asyncio.wait_for(loop.run_in_executor(None, fakeyou.say, spoken_line, model_token), fakeyou_timeout)
                with BytesIO(fy_tts.content) as wav:
                    seg = AudioSegment.from_wav(wav)
                await asyncio.sleep(10)
            seg = pydub.effects.strip_silence(seg, 1000, -80, 0)
            if "loud" in character or spoken_line.isupper() or random.randrange(20) == 0:
                seg = seg.apply_gain(20)
                seg = seg.apply_gain(-10-seg.dBFS)
                output_line = output_line.replace(spoken_line, spoken_line.upper())
            else:
                seg = seg.apply_gain(-15-seg.dBFS)
            spoken_line = spoken_line.lower()
            for sfx in sfx_triggered.keys():
                keywords = sfx_triggered[sfx][1]
                collection = sfx_positions[sfx]
                if any(keyword in spoken_line for keyword in keywords) and not ("fire" in keywords and "fire in the hole" in spoken_line):
                    collection.append(len(combined) + random.randrange(len(seg)))
            combined = combined.append(seg, 0)
            if output_line[-1] in "-–—" or random.randrange(10) == 0:
                output_line = output_line[:-1] + "—"
            else:
                combined = combined.append(silence_line, 0)
            transcript.append(f"- {discord.utils.escape_markdown(output_line)}")
            completed += 1
        await inter.edit_original_response(embed=embed_generating_episode_end)
        combined = combined.append(silence_line, 0)
        if random.randrange(20) > 0:
            music = random.choices(list(songs.keys()), list(songs.values()))[0]
            music = music.apply_gain((music_gain + random.randint(-5, 5)) - music.dBFS)
            music_loop = silence_music.append(music.fade_in(10000), 0)
            while len(music_loop) < len(combined):
                music_loop = music_loop.append(music, 0)
            combined = combined.overlay(music_loop)
        if random.randrange(10) > 0:
            ambiance = random.choice(ambiance_time)
            ambiance = ambiance.apply_gain((ambiance_gain + random.randint(-5, 5)) - ambiance.dBFS)
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
        for sfx in sfx_triggered.keys():
            for position in sfx_positions[sfx]:
                if random.randrange(5) > 0:
                    choice = random.choice(sfx_triggered[sfx][0])
                    combined = combined.overlay(choice.apply_gain((sfx_gain + random.randint(-10, 0)) - choice.dBFS), position)
        combined = silence_transition.append(combined, 0).overlay(sfx_transition)
        for i in range(random.randint(1, math.ceil(len(transcript) / 5))):
            choice = random.choices(list(sfx_random.keys()), list(sfx_random.values()))[0]
            combined = combined.overlay(choice.apply_gain((sfx_gain + random.randint(-5, 5)) - choice.dBFS), random.randrange(len(combined)))
        combined = combined.fade_out(200)
        with BytesIO() as output:
            combined.export(output, "ogg")
            await inter.edit_original_response(embed=discord.Embed(title=embed_title, description="\n".join(transcript) + f"\n\n-# > *{discord.utils.escape_markdown(topic)}*", color=embed_color_command_successful), attachments=[discord.File(output, f"{file_title}.ogg")])
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
        await inter.edit_original_response(embed=embed_generation_failed)
    finally:
        await client.change_presence(activity=activity_ready, status=discord.Status.online)
        episode_generating = False


async def character_autocomplete(interaction: discord.Interaction, current: str,):
    return [app_commands.Choice(name=character.title().replace("bob", "Bob"), value=character) for character in characters.keys() if character != "all" and current.lower() in character]


@command_tree.command(description="Chat with a character.")
@app_commands.describe(character="Character to chat with.")
@app_commands.describe(message="Message to send.")
@app_commands.autocomplete(character=character_autocomplete)
@app_commands.allowed_installs(True, True)
@app_commands.allowed_contexts(True, True, True)
async def chat(inter: discord.Interaction, character: str, message: str):
    character_lower = character.lower()
    if character_lower not in characters.keys() or character_lower == "all":
        await inter.response.send_message(ephemeral=True, delete_after=embed_delete_after, embed=embed_unknown_character)
        return
    if inter.user.id in bans:
        await inter.response.send_message(embed=embed_banned, file=discord.File("img/explodeward.gif"), ephemeral=True, delete_after=embed_delete_after)
        return
    try:
        await inter.response.send_message(embed=embed_generating_chat)
        await moderation_channel.send(embed=discord.Embed(title=inter.user.id, description=f"/chat `character:`{character} `message:`{discord.utils.escape_markdown(message)}", color=embed_color_logging))
        character_title = character.title().replace("bob", "Bob")
        completion = await openai.completions.create(
            model="gpt-3.5-turbo-instruct",
            max_tokens=250,
            prompt=f"You are {character_title} from SpongeBob SquarePants chatting with {inter.user.display_name} on Discord. Use the format: {character_title}: <response>. Respond only with a brief, exaggerated response. {inter.user.display_name} says: {message}."
        )
        output = discord.utils.escape_markdown(completion.choices[0].text.split(":", 1)[1].strip(" \'\""))
        await inter.edit_original_response(embed=discord.Embed(description=f"{output}\n\n-# > *{discord.utils.escape_markdown(message)}*", color=embed_color_command_successful).set_author(name=character_title, icon_url=emojis[character_lower.replace(' ', '').replace('.', '')].url))
        with open("statistics.txt", "a") as file:
            file.write(f"C {int(time.time())}\n")
    except:
        await inter.edit_original_response(embed=embed_generation_failed)


@command_tree.command(description="Synthesize character speech.")
@app_commands.describe(character="Voice to use.")
@app_commands.describe(text="Text to speak.")
@app_commands.autocomplete(character=character_autocomplete)
@app_commands.allowed_installs(True, True)
@app_commands.allowed_contexts(True, True, True)
async def tts(inter: discord.Interaction, character: str, text: str):
    character_lower = character.lower()
    if character_lower not in characters.keys() or character_lower == "all":
        await inter.response.send_message(ephemeral=True, delete_after=embed_delete_after, embed=embed_unknown_character)
        return
    if episode_generating:
        await inter.response.send_message(ephemeral=True, delete_after=embed_delete_after, embed=embed_in_use_tts)
        return
    if inter.user.id in bans:
        await inter.response.send_message(embed=embed_banned, file=discord.File("img/explodeward.gif"), ephemeral=True, delete_after=embed_delete_after)
        return
    try:
        await inter.response.send_message(embed=embed_generating_tts)
        await moderation_channel.send(embed=discord.Embed(title=inter.user.id, description=f"/tts `character:`{character} `text:`{discord.utils.escape_markdown(text)}", color=embed_color_logging))
        loop = asyncio.get_running_loop()
        if character_lower == "doodlebob":
            seg = random.choice(voice_doodlebob)
        elif character_lower == "gary" and re.fullmatch(r"(\W*m+e+o+w+\W*)+", text, re.IGNORECASE):
            seg = random.choice(voice_gary)
        else:
            fy_tts = await asyncio.wait_for(loop.run_in_executor(None, fakeyou.say, text, characters[character_lower][0]), fakeyou_timeout)
            with BytesIO(fy_tts.content) as wav:
                seg = AudioSegment.from_wav(wav)
        seg = pydub.effects.strip_silence(seg, 1000, -80, 0)
        seg = seg.apply_gain(-15-seg.dBFS)
        with BytesIO() as output:
            seg.export(output, "ogg")
            await inter.edit_original_response(embed=discord.Embed(description=f"{emojis[character_lower.replace(' ', '').replace('.', '')]} {discord.utils.escape_markdown(text)}", color=embed_color_command_successful), attachments=[discord.File(output, f"{character.title().replace('bob', 'Bob')} — {text}.ogg")])
        with open("statistics.txt", "a") as file:
            file.write(f"T {int(time.time())}\n")
    except:
        await inter.edit_original_response(embed=embed_generation_failed)


@command_tree.command(description="Show bot statistics.")
@app_commands.allowed_installs(True, True)
@app_commands.allowed_contexts(True, True, True)
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
            for line in file:
                line_parts = line.strip().split(" ")
                if line_parts[0] == "E":
                    episodes_all += 1
                    if current_time - int(line_parts[1]) < 86400:
                        episodes_24h += 1
                elif line_parts[0] == "C":
                    chats_all += 1
                    if current_time - int(line_parts[1]) < 86400:
                        chats_24h += 1
                elif line_parts[0] == "T":
                    tts_all += 1
                    if current_time - int(line_parts[1]) < 86400:
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
    await inter.response.send_message(embed=discord.Embed(color=embed_color_command_successful)
                                      .add_field(name="Episodes", value=f"- 24h: `{episodes_24h}`\n- All: `{episodes_all}`", inline=False)
                                      .add_field(name="Chats", value=f"- 24h: `{chats_24h}`\n- All: `{chats_all}`", inline=False)
                                      .add_field(name="TTS", value=f"- 24h: `{tts_24h}`\n- All: `{tts_all}`", inline=False)
                                      .add_field(name="Bot", value=f"- Latency: `{int(1000 * client.latency)}ms`\n- Uptime: `{uptime_formatted}`\n- Guilds: `{len(client.guilds)}`", inline=False),
                                      ephemeral=True, delete_after=embed_delete_after)


@command_tree.command(description="Show bot help.")
@app_commands.allowed_installs(True, True)
@app_commands.allowed_contexts(True, True, True)
async def help(inter: discord.Interaction):
    await inter.response.send_message(embed=embed_help, ephemeral=True, delete_after=embed_delete_after, view=discord.ui.View().add_item(help_button))


@command_tree.command(description="Ban a user.", guild=moderation_guild)
@app_commands.describe(id="ID of user.")
@app_commands.allowed_installs(True, False)
@app_commands.allowed_contexts(True, False, True)
async def ban(inter: discord.Interaction, id: str):
    if inter.channel != moderation_channel:
        await inter.response.send_message(embed=discord.Embed(title="Incorrect channel.", description=f"This command can only be used in {moderation_channel.mention}.", color=embed_color_command_unsuccessful), ephemeral=True, delete_after=embed_delete_after)
        return
    try:
        id = int(id)
        await client.fetch_user(id)
    except:
        await inter.response.send_message(embed=discord.Embed(title="Unknown user.", description=f"No user exists with ID `{id}`.", color=embed_color_command_unsuccessful), ephemeral=True, delete_after=embed_delete_after)
        return
    if id in bans:
        await inter.response.send_message(embed=discord.Embed(title="User already banned.", description=f"User with ID `{id}` is already banned.", color=embed_color_command_unsuccessful), ephemeral=True, delete_after=embed_delete_after)
        return
    bans.append(id)
    with open("bans.txt", "a") as file:
        file.write(f"{id}\n")
    await inter.response.send_message(embed=discord.Embed(title="Banned user.", description=f"User with ID `{id}` has been banned.", color=embed_color_command_successful))


@command_tree.context_menu(name="Convert OGG to MP3")
@app_commands.allowed_installs(True, True)
@app_commands.allowed_contexts(True, True, True)
async def convert(inter: discord.Interaction, message: discord.Message):
    if message.author != client.user or not message.attachments or message.attachments[0].filename[-3:].lower() != "ogg":
        await inter.response.send_message(embed=embed_no_file, ephemeral=True, delete_after=embed_delete_after)
        return
    await inter.response.send_message(embed=embed_converting_file)
    with BytesIO() as input:
        await message.attachments[0].save(input)
        seg = AudioSegment.from_ogg(input)
    with BytesIO() as output:
        seg.export(output, "mp3")
        await inter.edit_original_response(embed=None, attachments=[discord.File(output, f"{message.attachments[0].filename[:-3]}mp3")])


@client.event
async def on_ready():
    await command_tree.sync()
    await command_tree.sync(guild=moderation_guild)
    global moderation_channel, emojis
    moderation_channel = await client.fetch_channel(int(os.getenv("MODERATION_CHANNEL_ID")))
    emojis = {e.name: e for e in await client.fetch_application_emojis()}
    for x in characters["all"][1]:
        emojis[x] = emojis["all"]
    await client.change_presence(activity=activity_ready, status=discord.Status.online)


client.run(os.getenv("DISCORD_BOT_TOKEN"))
