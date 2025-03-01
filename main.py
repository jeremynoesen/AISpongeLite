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
music_hello_sailor_b = load_wav("music/hello_sailor_b.wav", gain=-35)
music_stars_and_games = load_wav("music/stars_and_games.wav", gain=-35)
music_rock_bottom = load_wav("music/rock_bottom.wav", gain=-35)
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
ambiance_day = load_wav("ambiance/day.wav", start=2000, end=-1000, gain=-45)
ambiance_night = load_wav("ambiance/night.wav", start=100, end=-4000, gain=-45)
ambiance_rain = load_wav("ambiance/rain.wav", start=1000, end=-1000)
voice_gary = load_wav("voice/gary.wav", end=6000)
silence_line = AudioSegment.silent(500)
silence_transition = AudioSegment.silent(1100)
silence_music = AudioSegment.silent(2450)
emoji_spongebob = os.getenv("EMOJI_SPONGEBOB")
emoji_patrick = os.getenv("EMOJI_PATRICK")
emoji_squidward = os.getenv("EMOJI_SQUIDWARD")
emoji_gary = os.getenv("EMOJI_GARY")
emoji_plankton = os.getenv("EMOJI_PLANKTON")
emoji_mrkrabs = os.getenv("EMOJI_MRKRABS")
emoji_karen = os.getenv("EMOJI_KAREN")
emoji_sandy = os.getenv("EMOJI_SANDY")
emoji_mrspuff = os.getenv("EMOJI_MRSPUFF")
emoji_squilliam = os.getenv("EMOJI_SQUILLIAM")
emoji_larry = os.getenv("EMOJI_LARRY")
emoji_bubblebass = os.getenv("EMOJI_BUBBLEBASS")
emoji_bubblebuddy = os.getenv("EMOJI_BUBBLEBUDDY")
emoji_frenchnarrator = os.getenv("EMOJI_FRENCHNARRATOR")
embed_ready = discord.Embed(title="Ready", color=0xf5f306).set_footer(text="Ready to generate.")
embed_error_permissions = discord.Embed(title="Generating...", description="# > Failed", color=0xf5f306).set_footer(text="Missing permissions.")
embed_error_failed = discord.Embed(title="Generating...", description="# > Failed", color=0xf5f306).set_footer(text="An error occurred.")
generating = False
progress = 0
cooldown = {}
remove_cooldown_sku = int(os.getenv("REMOVE_COOLDOWN_SKU"))
remove_cooldown_button = discord.ui.Button(style=discord.ButtonStyle.premium, sku_id=remove_cooldown_sku)


