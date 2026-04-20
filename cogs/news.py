"""
News episode type, based on AI Sponge Rehydrated news topics.

Written by Jeremy Noesen
"""

from typing import Literal
from random import randint, randrange, choice, choices
from re import sub
from math import ceil
from io import BytesIO
from discord import Embed, Interaction, Color, File
from discord.utils import escape_markdown
from discord.ext.commands import GroupCog, Range
from discord.app_commands import Range, describe, command
from pydub import AudioSegment
from pydub.effects import high_pass_filter
from tts import speak
from llm import write


# Embed settings and static embeds
embed_color = Color.dark_theme()
embed_episode_start = Embed(title="Generating...", description="Writing script...", color=embed_color)
embed_episode_end = Embed(title="Generating...", description="Mixing audio...", color=embed_color)
embed_tts = Embed(title="Generating...", description="Speaking text...", color=embed_color)
embed_chat = Embed(title="Generating...", description="Writing response...", color=embed_color)
embed_failed = Embed(title="Failed.", description="An error occurred.", color=embed_color)
embed_not_permitted = Embed(title="Not Permitted.", description="> **[Subscribe to the AI Sponge Lite Patreon](https://www.patreon.com/cw/AISpongeLite/membership)**\n> **or boost this server to use AI Sponge Lite.**", color=embed_color).set_image(url="attachment://explodeward.gif")
embed_delete_after = 30

# Regex patterns for script modification
regex_actions = r"^[*<([][^:@#]+?[])>*]\s+"

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
    "Perch Perkins": 0x987cb4,
    "Pearl": 0xa7b2b3,
    "DoodleBob": 0x9a94a0,
    "Mr. Fish": 0x999072,
    "Flying Dutchman": 0x11c304,
    "King Neptune": 0x82f386,
    "Man Ray": 0x0b4881,
    "Dirty Bubble": 0x7c522d
}

# Gain settings for audio segments
gain_music = -35
gain_sfx = -25
gain_voice = -15

# Music audio segment
music_just_breaking_softer = AudioSegment.from_mp3("audio/music/just_breaking_softer.mp3")

# SFX audio segments
sfx_random = {
    AudioSegment.from_wav("audio/sfx/random/fling_1.wav"): 10,
    AudioSegment.from_wav("audio/sfx/random/fling_2.wav"): 10,
    AudioSegment.from_wav("audio/sfx/random/kick.wav"): 10,
    AudioSegment.from_wav("audio/sfx/random/squish_1.wav"): 10,
    AudioSegment.from_wav("audio/sfx/random/squish_2.wav"): 10,
    AudioSegment.from_wav("audio/sfx/random/explosion.wav"): 10,
    AudioSegment.from_wav("audio/sfx/random/ignite.wav"): 10,
    AudioSegment.from_wav("audio/sfx/random/steel_sting.wav"): 1,
    AudioSegment.from_wav("audio/sfx/random/boowomp.wav"): 1,
    AudioSegment.from_wav("audio/sfx/random/my_leg_1.wav"): 1,
    AudioSegment.from_wav("audio/sfx/random/my_leg_2.wav"): 1,
    AudioSegment.from_wav("audio/sfx/random/bonk.wav"): 1,
    AudioSegment.from_wav("audio/sfx/random/foghorn.wav"): 1,
    AudioSegment.from_wav("audio/sfx/random/vibe_link_b.wav"): 1,
    AudioSegment.from_wav("audio/sfx/random/this_guy_stinks.wav"): 1,
    AudioSegment.from_wav("audio/sfx/random/you_what.wav"): 1,
    AudioSegment.from_wav("audio/sfx/random/dolphin.wav"): 1,
    AudioSegment.from_wav("audio/sfx/random/boo_you_stink.wav"): 1,
    AudioSegment.from_wav("audio/sfx/random/dramatic_cue_a.wav"): 1,
    AudioSegment.from_wav("audio/sfx/random/dramatic_cue_d.wav"): 1,
    AudioSegment.from_wav("audio/sfx/random/alarm.wav"): 1,
    AudioSegment.from_wav("audio/sfx/random/phone_call.wav"): 1
}

# Transition audio segments
transition = AudioSegment.from_wav("audio/transition/news.wav")
transition = transition.apply_gain(gain_sfx - transition.dBFS)

# Voice audio segments
voice_gary = [AudioSegment.from_wav(f"audio/voice/gary_{i}.wav") for i in range(1, 7)]
voice_doodlebob = [AudioSegment.from_wav(f"audio/voice/doodlebob_{i}.wav") for i in range(1, 19)]
voice_failed = AudioSegment.from_wav("audio/voice/failed.wav")

# Silence audio segments
silence_line = AudioSegment.silent(400)
silence_intro = AudioSegment.silent(2000)
silence_music = AudioSegment.silent(7500)
silence_phone = AudioSegment.silent(400)
silence_outro = AudioSegment.silent(500)

