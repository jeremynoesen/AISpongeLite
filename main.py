import asyncio
import random
import re
import time
import discord
import os
from dotenv import load_dotenv
from discord import app_commands
from io import BytesIO
from fakeyou import FakeYou
from openai import AsyncOpenAI
from pydub import AudioSegment


def load_wav(path, start=None, end=None, gain=None):
    seg = AudioSegment.from_wav(path)[start:end]
    if gain is not None:
        seg = seg.apply_gain(gain-seg.dBFS)
    return seg


load_dotenv()
gpt = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
fy = FakeYou()
fy.login(os.getenv("FAKEYOU_USERNAME"), os.getenv("FAKEYOU_PASSWORD"))
client = discord.Client(intents=discord.Intents.default(), activity=discord.Game("Ready"), status=discord.Status.online)
tree = app_commands.CommandTree(client)
embed_ready = discord.Embed(title="Ready", color=0xf5f306).set_footer(text="Ready to generate.")
embed_generating_msg = discord.Embed(title="Generating...", description=f"# 💬", color=0xf5f306).set_footer(text=f"Sending message...")
embed_error_permissions = discord.Embed(title="Generating...", description="# Failed", color=0xf5f306).set_footer(text="Missing permissions.")
embed_error_failed = discord.Embed(title="Generating...", description="# Failed", color=0xf5f306).set_footer(text="An error occurred.")
embed_error_character = discord.Embed(title="Generating...", description="# Failed", color=0xf5f306).set_footer(text="Invalid character.")
remove_cooldown_sku = int(os.getenv("REMOVE_COOLDOWN_SKU"))
remove_cooldown_button = discord.ui.Button(style=discord.ButtonStyle.premium, sku_id=remove_cooldown_sku)
characters = {"spongebob": ("weight_5by9kjm8vr8xsp7abe8zvaxc8", os.getenv("EMOJI_SPONGEBOB")),
              "patrick": ("weight_154man2fzg19nrtc15drner7t", os.getenv("EMOJI_PATRICK")),
              "squidward": ("weight_y9arhnd7wjamezhqd27ksvmaz", os.getenv("EMOJI_SQUIDWARD")),
              "loudward": ("weight_y9arhnd7wjamezhqd27ksvmaz", os.getenv("EMOJI_SQUIDWARD")),
              "gary": (None, os.getenv("EMOJI_GARY")),
              "plankton": ("weight_ahxbf2104ngsgyegncaefyy6j", os.getenv("EMOJI_PLANKTON")),
              "loudton": ("weight_ahxbf2104ngsgyegncaefyy6j", os.getenv("EMOJI_PLANKTON")),
              "mr. krabs": ("weight_5bxbp9xqy61svfx03b25ezmwx", os.getenv("EMOJI_MRKRABS")),
              "karen": ("weight_eckp92cd68r4yk68n6re3fwcb", os.getenv("EMOJI_KAREN")),
              "sandy": ("weight_tzgp5df2xzwz7y7jzz7at96jf", os.getenv("EMOJI_SANDY")),
              "mrs. puff": ("weight_129qhgze57zhndkkcq83e6b2a", os.getenv("EMOJI_MRSPUFF")),
              "squilliam": ("weight_zmjv8223ed6wx1fp234c79v9s", os.getenv("EMOJI_SQUILLIAM")),
              "larry": ("weight_k7qvaffwsft6vxbcps4wbyj58", os.getenv("EMOJI_LARRY")),
              "bubble bass": ("weight_h9g7rh6tj2hvfezrz8gjs4gwa", os.getenv("EMOJI_BUBBLEBASS")),
              "bubble buddy": ("weight_sbr0372ysxbdahcvej96axy1t", os.getenv("EMOJI_BUBBLEBUDDY")),
              "french narrator": ("weight_edzcfmq6y0vj7pte9pzhq5b6j", os.getenv("EMOJI_FRENCHNARRATOR"))}
