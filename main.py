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


def load_wav(path, end, gain, repeat, fade, delay):
    if end is None:
        seg = AudioSegment.from_wav(path)
    else:
        seg = AudioSegment.from_wav(path)[:end]
    seg = seg.apply_gain(gain-seg.dBFS)
    if repeat:
        seg = seg.append(seg, 0)
    if fade:
        seg = seg.fade_in(fade)
    if delay:
        seg = AudioSegment.silent(delay).append(seg, 0)
    return seg


load_dotenv()
gpt = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
fy = FakeYou()
fy.login(os.getenv("FAKEYOU_USERNAME"), os.getenv("FAKEYOU_PASSWORD"))
client = discord.Client(intents=discord.Intents.default(), activity=discord.Game("/generate /status"))
tree = app_commands.CommandTree(client)
music_closing_theme = load_wav("music/closing_theme.wav", -2000, -40, True, 10000, 2000)
music_tip_top_polka = load_wav("music/tip_top_polka.wav", -2000, -40, True, 10000, 2000)
music_rake_hornpipe = load_wav("music/rake_hornpipe.wav", None, -40, True, 10000, 2000)
music_seaweed = load_wav("music/seaweed.wav", None, -40, False, 10000, 2000)
sfx_steel_sting = load_wav("sfx/steel_sting.wav", None, -25, False, 0, 0)
sfx_boowomp = load_wav("sfx/boowomp.wav", None, -25, False, 0, 0)
sfx_disgusting = load_wav("sfx/disgusting.wav", None, -25, False, 0, 0)
sfx_vibe_link_b = load_wav("sfx/vibe_link_b.wav", None, -25, False, 0, 0)
sfx_this_guy_stinks = load_wav("sfx/this_guy_stinks.wav", -100, -25, False, 0, 0)
sfx_my_leg = load_wav("sfx/my_leg.wav", -2000, -25, False, 0, 0)
sfx_you_what = load_wav("sfx/you_what.wav", None, -25, False, 0, 0)
sfx_transition = load_wav("sfx/transition.wav", None, -25, False, 0, 0)
sfx_gary = AudioSegment.from_wav("sfx/gary.wav")[:6000]
silence_line = AudioSegment.silent(500)
silence_transition = AudioSegment.silent(1500)
embed_busy = discord.Embed(title="Busy", color=0xf5f306).set_footer(text="An episode is generating.")
embed_idle = discord.Embed(title="Idle", color=0xf5f306).set_footer(text="An episode can be generated.")
embed_generating = discord.Embed(title="0%", color=0xf5f306).set_footer(text="This may take a while.")
embed_error_permissions = discord.Embed(title="Error", color=0xf5f306).set_footer(text="Missing required permissions.")
embed_error_failed = discord.Embed(title="Error", color=0xf5f306).set_footer(text="Failed to generate episode.")
busy = False
cooldown = {}