# Literal type
literal_characters = Literal["SpongeBob", "Patrick", "Squidward", "Sandy", "Mr. Krabs", "Plankton", "Gary", "Mrs. Puff", "Larry", "Squilliam", "Karen", "Narrator", "Bubble Buddy", "Bubble Bass", "Perch Perkins", "Pearl", "DoodleBob", "Mr. Fish", "Flying Dutchman", "King Neptune", "Man Ray", "Dirty Bubble"]

# Character limits for input and output
char_limit_min = 1
char_limit_max = 512


class News(GroupCog, name="news", description="Generate episodes, TTS, and chats based on news topics."):
    """
    Cog for generating news episodes, TTS, and chats.
    """


    def __init__(self, bot):
        """
        Initialize the cog
        :param bot: The bot instance
        """

        self.bot = bot


    @command(name="episode", description="Generate a news episode.")
    @describe(topic="What the episode is about.", chaos="Whether to simulate chaos hour.")
    async def episode(self, interaction: Interaction, topic: Range[str, char_limit_min, char_limit_max], chaos: bool = False):
        """
        Generate a news episode about a topic.
        :param interaction: Interaction created by the command
        :param topic: What the episode is about
        :param chaos: Whether to simulate chaos hour
        :return: None
        """

        # Check if user has access
        if interaction.user.premium_since is None and interaction.user.id not in self.bot.permitted_discord_user_ids:
            await interaction.response.send_message(embed=embed_not_permitted, file=File("image/misc/explodeward.gif"), ephemeral=True, delete_after=embed_delete_after)
            return

        # Start generation
        try:

            # Show generating message
            await interaction.response.send_message(embed=embed_episode_start)

            # Log the interaction
            await self.bot.logging_channel.send(embed=Embed(title=interaction.user.id, description=f"/news episode topic:{escape_markdown(topic, as_needed=True)} chaos:{chaos}", color=embed_color))

            # Generate the script
            script = await write(f"Write a fucking chaotic, profanity-filled, and morally incorrect script for a Bikini Bottom news report about a topic that is broadcasted live from the Bikini Bottom News Studio and features Perch Perkins and Mr. Fish as news anchors, and any other characters mentioned in the topic as callers. Only respond with a two-word, SpongeBob-style breaking news headline using the format: title: <title> followed by ten lines of brief character dialogue using the format: <character>: <dialogue>. The topic is: \"{topic}\".")

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
            embed_output = Embed(title=escape_markdown(title_formatted, as_needed=True), color=0x316ec3)

            # Variables used for generation data
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

                # Limit the audio length based on text length
                seg = seg[:1000 + (len(output_line) * 100)]

                # Apply phone filter for callers
                if character not in ["Perch Perkins", "Mr. Fish"]:
                    seg = high_pass_filter(seg, 3000)
                    combined = combined.append(silence_phone, 0)

                # Apply gain
                seg = seg.apply_gain(gain_voice-seg.dBFS)

                # Add the line to the combined audio segment
                combined = combined.append(seg, 0)

                # Add line spacing unless a cutoff event occurs
                if output_line[-1] not in "-–—":
                    combined = combined.append(silence_line, 0)

                # Add the line to the output script
                embed_output.add_field(name="", value=f"{self.bot.fetched_emojis[character.replace(' ', '').replace('.', '')]} ​ ​ {escape_markdown(output_line, as_needed=True)}", inline=False)

                # Line completed
                current_line += 1

                # Embeds have a 25 field limit. Skip remaining lines.
                if current_line > 25:
                    break

            # Show final generating message
            await interaction.edit_original_response(embed=embed_episode_end)

            # Add silence at the end of the episode
            combined = combined.append(silence_outro, 0)

            # Add music to the episode
            music = music_just_breaking_softer
            music = music.apply_gain((gain_music + randint(-5, 5)) - music.dBFS)
            music_loop = silence_music.append(music, 0)
            while len(music_loop) < len(combined):
                music_loop = music_loop.append(music, 0)
            combined = combined.overlay(music_loop)

            # Add random SFX to the episode
            for sfx in choices(list(sfx_random.keys()), list(sfx_random.values()), k=(ceil(len(combined) / 1000) if chaos else randint(1, ceil(min(total_lines, 25) / 5)))):
                combined = combined.overlay(sfx.apply_gain((gain_sfx + randint(-5, 5)) - sfx.dBFS), randrange(len(combined)))

            # Add the transition SFX to the beginning of the episode and fade out the end
            combined = silence_intro.append(combined, 0).overlay(transition).fade_out(len(silence_outro))

            # Export the episode and send it
            with BytesIO() as output:
                combined.export(output, "mp3", bitrate="320k")
                await interaction.edit_original_response(embed=embed_output, attachments=[
                    File(output, title_formatted.replace("/", "\\").replace("\n", " ") + ".mp3")])

        # Generation failed
        except:
            with BytesIO() as output:
                voice_failed.export(output, "wav")
                await interaction.edit_original_response(embed=embed_failed, attachments=[File(output, "Failed.wav")])


    @command(name="tts", description="Make a news character speak text.")
    @describe(character="Who should speak.", text="What should be said.")
    async def tts(self, interaction: Interaction, character: literal_characters, text: Range[str, char_limit_min, char_limit_max]):
        """
        Make a character from news episodes speak text using text-to-speech.
        :param interaction: Interaction created by the command
        :param character: Who should speak
        :param text: What should be said
        :return: None
        """

        # Check if user has access
        if interaction.user.premium_since is None and interaction.user.id not in self.bot.permitted_discord_user_ids:
            await interaction.response.send_message(embed=embed_not_permitted, file=File("image/misc/explodeward.gif"), ephemeral=True, delete_after=embed_delete_after)
            return

        # Start generation
        try:

            # Show generating message
            await interaction.response.send_message(embed=embed_tts)

            # Log the interaction
            await self.bot.logging_channel.send(embed=Embed(title=interaction.user.id, description=f"/news tts character:{character} text:{escape_markdown(text, as_needed=True)}", color=embed_color))

            # Speak text using voice files for DoodleBob
            if character == "DoodleBob":
                seg = choice(voice_doodlebob)

            # Speak text using voice files for Gary
            elif character == "Gary":
                seg = choice(voice_gary)

            # Speak line for all other characters
            else:
                seg = await speak(character, text)

            # Limit the audio length based on text length
            seg = seg[:1000 + (len(text) * 100)]

            # Apply phone to callers
            if character not in ["Perch Perkins", "Mr. Fish"]:
                seg = high_pass_filter(seg, 3000)
                seg = silence_phone.append(seg, 0)

            # Apply gain
            seg = seg.apply_gain(gain_voice-seg.dBFS)

            # Export and send the file
            with BytesIO() as output:
                seg.export(output, "wav")
                await interaction.edit_original_response(embed=Embed(color=characters[character], description=escape_markdown(text, as_needed=True)).set_author(name=character, icon_url=self.bot.fetched_emojis[character.replace(' ', '').replace('.', '')].url), attachments=[
                    File(output, character + ": " + text.replace("/", "\\").replace("\n", " ") + ".wav")])

        # Generation failed
        except:
            with BytesIO() as output:
                voice_failed.export(output, "wav")
                await interaction.edit_original_response(embed=embed_failed, attachments=[File(output, "Failed.wav")])


    @command(name="chat", description="Chat with a news character.")
    @describe(character="Who to chat with.", message="What to say to them.")
    async def chat(self, interaction: Interaction, character: literal_characters, message: Range[str, char_limit_min, char_limit_max]):
        """
        Chat with one of the characters from news episodes.
        :param interaction: Interaction created by the command
        :param character: Who to chat with
        :param message: What to say to them
        :return: None
        """

        # Check if user has access
        if interaction.user.premium_since is None and interaction.user.id not in self.bot.permitted_discord_user_ids:
            await interaction.response.send_message(embed=embed_not_permitted, file=File("image/misc/explodeward.gif"), ephemeral=True, delete_after=embed_delete_after)
            return

        # Start generation
        try:

            # Show generating message
            await interaction.response.send_message(embed=embed_chat)

            # Log the interaction
            await self.bot.logging_channel.send(embed=Embed(title=interaction.user.id, description=f"/news chat character:{character} message:{escape_markdown(message, as_needed=True)}", color=embed_color))

            # Generate the chat response
            response = await write(f"Write a response to a news interview question as {character} from SpongeBob. Only respond with {character}'s brief response using the format: {character}: <response>. The question from \"{interaction.user.display_name}\" says: \"{message}\".")

            # Clean the response text
            output = escape_markdown(sub(regex_actions, "", response.split(":", 1)[1].strip())[:char_limit_max].strip(), as_needed=True)

            # Send the response
            await interaction.edit_original_response(embed=Embed(description=output, color=characters[character]).set_footer(text=message, icon_url=interaction.user.display_avatar.url).set_author(name=character, icon_url=self.bot.fetched_emojis[character.replace(' ', '').replace('.', '')].url))

        # Generation failed
        except:
            with BytesIO() as output:
                voice_failed.export(output, "wav")
                await interaction.edit_original_response(embed=embed_failed, attachments=[File(output, "Failed.wav")])


async def setup(bot):
    """
    Register the News cog with the bot.
    :param bot: The bot instance
    :return: None
    """

    await bot.add_cog(News(bot))