@tree.command(name="generate", description="Generate an episode.")
@app_commands.describe(topic="Topic of episode.")
async def generate(inter: discord.Interaction, topic: str):
    if not (inter.app_permissions.view_channel and inter.app_permissions.embed_links and inter.app_permissions.attach_files and inter.app_permissions.read_message_history and inter.app_permissions.use_external_emojis and inter.app_permissions.send_messages):
        try:
            await inter.response.send_message(embed=embed_error_permissions)
        except:
            pass
    elif inter.user.id not in cooldown.keys() or time.time() - cooldown[inter.user.id] > 300:
        if inter.user.id in cooldown.keys():
            del cooldown[inter.user.id]
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
                    prompt=f"Create a vulgar, morally incorrect script for a scene from SpongeBob where characters discuss a topic. Common characters include SpongeBob, Patrick, Squidward, Mr. Krabs, Plankton, Karen, and Sandy. Rare characters include Gary, Larry, Mrs. Puff, Squilliam, Bubble Bass, Bubble Buddy, and French Narrator. Include 3 - 5 characters max. Use the format: Character: <dialogue>. Only reply with coherent character dialogue. Around 12 - 15 lines of dialogue with talking only. Include a relevant 1 - 2 word title with format: Title: <title>. The topic is: {topic}"
                )
                lines = re.sub(r"(^|\s+)(\(+\S[^()]+\S\)+|\[+\S[^\[\]]+\S]+|\*+\S[^*]+\S\*+|<+\S[^<>]+\S>+|\{+\S[^{}]+\S}+|-+\S[^-]+\S-+|\|+\S[^|]+\S\|+|/+\S[^/]+\S/+|\\+\S[^\\]+\S\\+)(\s+|$)", " ", completion.choices[0].text).replace("\n\n", "\n").replace(":\n", ": ").replace("  ", " ").strip().split("\n")
                remaining = len(lines)
                title = lines.pop(0)[6:].strip().upper().replace("I", "i")
                if not title:
                    title = "EPiSODE"
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
                        stripped = line[10:].strip()
                        tts = await asyncio.wait_for(loop.run_in_executor(None, fy.say, stripped, "weight_5by9kjm8vr8xsp7abe8zvaxc8"), 180)
                        line = "- " + emoji_spongebob + " " + stripped
                    elif lower.startswith("patrick:"):
                        stripped = line[8:].strip()
                        tts = await asyncio.wait_for(loop.run_in_executor(None, fy.say, stripped, "weight_154man2fzg19nrtc15drner7t"), 180)
                        line = "- " + emoji_patrick + " " + stripped
                    elif lower.startswith("squidward:"):
                        stripped = line[10:].strip()
                        tts = await asyncio.wait_for(loop.run_in_executor(None, fy.say, stripped, "weight_y9arhnd7wjamezhqd27ksvmaz"), 180)
                        line = "- " + emoji_squidward + " " + stripped
                    elif lower.startswith("loudward:"):
                        stripped = line[9:].strip()
                        tts = await asyncio.wait_for(loop.run_in_executor(None, fy.say, stripped, "weight_y9arhnd7wjamezhqd27ksvmaz"), 180)
                        line = "- " + emoji_squidward + " " + stripped
                        loud = True
                    elif lower.startswith("gary:"):
                        stripped = line[5:].strip()
                        tts = None
                        line = "- " + emoji_gary + " " + stripped
                        seg = voice_gary
                    elif lower.startswith("plankton:"):
                        stripped = line[9:].strip()
                        tts = await asyncio.wait_for(loop.run_in_executor(None, fy.say, stripped, "weight_ahxbf2104ngsgyegncaefyy6j"), 180)
                        line = "- " + emoji_plankton + " " + stripped
                    elif lower.startswith("loudton:"):
                        stripped = line[8:].strip()
                        tts = await asyncio.wait_for(loop.run_in_executor(None, fy.say, stripped, "weight_ahxbf2104ngsgyegncaefyy6j"), 180)
                        line = "- " + emoji_plankton + " " + stripped
                        loud = True
                    elif lower.startswith("mr. krabs:"):
                        stripped = line[10:].strip()
                        tts = await asyncio.wait_for(loop.run_in_executor(None, fy.say, stripped, "weight_5bxbp9xqy61svfx03b25ezmwx"), 180)
                        line = "- " + emoji_mrkrabs + " " + stripped
                    elif lower.startswith("karen:"):
                        stripped = line[6:].strip()
                        tts = await asyncio.wait_for(loop.run_in_executor(None, fy.say, stripped, "weight_eckp92cd68r4yk68n6re3fwcb"), 180)
                        line = "- " + emoji_karen + " " + stripped
                    elif lower.startswith("sandy:"):
                        stripped = line[6:].strip()
                        tts = await asyncio.wait_for(loop.run_in_executor(None, fy.say, stripped, "weight_tzgp5df2xzwz7y7jzz7at96jf"), 180)
                        line = "- " + emoji_sandy + " " + stripped
                    elif lower.startswith("mrs. puff:"):
                        stripped = line[10:].strip()
                        tts = await asyncio.wait_for(loop.run_in_executor(None, fy.say, stripped, "weight_129qhgze57zhndkkcq83e6b2a"), 180)
                        line = "- " + emoji_mrspuff + " " + stripped
                    elif lower.startswith("squilliam:"):
                        stripped = line[10:].strip()
                        tts = await asyncio.wait_for(loop.run_in_executor(None, fy.say, stripped, "weight_zmjv8223ed6wx1fp234c79v9s"), 180)
                        line = "- " + emoji_squilliam + " " + stripped
                    elif lower.startswith("larry:"):
                        stripped = line[6:].strip()
                        tts = await asyncio.wait_for(loop.run_in_executor(None, fy.say, stripped, "weight_k7qvaffwsft6vxbcps4wbyj58"), 180)
                        line = "- " + emoji_larry + " " + stripped
                    elif lower.startswith("bubble bass:"):
                        stripped = line[12:].strip()
                        tts = await asyncio.wait_for(loop.run_in_executor(None, fy.say, stripped, "weight_h9g7rh6tj2hvfezrz8gjs4gwa"), 180)
                        line = "- " + emoji_bubblebass + " " + stripped
                    elif lower.startswith("bubble buddy:"):
                        stripped = line[13:].strip()
                        tts = await asyncio.wait_for(loop.run_in_executor(None, fy.say, stripped, "weight_sbr0372ysxbdahcvej96axy1t"), 180)
                        line = "- " + emoji_bubblebuddy + " " + stripped
                    elif lower.startswith("french narrator:"):
                        stripped = line[16:].strip()
                        tts = await asyncio.wait_for(loop.run_in_executor(None, fy.say, stripped, "weight_edzcfmq6y0vj7pte9pzhq5b6j"), 180)
                        line = "- " + emoji_frenchnarrator + " " + stripped
                    else:
                        remaining -= 1
                        progress = int(100 * (completed / remaining))
                        await message.edit(embed=discord.Embed(title="Generating...", description=f"# > {progress}%", color=0xf5f306).set_footer(text=f"Skipped line."))
                        await client.change_presence(activity=discord.Game(f"Generating... {progress}%"), status=discord.Status.dnd)
                        continue
                    if tts is None:
                        remaining -= 1
                    else:
                        with BytesIO(tts.content) as wav:
                            seg = AudioSegment.from_wav(wav)
                        completed += 1
                    if loud or stripped.isupper() or random.randrange(100) == 0:
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
                    await message.edit(embed=discord.Embed(title="Generating...", description=f"# > {progress}%", color=0xf5f306).set_footer(text=f"Synthesized line {completed-1}/{remaining-1}."))
                    await client.change_presence(activity=discord.Game(f"Generating... {progress}%"), status=discord.Status.dnd)
                combined = combined.append(silence_line, 0)
                music = random.choices([music_closing_theme, music_tip_top_polka, music_rake_hornpipe, music_seaweed, music_hello_sailor_b, music_stars_and_games, music_rock_bottom, music_sneaky_snitch, music_better_call_saul], [10, 10, 10, 10, 5, 5, 5, 1, 1])[0]
                music_loop = silence_music.append(music.fade_in(10000), 0)
                while len(music_loop) < len(combined):
                    music_loop = music_loop.append(music, 0)
                combined = combined.overlay(music_loop)
                if random.randrange(5) > 0:
                    ambiance = random.choice([ambiance_day, ambiance_night])
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
                    sfx = random.choices([sfx_steel_sting, sfx_boowomp, sfx_disgusting, sfx_vibe_link_b, sfx_this_guy_stinks, sfx_my_leg, sfx_you_what, sfx_dolphin], [5, 5, 1, 1, 1, 1, 1, 1])[0]
                    combined = combined.overlay(sfx, random.randrange(len(combined)))
                combined = combined.fade_out(500)
                with BytesIO() as episode:
                    combined.export(episode, "ogg")
                    await message.edit(embed=discord.Embed(title=title, description="\n".join(transcript), color=0xf5f306).set_footer(text=f"{inter.user.display_name} – \"{topic}\"", icon_url=inter.user.display_avatar.url), attachments=[discord.File(episode, f"{title}.ogg")])
                    await client.change_presence(activity=discord.Game("Ready"), status=discord.Status.online)
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
            await inter.response.send_message(ephemeral=True, delete_after=10, embed=discord.Embed(title="Generating", description=f"# > {progress}%", color=0xf5f306).set_footer(text="Generating an episode."))
    else:
        view = discord.ui.View()
        view.add_item(remove_cooldown_button)
        await inter.response.send_message(ephemeral=True, delete_after=10, embed=discord.Embed(title=f"Cooldown", description=f"# > {int((300 - (time.time() - cooldown[inter.user.id])) / 60)}m {int((300 - (time.time() - cooldown[inter.user.id])) % 60)}s", color=0xf5f306).set_footer(text="You're on cooldown."), view=view)


@tree.command(name="status", description="Check if an episode can be generated.")
async def status(inter: discord.Interaction):
    if inter.user.id not in cooldown.keys() or time.time() - cooldown[inter.user.id] > 300:
        if inter.user.id in cooldown.keys():
            del cooldown[inter.user.id]
        if generating:
            await inter.response.send_message(ephemeral=True, delete_after=10, embed=discord.Embed(title="Generating", description=f"# > {progress}%", color=0xf5f306).set_footer(text="Generating an episode."))
        else:
            await inter.response.send_message(ephemeral=True, delete_after=10, embed=embed_ready)
    else:
        view = discord.ui.View()
        view.add_item(remove_cooldown_button)
        await inter.response.send_message(ephemeral=True, delete_after=10, embed=discord.Embed(title=f"Cooldown", description=f"# > {int((300 - (time.time() - cooldown[inter.user.id])) / 60)}m {int((300 - (time.time() - cooldown[inter.user.id])) % 60)}s", color=0xf5f306).set_footer(text="You're on cooldown."), view=view)


@client.event
async def on_ready():
    await tree.sync()


client.run(os.getenv("DISCORD_BOT_TOKEN"))

