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
client = discord.Client(intents=discord.Intents.default(), activity=discord.Game("/generate /status"))
tree = app_commands.CommandTree(client)
music_closing_theme = load_wav("music/closing_theme.wav", gain=-40)
music_tip_top_polka = load_wav("music/tip_top_polka.wav", gain=-40)
music_rake_hornpipe = load_wav("music/rake_hornpipe.wav", gain=-40)
music_seaweed = load_wav("music/seaweed.wav", gain=-40)
music_sneaky_snitch = load_wav("music/sneaky_snitch.wav", gain=-40)
music_better_call_saul = load_wav("music/better_call_saul.wav", start=50, end=18250, gain=-40)
sfx_steel_sting = load_wav("sfx/steel_sting.wav", start=100, end=-450, gain=-25)
sfx_boowomp = load_wav("sfx/boowomp.wav", start=750, end=1200, gain=-25)
sfx_disgusting = load_wav("sfx/disgusting.wav", start=100, end=-250, gain=-25)
sfx_vibe_link_b = load_wav("sfx/vibe_link_b.wav", start=50, gain=-25)
sfx_this_guy_stinks = load_wav("sfx/this_guy_stinks.wav", start=550, end=-100, gain=-25)
sfx_my_leg = load_wav("sfx/my_leg.wav", start=150, end=-2700, gain=-25)
sfx_you_what = load_wav("sfx/you_what.wav", start=150, gain=-25)
sfx_dolphin = load_wav("sfx/dolphin.wav", start=1050, end=-950, gain=-25)
sfx_transition = load_wav("sfx/transition.wav", start=200, gain=-25)
sfx_gary = load_wav("sfx/gary.wav", end=6000)
silence_line = AudioSegment.silent(500)
silence_transition = AudioSegment.silent(1100)
silence_music = AudioSegment.silent(1900)
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
                    prompt=f"Create a vulgar, nsfw, politically incorrect script for a scene from Spongebob where characters discuss a topic. Possible characters include SpongeBob, Patrick, Squidward, Mr. Krabs, Plankton, Karen, Sandy and very rarely Gary, Larry, Mrs. Puff, Squilliam, Bubble Bass, Bubble Buddy, and French Narrator. Use the format: Character: <dialogue>. Only reply with coherent character dialogue. Around 12 - 15 lines of dialogue with talking only. Create a two word title with format: Title: <title>. The topic is: {topic}"
                )
                lines = re.sub(r"(^|\s+)(\(\S[^()]*?\S\)|\[\S[^\[\]]*?\S]|\*\S[^*]*?\S\*|<\S[^<>]*?\S>|\{\S[^{}]*?\S}|-\S[^-]*?\S-|\|\S[^|]*?\S\||/\S[^/]*?\S/|\\\S[^\\]*?\S\\)(\s+|$)", " ", completion.choices[0].text).replace("\n\n", "\n").replace(":\n", ": ").replace("  ", " ").strip().split("\n")
                remaining = len(lines)
                title = re.sub(r"[^A-Za-z0-9 ]+", "", lines.pop(0)[6:]).strip().replace(" ", "_").upper().replace("I", "i")
                progress = 1
                await message.edit(embed=discord.Embed(title=f"{int(100 * (progress / remaining))}%", color=0xf5f306).set_footer(text="This may take a while."))
                transcript = []
                combined = AudioSegment.empty()
                loop = asyncio.get_running_loop()
                for line in lines:
                    loud = False
                    line = line.strip()
                    lower = line.lower()
                    if lower.startswith("spongebob:"):
                        tts = await asyncio.wait_for(loop.run_in_executor(None, fy.say, line[10:].strip(), "weight_5by9kjm8vr8xsp7abe8zvaxc8"), 180)
                    elif lower.startswith("patrick:"):
                        tts = await asyncio.wait_for(loop.run_in_executor(None, fy.say, line[8:].strip(), "weight_154man2fzg19nrtc15drner7t"), 180)
                    elif lower.startswith("squidward:"):
                        tts = await asyncio.wait_for(loop.run_in_executor(None, fy.say, line[10:].strip(), "weight_y9arhnd7wjamezhqd27ksvmaz"), 180)
                    elif lower.startswith("loudward:"):
                        tts = await asyncio.wait_for(loop.run_in_executor(None, fy.say, line[9:].strip(), "weight_y9arhnd7wjamezhqd27ksvmaz"), 180)
                        loud = True
                    elif lower.startswith("gary:"):
                        tts = None
                        seg = sfx_gary
                    elif lower.startswith("plankton:"):
                        tts = await asyncio.wait_for(loop.run_in_executor(None, fy.say, line[9:].strip(), "weight_ahxbf2104ngsgyegncaefyy6j"), 180)
                    elif lower.startswith("mr. krabs:"):
                        tts = await asyncio.wait_for(loop.run_in_executor(None, fy.say, line[10:].strip(), "weight_5bxbp9xqy61svfx03b25ezmwx"), 180)
                    elif lower.startswith("karen:"):
                        tts = await asyncio.wait_for(loop.run_in_executor(None, fy.say, line[6:].strip(), "weight_eckp92cd68r4yk68n6re3fwcb"), 180)
                    elif lower.startswith("sandy:"):
                        tts = await asyncio.wait_for(loop.run_in_executor(None, fy.say, line[6:].strip(), "weight_tzgp5df2xzwz7y7jzz7at96jf"), 180)
                    elif lower.startswith("mrs. puff:"):
                        tts = await asyncio.wait_for(loop.run_in_executor(None, fy.say, line[10:].strip(), "weight_129qhgze57zhndkkcq83e6b2a"), 180)
                    elif lower.startswith("squilliam:"):
                        tts = await asyncio.wait_for(loop.run_in_executor(None, fy.say, line[10:].strip(), "weight_zmjv8223ed6wx1fp234c79v9s"), 180)
                    elif lower.startswith("larry:"):
                        tts = await asyncio.wait_for(loop.run_in_executor(None, fy.say, line[6:].strip(), "weight_k7qvaffwsft6vxbcps4wbyj58"), 180)
                    elif lower.startswith("bubble bass:"):
                        tts = await asyncio.wait_for(loop.run_in_executor(None, fy.say, line[12:].strip(), "weight_h9g7rh6tj2hvfezrz8gjs4gwa"), 180)
                    elif lower.startswith("bubble buddy:"):
                        tts = await asyncio.wait_for(loop.run_in_executor(None, fy.say, line[13:].strip(), "weight_sbr0372ysxbdahcvej96axy1t"), 180)
                    elif lower.startswith("french narrator:"):
                        tts = await asyncio.wait_for(loop.run_in_executor(None, fy.say, line[16:].strip(), "weight_edzcfmq6y0vj7pte9pzhq5b6j"), 180)
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
                    if random.randrange(20) > 0 and not line.endswith("-"):
                        combined = combined.append(silence_line, 0)
                    await message.edit(embed=discord.Embed(title=f"{int(100 * (progress / remaining))}%", color=0xf5f306).set_footer(text="This may take a while."))
                sfx = random.choice([sfx_steel_sting, sfx_boowomp, sfx_disgusting, sfx_vibe_link_b, sfx_this_guy_stinks, sfx_my_leg, sfx_you_what, sfx_dolphin])
                song = random.choices([music_closing_theme, music_tip_top_polka, music_rake_hornpipe, music_seaweed, music_sneaky_snitch, music_better_call_saul], [10, 10, 10, 10, 1, 1])[0]
                music = silence_music.append(song.fade_in(10000), 0)
                while len(music) < len(combined):
                    music = music.append(song, 0)
                final = silence_transition.append(combined.overlay(music).overlay(sfx, random.randrange(len(combined) - len(sfx))), 0).overlay(sfx_transition)
                with BytesIO() as episode:
                    final.export(episode, "mp3")
                    await message.edit(content="***[Enjoying this bot? Consider donating!](https://github.com/sponsors/jeremynoesen)***", embed=discord.Embed(color=0xf5f306).set_footer(text="\n".join(transcript)), attachments=[discord.File(episode, f"{title}.mp3")])
                cooldown[inter.user.id] = time.time()
            except:
                try:
                    await message.edit(content=None, embed=embed_error_failed)
                except:
                    try:
                        await inter.edit_original_response(content=None, embed=embed_error_failed)
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