songs = {load_wav("music/closing_theme.wav", gain=-35): 10,
         load_wav("music/tip_top_polka.wav", gain=-35): 10,
         load_wav("music/rake_hornpipe.wav", gain=-35): 10,
         load_wav("music/seaweed.wav", gain=-35): 10,
         load_wav("music/hello_sailor_b.wav", gain=-35): 5,
         load_wav("music/stars_and_games.wav", gain=-35): 5,
         load_wav("music/rock_bottom.wav", gain=-35): 5,
         load_wav("music/sneaky_snitch.wav", gain=-35): 1,
         load_wav("music/better_call_saul.wav", start=50, end=18250, gain=-35): 1}
sfx = {load_wav("sfx/steel_sting.wav", start=100, end=-450, gain=-20): 5,
       load_wav("sfx/boowomp.wav", start=750, end=1200, gain=-20): 5,
       load_wav("sfx/disgusting.wav", start=100, end=-250, gain=-20): 1,
       load_wav("sfx/vibe_link_b.wav", start=50, gain=-20): 1,
       load_wav("sfx/this_guy_stinks.wav", start=550, end=-100, gain=-20): 1,
       load_wav("sfx/my_leg.wav", start=150, end=-2700, gain=-20): 1,
       load_wav("sfx/you_what.wav", start=150, gain=-20): 1,
       load_wav("sfx/dolphin.wav", start=1050, end=-950, gain=-20): 1}
sfx_transition = load_wav("sfx/transition.wav", start=200, gain=-20)
ambiance_time = [load_wav("ambiance/day.wav", start=2000, end=-1000, gain=-45),
                 load_wav("ambiance/night.wav", start=100, end=-4000, gain=-45)]
ambiance_rain = load_wav("ambiance/rain.wav", start=1000, end=-1000)
voice_gary = load_wav("voice/gary.wav", end=6000)
silence_line = AudioSegment.silent(500)
silence_transition = AudioSegment.silent(1100)
silence_music = AudioSegment.silent(2450)
generating = False
progress = 0
cooldown = {}


