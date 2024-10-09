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
music_closing_theme = load_wav("music/closing_theme.wav", gain=-35)
music_tip_top_polka = load_wav("music/tip_top_polka.wav", gain=-35)
music_rake_hornpipe = load_wav("music/rake_hornpipe.wav", gain=-35)
music_seaweed = load_wav("music/seaweed.wav", gain=-35)
music_sneaky_snitch = load_wav("music/sneaky_snitch.wav", gain=-35)
music_better_call_saul = load_wav("music/better_call_saul.wav", start=50, end=18250, gain=-35)
sfx_steel_sting = load_wav("sfx/steel_sting.wav", start=100, end=-450, gain=-20)
sfx_boowomp = load_wav("sfx/boowomp.wav", start=750, end=1200, gain=-20)
sfx_disgusting = load_wav("sfx/disgusting.wav", start=100, end=-250, gain=-20)
sfx_vibe_link_b = load_wav("sfx/vibe_link_b.wav", start=50, gain=-20)
sfx_this_guy_stinks = load_wav("sfx/this_guy_stinks.wav", start=550, end=-100, gain=-20)
sfx_my_leg = load_wav("sfx/my_leg.wav", start=150, end=-2700, gain=-20)
sfx_you_what = load_wav("sfx/you_what.wav", start=150, gain=-20)
sfx_dolphin = load_wav("sfx/dolphin.wav", start=1050, end=-950, gain=-20)
sfx_transition = load_wav("sfx/transition.wav", start=200, gain=-20)
sfx_day = load_wav("sfx/day.wav", start=2000, end=-1000, gain=-50)
sfx_night = load_wav("sfx/night.wav", start=100, end=-4000, gain=-50)
sfx_rain = load_wav("sfx/rain.wav", start=1000, end=-1000, gain=-50)
sfx_gary = load_wav("sfx/gary.wav", end=6000)
silence_line = AudioSegment.silent(500)
silence_transition = AudioSegment.silent(1100)
silence_music = AudioSegment.silent(2000)
embed_ready = discord.Embed(title="Ready", color=0xf5f306).set_footer(text="Ready to generate.")
embed_error_permissions = discord.Embed(title="Generating...", description="# > Failed", color=0xf5f306).set_footer(text="Missing permissions.")
embed_error_failed = discord.Embed(title="Generating...", description="# > Failed", color=0xf5f306).set_footer(text="An error occurred.")
generating = False
progress = 0
cooldown = {}