@tree.command(name="generate", description="Generate an episode.")
@app_commands.describe(topic="Topic of episode.")
async def generate(inter: discord.Interaction, topic: str) -> None:
    if not (inter.app_permissions.view_channel and inter.app_permissions.embed_links and inter.app_permissions.attach_files and inter.app_permissions.read_message_history):
        try:
            await inter.response.send_message(embed=embed_error_permissions)
        except:
            pass
    elif inter.user.id not in cooldown.keys() or time.time() - cooldown[inter.user.id] > 300:
        global busy
        if not busy:
            busy = True
            try:
                await inter.response.send_message(embed=embed_generating)
                response = await inter.original_response()
                message = await response.channel.fetch_message(response.id)
                completion = await gpt.completions.create(
                    model="gpt-3.5-turbo-instruct",
                    max_tokens=700,
                    prompt=f"Create a vulgar, nsfw, politically incorrect script for a scene from Spongebob where characters discuss a topic. Possible characters include SpongeBob, Patrick, Squidward, Mr. Krabs, Plankton, Karen, Sandy. Very rarely include Gary, Larry, Mrs. Puff, Squilliam, Bubble Bass, Bubble Buddy, and French Narrator. Use the format: Character: <dialogue>. Only reply with coherent character dialogue. No more than ten lines of dialogue with talking only. Create a two word title with format: Title: <title>. The topic is: {topic}"
                )
                lines = re.sub(r"\(.*?\)|\[.*?]|\*.*?\*", "", completion.choices[0].text).replace("\n\n", "\n").replace(":\n", ": ").replace("  ", " ").strip().split("\n")
                remaining = len(lines)
                title = re.sub(r"[^A-Za-z0-9 ]+", "", lines.pop(0)[7:]).strip().replace(" ", "_").upper().replace("I", "i")
                progress = 1
                await message.edit(embed=discord.Embed(title=f"{int(100 * (progress / remaining))}%", color=0xf5f306).set_footer(text="This may take a while."))
                transcript = []
                combined = AudioSegment.empty()
                loop = asyncio.get_running_loop()
                for line in lines:
                    loud = False
                    line = line.strip()
                    lower = line.lower()
                    if lower.startswith("spongebob: "):
                        tts = await asyncio.wait_for(loop.run_in_executor(None, fy.say, line[11:], "weight_5by9kjm8vr8xsp7abe8zvaxc8"), 180)
                    elif lower.startswith("patrick: "):
                        tts = await asyncio.wait_for(loop.run_in_executor(None, fy.say, line[9:], "weight_154man2fzg19nrtc15drner7t"), 180)
                    elif lower.startswith("squidward: "):
                        tts = await asyncio.wait_for(loop.run_in_executor(None, fy.say, line[11:], "weight_y9arhnd7wjamezhqd27ksvmaz"), 180)
                    elif lower.startswith("loudward: "):
                        tts = await asyncio.wait_for(loop.run_in_executor(None, fy.say, line[10:], "weight_y9arhnd7wjamezhqd27ksvmaz"), 180)
                        loud = True
                    elif lower.startswith("gary: "):
                        tts = None
                        seg = sfx_gary
                    elif lower.startswith("plankton: "):
                        tts = await asyncio.wait_for(loop.run_in_executor(None, fy.say, line[10:], "weight_ahxbf2104ngsgyegncaefyy6j"), 180)
                    elif lower.startswith("mr. krabs: "):
                        tts = await asyncio.wait_for(loop.run_in_executor(None, fy.say, line[11:], "weight_5bxbp9xqy61svfx03b25ezmwx"), 180)
                    elif lower.startswith("karen: "):
                        tts = await asyncio.wait_for(loop.run_in_executor(None, fy.say, line[7:], "weight_eckp92cd68r4yk68n6re3fwcb"), 180)
                    elif lower.startswith("sandy: "):
                        tts = await asyncio.wait_for(loop.run_in_executor(None, fy.say, line[7:], "weight_tzgp5df2xzwz7y7jzz7at96jf"), 180)
                    elif lower.startswith("mrs. puff: "):
                        tts = await asyncio.wait_for(loop.run_in_executor(None, fy.say, line[11:], "weight_129qhgze57zhndkkcq83e6b2a"), 180)
                    elif lower.startswith("squilliam: "):
                        tts = await asyncio.wait_for(loop.run_in_executor(None, fy.say, line[11:], "weight_zmjv8223ed6wx1fp234c79v9s"), 180)
                    elif lower.startswith("larry: "):
                        tts = await asyncio.wait_for(loop.run_in_executor(None, fy.say, line[7:], "weight_k7qvaffwsft6vxbcps4wbyj58"), 180)
                    elif lower.startswith("bubble bass: "):
                        tts = await asyncio.wait_for(loop.run_in_executor(None, fy.say, line[13:], "weight_h9g7rh6tj2hvfezrz8gjs4gwa"), 180)
                    elif lower.startswith("bubble buddy: "):
                        tts = await asyncio.wait_for(loop.run_in_executor(None, fy.say, line[14:], "weight_sbr0372ysxbdahcvej96axy1t"), 180)
                    elif lower.startswith("french narrator: "):
                        tts = await asyncio.wait_for(loop.run_in_executor(None, fy.say, line[17:], "weight_edzcfmq6y0vj7pte9pzhq5b6j"), 180)
                    else:
                        remaining -= 1
                        await message.edit(embed=discord.Embed(title=f"{int(100 * (progress / remaining))}%", color=0xf5f306).set_footer(text="This may take a while."))
                        continue
                    transcript.append(line)
                    if tts is None:
                        remaining -= 1
                    else:
                        with BytesIO(tts.content) as wav:
                            seg = AudioSegment.from_wav(wav)
                        await asyncio.sleep(10)
                        progress += 1
                    if random.randrange(100) > 0 and not loud:
                        seg = seg.apply_gain(-20-seg.dBFS)
                    else:
                        seg = seg.apply_gain(-seg.dBFS)
                    combined = combined.append(seg, 0)
                    if random.randrange(20) > 0:
                        combined = combined.append(silence_line, 0)
                    await message.edit(embed=discord.Embed(title=f"{int(100 * (progress / remaining))}%", color=0xf5f306).set_footer(text="This may take a while."))
                sfx = random.choice([sfx_steel_sting, sfx_boowomp, sfx_disgusting, sfx_vibe_link_b, sfx_this_guy_stinks, sfx_my_leg, sfx_you_what])
                final = silence_transition.append(combined.overlay(random.choice([music_closing_theme, music_tip_top_polka, music_rake_hornpipe, music_seaweed])).overlay(sfx, random.randrange(len(combined) - len(sfx)))).overlay(sfx_transition)
                with BytesIO() as episode:
                    final.export(episode, "wav")
                    await message.edit(embed=discord.Embed(color=0xf5f306).set_footer(text="\n".join(transcript)), attachments=[discord.File(episode, f"{title}.wav")])
                cooldown[inter.user.id] = time.time()
            except:
                try:
                    await message.edit(embed=embed_error_failed)
                except:
                    try:
                        await inter.edit_original_response(embed=embed_error_failed)
                    except:
                        pass
            busy = False
        else:
            await inter.response.send_message(ephemeral=True, embed=embed_busy)
    else:
        await inter.response.send_message(ephemeral=True, embed=discord.Embed(title="Cooldown", color=0xf5f306).set_footer(text=f"You can generate in {int((300 - (time.time() - cooldown[inter.user.id])) / 60)}m {int((300 - (time.time() - cooldown[inter.user.id])) % 60)}s."))


@tree.command(name="status", description="Check if an episode can be generated.")
async def status(inter: discord.Interaction) -> None:
    if inter.user.id not in cooldown.keys() or time.time() - cooldown[inter.user.id] > 300:
        if busy:
            await inter.response.send_message(ephemeral=True, embed=embed_busy)
        else:
            await inter.response.send_message(ephemeral=True, embed=embed_idle)
    else:
        await inter.response.send_message(ephemeral=True, embed=discord.Embed(title="Cooldown", color=0xf5f306).set_footer(text=f"You can generate in {int((300 - (time.time() - cooldown[inter.user.id])) / 60)}m {int((300 - (time.time() - cooldown[inter.user.id])) % 60)}s."))


@client.event
async def on_ready():
    await tree.sync()


client.run(os.getenv("DISCORD_BOT_TOKEN"))