@tree.command(name="episode", description="Generate an episode.")
@app_commands.describe(topic="Topic of episode.")
async def episode(inter: discord.Interaction, topic: str = ""):
    if not (inter.app_permissions.view_channel and inter.app_permissions.embed_links and inter.app_permissions.attach_files and inter.app_permissions.read_message_history and inter.app_permissions.use_external_emojis):
        try:
            await inter.response.send_message(embed=embed_error_permissions)
        except:
            pass
    elif inter.user.id not in cooldown.keys() or time.time() - cooldown[inter.user.id] > 300:
        if inter.user.id in cooldown.keys():
            del cooldown[inter.user.id]
        global generating
        if not generating:
            if topic:
                try:
                    generating = True
                    global progress
                    progress = 0
                    await inter.response.send_message(embed=discord.Embed(title="Generating...", description=f"# {progress}%", color=0xf5f306).set_footer(text=f"Preparing episode..."))
                    await client.change_presence(activity=discord.Game(f"Generating... {progress}%"), status=discord.Status.dnd)
                    response = await inter.original_response()
                    message = await response.channel.fetch_message(response.id)
                    completion = await gpt.completions.create(
                        model="gpt-3.5-turbo-instruct",
                        max_tokens=700,
                        prompt=f"Create a vulgar, morally incorrect script for a scene from SpongeBob SquarePants where characters discuss a topic. Common characters include SpongeBob, Patrick, Squidward, Mr. Krabs, Plankton, Karen, and Sandy. Rare characters include Gary, Larry, Mrs. Puff, Squilliam, Bubble Bass, Bubble Buddy, and French Narrator. Include 3 - 5 characters max. Use the format: Character: <dialogue>. Only reply with coherent character dialogue. Around 12 - 15 lines of dialogue with talking only. Include a relevant 1 - 2 word title with format: Title: <title>. The topic is: {topic}"
                    )
                    lines = re.sub(r"(^|\s+)(\(+\S[^()]+\S\)+|\[+\S[^\[\]]+\S]+|\*+\S[^*]+\S\*+|<+\S[^<>]+\S>+|\{+\S[^{}]+\S}+|-+\S[^-]+\S-+|\|+\S[^|]+\S\|+|/+\S[^/]+\S/+|\\+\S[^\\]+\S\\+)(\s+|$)", " ", completion.choices[0].text).replace("\n\n", "\n").replace(":\n", ": ").replace("  ", " ").strip().split("\n")
                    remaining = len(lines)
                    title = lines.pop(0)[6:].strip().upper().replace("I", "i")
                    if not title:
                        title = "EPiSODE"
                    completed = 1
                    progress = int(100 * (completed / remaining))
                    await message.edit(embed=discord.Embed(title="Generating...", description=f"# {progress}%", color=0xf5f306).set_footer(text=f"Generated script."))
                    await client.change_presence(activity=discord.Game(f"Generating... {progress}%"), status=discord.Status.dnd)
                    transcript = []
                    combined = AudioSegment.empty()
                    loop = asyncio.get_running_loop()
                    for line in lines:
                        line = discord.utils.escape_markdown(line).strip()
                        character = line.split(":")[0].lower()
                        if character in characters.keys():
                            stripped = line[len(character)+1:].strip()
                            line = "- " + characters[character][1] + " " + stripped
                            if character == "gary":
                                seg = voice_gary
                                remaining -= 1
                            else:
                                tts = await asyncio.wait_for(loop.run_in_executor(None, fy.say, stripped, characters[character][0]), 180)
                                with BytesIO(tts.content) as wav:
                                    seg = AudioSegment.from_wav(wav)
                                completed += 1
                            if "loud" in character or stripped.isupper() or random.randrange(100) == 0:
                                seg = seg.apply_gain(-seg.dBFS)
                                line = line.replace(stripped, stripped.upper())
                            else:
                                seg = seg.apply_gain(-15-seg.dBFS)
                            combined = combined.append(seg, 0)
                            if line[-1] in "-–—":
                                pass
                            elif random.randrange(10) == 0:
                                while line[-1] in ".!?":
                                    line = line[:-1]
                                line += "—"
                            else:
                                combined = combined.append(silence_line, 0)
                            transcript.append(line)
                            progress = int(100 * (completed / remaining))
                            await message.edit(embed=discord.Embed(title="Generating...", description=f"# {progress}%", color=0xf5f306).set_footer(text=f"Synthesized line {completed-1}/{remaining-1}."))
                        else:
                            remaining -= 1
                            progress = int(100 * (completed / remaining))
                            await message.edit(embed=discord.Embed(title="Generating...", description=f"# {progress}%", color=0xf5f306).set_footer(text=f"Skipped line."))
                        await client.change_presence(activity=discord.Game(f"Generating... {progress}%"), status=discord.Status.dnd)
                    combined = combined.append(silence_line, 0)
                    music = random.choices(list(songs.keys()), list(songs.values()))[0]
                    music_loop = silence_music.append(music.fade_in(10000), 0)
                    while len(music_loop) < len(combined):
                        music_loop = music_loop.append(music, 0)
                    combined = combined.overlay(music_loop)
                    if random.randrange(5) > 0:
                        ambiance = random.choice(ambiance_time)
                        ambiance_loop = ambiance.fade_in(500)
                        while len(ambiance_loop) < len(combined):
                            ambiance_loop = ambiance_loop.append(ambiance, 0)
                        combined = combined.overlay(ambiance_loop)
                    if random.randrange(5) == 0:
                        rain_randomized = ambiance_rain.apply_gain(random.randint(-45, -40)-ambiance_rain.dBFS)
                        rain_loop = rain_randomized.fade_in(500)
                        while len(rain_loop) < len(combined):
                            rain_loop = rain_loop.append(rain_randomized, 0)
                        combined = combined.overlay(rain_loop)
                    combined = silence_transition.append(combined, 0).overlay(sfx_transition)
                    for i in range(random.randint(1, len(transcript) // 5)):
                        combined = combined.overlay(random.choices(list(sfx.keys()), list(sfx.values()))[0], random.randrange(len(combined)))
                    combined = combined.fade_out(500)
                    with BytesIO() as output:
                        combined.export(output, "ogg")
                        await message.edit(embed=discord.Embed(title=title, description="\n".join(transcript) + "\n\n-# > " + topic, color=0xf5f306), attachments=[discord.File(output, f"{title}.ogg")])
                    remove_cooldown = False
                    for entitlement in inter.entitlements:
                        if entitlement.sku_id == remove_cooldown_sku and not entitlement.is_expired():
                            remove_cooldown = True
                            break
                    if not remove_cooldown:
                        cooldown[inter.user.id] = time.time()
                except:
                    try:
                        await message.edit(embed=embed_error_failed)
                    except:
                        try:
                            await inter.edit_original_response(embed=embed_error_failed)
                        except:
                            pass
                await client.change_presence(activity=discord.Game("Ready"), status=discord.Status.online)
                generating = False
            else:
                await inter.response.send_message(ephemeral=True, delete_after=10, embed=embed_ready)
        else:
            await inter.response.send_message(ephemeral=True, delete_after=10, embed=discord.Embed(title="Generating", description=f"# {progress}%", color=0xf5f306).set_footer(text="Generating an episode."))
    else:
        view = discord.ui.View()
        view.add_item(remove_cooldown_button)
        await inter.response.send_message(ephemeral=True, delete_after=10, embed=discord.Embed(title=f"Cooldown", description=f"# {int((300 - (time.time() - cooldown[inter.user.id])) / 60)}m {int((300 - (time.time() - cooldown[inter.user.id])) % 60)}s", color=0xf5f306).set_footer(text="You're on cooldown."), view=view)


async def character_autocomplete(interaction: discord.Interaction, current: str,):
    return [app_commands.Choice(name=character, value=character) for character in [character.title().replace("bob", "Bob") for character in characters.keys()] if current.lower() in character.lower()]


@tree.command(name="msg", description="Message a character.")
@app_commands.describe(character="Character to message.")
@app_commands.describe(message="Message to send.")
@app_commands.autocomplete(character=character_autocomplete)
async def msg(inter: discord.Interaction, character: str, message: str):
    try:
        character = character.lower()
        if character in characters.keys():
            emoji = characters[character][1]
        else:
            await inter.response.send_message(ephemeral=True, delete_after=10, embed=embed_error_character)
            return
        character = character.title().replace("bob", "Bob")
        await inter.response.send_message(embed=embed_generating_msg)
        completion = await gpt.completions.create(
            model="gpt-3.5-turbo-instruct",
            max_tokens=250,
            prompt=f"You are {character} from SpongeBob SquarePants messaging with {inter.user.display_name} on Discord. Only respond with a brief, exaggerated response. {inter.user.display_name} says: {message}."
        )
        output = re.compile(re.escape(character + ": "), re.IGNORECASE).sub("", completion.choices[0].text.strip().strip("\""), 1)
        embed = discord.Embed(description=f"{output}\n\n-# > {message}", color=0xf5f306).set_author(name=character, icon_url=client.get_emoji(int(emoji.split(":")[-1][:-1])).url)
        await inter.edit_original_response(embed=embed)
    except:
        try:
            await inter.edit_original_response(embed=embed_error_failed)
        except:
            pass


@client.event
async def on_ready():
    await tree.sync()


client.run(os.getenv("DISCORD_BOT_TOKEN"))