@tree.command(name="generate", description="Generate an episode.")
@app_commands.describe(topic="Topic of episode.")
async def generate(inter: discord.Interaction, topic: str) -> None:
    if not (inter.app_permissions.view_channel and inter.app_permissions.embed_links and inter.app_permissions.attach_files and inter.app_permissions.read_message_history and inter.app_permissions.use_external_emojis):
        try:
            await inter.response.send_message(embed=embed_error_permissions)
        except:
            pass
    elif inter.user.id not in cooldown.keys() or time.time() - cooldown[inter.user.id] > 300:
        global generating
        if not generating:
            generating = True
            try:
                global progress
                progress = 0
                await inter.response.send_message(embed=discord.Embed(title="Generating...", description=f"# > {progress}%", color=0xf5f306).set_footer(text=f"Please wait..."))
                await client.change_presence(activity=discord.Game(f"Generating... {progress}%"), status=discord.Status.dnd)
                response = await inter.original_response()
                message = await response.channel.fetch_message(response.id)
                completion = await gpt.completions.create(
                    model="gpt-3.5-turbo-instruct",
                    max_tokens=700,
                    prompt=f"Create a vulgar, nsfw, politically incorrect script for a scene from Spongebob where characters discuss a topic. Possible characters include SpongeBob, Patrick, Squidward, Mr. Krabs, Plankton, Karen, Sandy and very rarely Gary, Larry, Mrs. Puff, Squilliam, Bubble Bass, Bubble Buddy, and French Narrator. Use the format: Character: <dialogue>. Only reply with coherent character dialogue. Around 12 - 15 lines of dialogue with talking only. Create a two word title with format: Title: <title>. The topic is: {topic}"
                )
                lines = re.sub(r"(^|\s+)(\(+\S[^()]+\S\)+|\[+\S[^\[\]]+\S]+|\*+\S[^*]+\S\*+|<+\S[^<>]+\S>+|\{+\S[^{}]+\S}+|-+\S[^-]+\S-+|\|+\S[^|]+\S\|+|/+\S[^/]+\S/+|\\+\S[^\\]+\S\\+)(\s+|$)", " ", completion.choices[0].text).replace("\n\n", "\n").replace(":\n", ": ").replace("  ", " ").strip().split("\n")
                remaining = len(lines)
                title = re.sub(r"[^A-Za-z0-9 ]+", "", lines.pop(0)[6:]).strip().replace(" ", "_").upper().replace("I", "i")
                completed = 1
                progress = int(100 * (completed / remaining))
                await message.edit(embed=discord.Embed(title="Generating...", description=f"# > {progress}%", color=0xf5f306).set_footer(text=f"Generated script."))
                await client.change_presence(activity=discord.Game(f"Generating... {progress}%"), status=discord.Status.dnd)
                transcript = []
                combined = AudioSegment.empty()
                loop = asyncio.get_running_loop()
                for line in lines:
                    loud = False
                    line = discord.utils.escape_markdown(line).strip()
                    lower = line.lower()
                    if lower.startswith("spongebob:"):
                        tts = await asyncio.wait_for(loop.run_in_executor(None, fy.say, line[10:].strip(), "weight_5by9kjm8vr8xsp7abe8zvaxc8"), 180)
                        line = "- <:spongebob:1290871906886619147>" + line[10:]
                    elif lower.startswith("patrick:"):
                        tts = await asyncio.wait_for(loop.run_in_executor(None, fy.say, line[8:].strip(), "weight_154man2fzg19nrtc15drner7t"), 180)
                        line = "- <:patrick:1290871963773960275>" + line[8:]
                    elif lower.startswith("squidward:"):
                        tts = await asyncio.wait_for(loop.run_in_executor(None, fy.say, line[10:].strip(), "weight_y9arhnd7wjamezhqd27ksvmaz"), 180)
                        line = "- <:squidward:1290871965623648286>" + line[10:]
                    elif lower.startswith("loudward:"):
                        tts = await asyncio.wait_for(loop.run_in_executor(None, fy.say, line[9:].strip(), "weight_y9arhnd7wjamezhqd27ksvmaz"), 180)
                        line = "- <:squidward:1290871965623648286>" + line[9:]
                        loud = True
                    elif lower.startswith("gary:"):
                        line = "- <:gary:1290871895759126538>" + line[5:]
                        tts = None
                        seg = sfx_gary
                    elif lower.startswith("plankton:"):
                        tts = await asyncio.wait_for(loop.run_in_executor(None, fy.say, line[9:].strip(), "weight_ahxbf2104ngsgyegncaefyy6j"), 180)
                        line = "- <:plankton:1290871903661195294>" + line[9:]
                    elif lower.startswith("mr. krabs:"):
                        tts = await asyncio.wait_for(loop.run_in_executor(None, fy.say, line[10:].strip(), "weight_5bxbp9xqy61svfx03b25ezmwx"), 180)
                        line = "- <:mrkrabs:1290871899621949490>" + line[10:]
                    elif lower.startswith("karen:"):
                        tts = await asyncio.wait_for(loop.run_in_executor(None, fy.say, line[6:].strip(), "weight_eckp92cd68r4yk68n6re3fwcb"), 180)
                        line = "- <:karen:1290871897394909184>" + line[6:]
                    elif lower.startswith("sandy:"):
                        tts = await asyncio.wait_for(loop.run_in_executor(None, fy.say, line[6:].strip(), "weight_tzgp5df2xzwz7y7jzz7at96jf"), 180)
                        line = "- <:sandy:1290871964709425182>" + line[6:]
                    elif lower.startswith("mrs. puff:"):
                        tts = await asyncio.wait_for(loop.run_in_executor(None, fy.say, line[10:].strip(), "weight_129qhgze57zhndkkcq83e6b2a"), 180)
                        line = "- <:mrspuff:1290871900712603709>" + line[10:]
                    elif lower.startswith("squilliam:"):
                        tts = await asyncio.wait_for(loop.run_in_executor(None, fy.say, line[10:].strip(), "weight_zmjv8223ed6wx1fp234c79v9s"), 180)
                        line = "- <:squilliam:1290871910137200712>" + line[10:]
                    elif lower.startswith("larry:"):
                        tts = await asyncio.wait_for(loop.run_in_executor(None, fy.say, line[6:].strip(), "weight_k7qvaffwsft6vxbcps4wbyj58"), 180)
                        line = "- <:larry:1290871898728566917>" + line[6:]
                    elif lower.startswith("bubble bass:"):
                        tts = await asyncio.wait_for(loop.run_in_executor(None, fy.say, line[12:].strip(), "weight_h9g7rh6tj2hvfezrz8gjs4gwa"), 180)
                        line = "- <:bubblebass:1291495397382164574>" + line[12:]
                    elif lower.startswith("bubble buddy:"):
                        tts = await asyncio.wait_for(loop.run_in_executor(None, fy.say, line[13:].strip(), "weight_sbr0372ysxbdahcvej96axy1t"), 180)
                        line = "- <:bubblebuddy:1291489139442847774>" + line[13:]
                    elif lower.startswith("french narrator:"):
                        tts = await asyncio.wait_for(loop.run_in_executor(None, fy.say, line[16:].strip(), "weight_edzcfmq6y0vj7pte9pzhq5b6j"), 180)
                        line = "- <:frenchnarrator:1290871893951512621>" + line[16:]
                    else:
                        remaining -= 1
                        progress = int(100 * (completed / remaining))
                        await message.edit(embed=discord.Embed(title="Generating...", description=f"# > {progress}%", color=0xf5f306).set_footer(text=f"Skipped line."))
                        await client.change_presence(activity=discord.Game(f"Generating... {progress}%"), status=discord.Status.dnd)
                        continue
                    transcript.append(line)
                    if tts is None:
                        remaining -= 1
                    else:
                        with BytesIO(tts.content) as wav:
                            seg = AudioSegment.from_wav(wav)
                        await asyncio.sleep(10)
                        completed += 1
                    if random.randrange(100) > 0 and not loud:
                        seg = seg.apply_gain(-15-seg.dBFS)
                    else:
                        seg = seg.apply_gain(-seg.dBFS)
                    combined = combined.append(seg, 0)
                    if random.randrange(10) > 0 and not line.endswith("-"):
                        combined = combined.append(silence_line, 0)
                    progress = int(100 * (completed / remaining))
                    await message.edit(embed=discord.Embed(title="Generating...", description=f"# > {progress}%", color=0xf5f306).set_footer(text=f"Synthesized line {completed-1}/{remaining-1}."))
                    await client.change_presence(activity=discord.Game(f"Generating... {progress}%"), status=discord.Status.dnd)
                sfx = random.choice([sfx_steel_sting, sfx_boowomp, sfx_disgusting, sfx_vibe_link_b, sfx_this_guy_stinks, sfx_my_leg, sfx_you_what, sfx_dolphin])
                music = random.choices([music_closing_theme, music_tip_top_polka, music_rake_hornpipe, music_seaweed, music_sneaky_snitch, music_better_call_saul], [10, 10, 10, 10, 1, 1])[0]
                music_loop = silence_music.append(music.fade_in(10000), 0)
                while len(music_loop) < len(combined):
                    music_loop = music_loop.append(music, 0)
                ambiance = random.choice([sfx_day, sfx_night])
                ambiance_loop = ambiance
                while len(ambiance_loop) < len(combined):
                    ambiance_loop = ambiance_loop.append(ambiance, 0)
                if random.randrange(4) > 0:
                    rain_loop = AudioSegment.empty()
                else:
                    rain_loop = sfx_rain
                    while len(rain_loop) < len(combined):
                        rain_loop = rain_loop.append(sfx_rain, 0)
                final = silence_transition.append(combined.overlay(music_loop).overlay(sfx, random.randrange(len(combined) - len(sfx))).overlay(ambiance_loop).overlay(rain_loop), 0).overlay(sfx_transition)
                with BytesIO() as episode:
                    final.export(episode, "mp3")
                    await message.edit(content="***[Donate to support AI Sponge Lite!](https://github.com/sponsors/jeremynoesen)***", embed=discord.Embed(description="\n".join(transcript), color=0xf5f306), attachments=[discord.File(episode, f"{title}.mp3")])
                    await client.change_presence(activity=discord.Game("Ready"), status=discord.Status.online)
                cooldown[inter.user.id] = time.time()
            except:
                try:
                    await message.edit(content=None, embed=embed_error_failed)
                except:
                    try:
                        await inter.edit_original_response(content=None, embed=embed_error_failed)
                    except:
                        pass
                await client.change_presence(activity=discord.Game("Ready"), status=discord.Status.online)
            generating = False
        else:
            await inter.response.send_message(ephemeral=True, delete_after=10, embed=discord.Embed(title="Generating", description=f"# > {progress}%", color=0xf5f306).set_footer(text="Generating an episode."))
    else:
        await inter.response.send_message(ephemeral=True, delete_after=10, embed=discord.Embed(title=f"Cooldown", description=f"# > {int((300 - (time.time() - cooldown[inter.user.id])) / 60)}m {int((300 - (time.time() - cooldown[inter.user.id])) % 60)}s", color=0xf5f306).set_footer(text="You're on cooldown."))


@tree.command(name="status", description="Check if an episode can be generated.")
async def status(inter: discord.Interaction) -> None:
    if inter.user.id not in cooldown.keys() or time.time() - cooldown[inter.user.id] > 300:
        if generating:
            await inter.response.send_message(ephemeral=True, delete_after=10, embed=discord.Embed(title="Generating", description=f"# > {progress}%", color=0xf5f306).set_footer(text="Generating an episode."))
        else:
            await inter.response.send_message(ephemeral=True, delete_after=10, embed=embed_ready)
    else:
        await inter.response.send_message(ephemeral=True, delete_after=10, embed=discord.Embed(title=f"Cooldown", description=f"# > {int((300 - (time.time() - cooldown[inter.user.id])) / 60)}m {int((300 - (time.time() - cooldown[inter.user.id])) % 60)}s", color=0xf5f306).set_footer(text="You're on cooldown."))


@client.event
async def on_ready():
    await tree.sync()


client.run(os.getenv("DISCORD_BOT_TOKEN"))

