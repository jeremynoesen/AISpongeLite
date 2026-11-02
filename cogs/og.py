"""
OG episode type, based on OG AI Sponge topics.

Written by Jeremy Noesen
"""

from asyncio import sleep
from logging import getLogger
from typing import Literal, get_args
from random import randrange, choices
from math import ceil
from io import BytesIO
from discord import Embed, Interaction, File
from discord.utils import escape_markdown
from discord.ext.commands import GroupCog
from discord.app_commands import Range, describe, command
from pydub import AudioSegment
from pydub.effects import high_pass_filter
from Pylette import extract_colors
from tts import speak
from llm import write

# Set up logger
logger = getLogger(__name__)

# Reused embeds
embed_failed = Embed(title="Generation Failed!", description="Edit your input, or try again later.", color=0xff0000)
embed_not_permitted = Embed(title="Gain Access to AI Sponge Lite!", description="**[Purchase a subscription](https://www.patreon.com/cw/AISpongeLite/membership)** to unlock **/og** commands.", color=0x1849b0).set_image(url="attachment://banner.png")
embed_delete_after = 30

# Characters and their embed colors
characters = Literal["SpongeBob", "Patrick", "Squidward", "Sandy", "Mr. Krabs", "Plankton", "Gary", "Mrs. Puff", "Larry"]
data_characters = {
    "SpongeBob": 0xf6ea71,
    "Patrick": 0xdb635e,
    "Squidward": 0x9edad3,
    "Sandy": 0xf3f3f1,
    "Mr. Krabs": 0xf94b30,
    "Plankton": 0x208346,
    "Gary": 0xb48e83,
    "Mrs. Puff": 0xf8f0bc,
    "Larry": 0xfa771b
}

# Gain settings for audio segments
gain_music = -35
gain_sfx = -25
gain_transition = -25
gain_voice = -15
gain_voice_loud = -10
gain_voice_distort = 20

# Filter cutoffs
cutoff_filter = 200

# Music audio segments
music_closing_theme = AudioSegment.from_wav("audio/music/closing_theme.wav")[:-3000]

# SFX audio segments
sfx_random = {
    AudioSegment.from_wav("audio/sfx/random/steel_sting.wav"): 10,
    AudioSegment.from_wav("audio/sfx/random/boowomp.wav"): 5,
    AudioSegment.from_wav("audio/sfx/random/kiss.wav"): 1
}

# Transition audio segments
transition = AudioSegment.from_wav("audio/transition/og.wav")
transition = transition.apply_gain(gain_transition - transition.dBFS)

# Voice audio segments
voice_gary = AudioSegment.from_wav("audio/voice/gary/gary_1.wav")
voice_failed = AudioSegment.from_wav("audio/voice/failed.wav")

# Silence audio segments
silence_line = AudioSegment.silent(1500)
silence_intro = AudioSegment.silent(750)

# Limits for input and output
char_limit_min = 1
char_limit_max = 512


class OG(GroupCog, name="og", description="Generate episodes, TTS, and chats based on OG topics."):
    """
    Cog for generating OG episodes, TTS, and chats.
    """


    def __init__(self, bot):
        """
        Initialize the cog
        :param bot: The bot instance
        """

        self.bot = bot


    @command(name="episode", description="Generate an OG episode.")
    @describe(topic="What the episode is about.")
    async def episode(self, interaction: Interaction, topic: Range[str, char_limit_min, char_limit_max]):
        """
        Generate an OG episode about a topic.
        :param interaction: Interaction created by the command
        :param topic: What the episode is about
        :return: None
        """

        # Check if user has access
        if interaction.user.id not in self.bot.permitted_discord_user_ids:
            await interaction.response.send_message(embed=embed_not_permitted, file=File("image/profile/banner.png"), ephemeral=True, delete_after=embed_delete_after)
            return

        # Start generation
        try:

            # Display version of topic
            topic_display = topic.replace("```", "'''")

            # Show generating message
            await interaction.response.send_message(embed=Embed(description=f"```{topic_display}```\n-# {self.bot.fetched_emojis['Processing']} ​ ​ ​ Writing script..."))

            # Log the interaction
            await self.bot.logging_channel.send(embed=Embed(description=f"```{topic_display}```\n{interaction.user.mention}"))

            # Generate the script
            script = await write(f"Write a script for a SpongeBob episode about a topic that features SpongeBob, Patrick, Squidward, and any other characters mentioned in the topic. Only respond with a two-word, SpongeBob-style title using the format: title: <title> followed by around twenty lines of character dialogue using the format: <character>: <dialogue>. The topic is: \"{topic}\".")

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
            line_index = 1
            line_count = len(lines)

            # Create the embed for the output
            embed_output = Embed(title=escape_markdown(title_formatted), color=0xfef4ad)

            # Variables used for generation data
            combined = AudioSegment.empty()

            # Process each line
            for line in lines:

                # Update generation status
                await interaction.edit_original_response(embed=Embed(description=f"```{topic_display}```\n-# {self.bot.fetched_emojis['Processing']} ​ ​ ​ Processing line {line_index} of {min(line_count, 25)}..."))

                # Skip line if it is improperly formatted
                line_parts = line.split(":", 1)
                if len(line_parts) != 2:
                    line_count -= 1
                    continue

                # Skip line if it is too short
                current_line = line_parts[1].strip()[:char_limit_max].strip()
                if len(current_line) < char_limit_min:
                    line_count -= 1
                    continue

                # Get the character
                current_character = ""
                string_casefold = line_parts[0].casefold()
                for character in list(get_args(characters)):
                    character_casefold = character.casefold()
                    if character_casefold in string_casefold or string_casefold in character_casefold:
                        current_character = character
                        break

                # Skip line if no character was found
                if not current_character:
                    line_count -= 1
                    continue

                # Speak line using voice file for Gary
                if current_character == "Gary":
                    seg = voice_gary

                # Speak line for all other characters
                else:

                    # Attempt to speak line
                    try:
                        seg = await speak(current_character, current_line, "uberduck")

                    # Line failed to generate
                    except Exception as exception:

                        # Log error
                        logger.warning(exception)

                        # Use failed sound as seg
                        seg = voice_failed

                # Apply gain, forcing a loud event sometimes
                if randrange(20) == 0:
                    seg = seg.apply_gain(gain_voice_distort)
                    seg = seg.apply_gain(gain_voice_loud - seg.dBFS)
                else:
                    seg = seg.apply_gain(gain_voice - seg.dBFS)

                # Add the line to the combined audio segment
                combined = combined.append(seg, 0)

                # Add line spacing
                combined = combined.append(silence_line, 0)

                # Add the line to the output script
                embed_output.add_field(name="", value=f"{self.bot.fetched_emojis['OG_' + current_character.replace(' ', '').replace('.', '')]} ​ ​ ​ {escape_markdown(current_line)}", inline=False)

                # Line completed
                line_index += 1

                # Embeds have a 25 field limit. Skip remaining lines.
                if line_index > 25:
                    break

            # Show final generating message
            await interaction.edit_original_response(embed=Embed(description=f"```{topic_display}```\n-# {self.bot.fetched_emojis['Processing']} ​ ​ ​ Mixing audio..."))

            # Add random SFX to the episode
            for sfx in choices(list(sfx_random.keys()), list(sfx_random.values()), k=ceil(min(line_count, 25) / 5)):
                combined = combined.overlay(sfx.apply_gain(gain_sfx - sfx.dBFS), randrange(len(combined)))

            # Add the transition SFX to the beginning of the episode
            combined = transition.append(silence_intro).append(combined, 0)

            # Add music to the episode
            music = music_closing_theme.apply_gain(gain_music - music_closing_theme.dBFS)
            music_loop = music[randrange(len(music)):]
            while len(music_loop) < len(combined):
                music_loop = music_loop.append(music, 0)
            combined = combined.overlay(music_loop)

            # Apply audio filter to episode
            combined = high_pass_filter(combined, cutoff_filter)

            # Export the episode and send it
            with BytesIO() as output:
                combined.export(output, "mp3", bitrate="128k")
                await interaction.edit_original_response(embed=embed_output, attachments=[
                    File(output, title_formatted.replace("/", "\\").replace("\n", " ") + ".mp3")])

        # Generation failed
        except Exception as exception:

            # Log error
            logger.warning(exception)

            # Show failed message
            with BytesIO() as output:
                voice_failed.export(output, "wav")
                await interaction.edit_original_response(embed=embed_failed, attachments=[File(output, "Failed.wav")])


    @command(name="tts", description="Make an OG character speak text.")
    @describe(character="Who should speak.", text="What should be said.", loud="Whether to speak loudly.")
    async def tts(self, interaction: Interaction, character: characters, text: Range[str, char_limit_min, char_limit_max], loud: bool = False):
        """
        Make a character from OG episodes speak text using text-to-speech.
        :param interaction: Interaction created by the command
        :param character: Who should speak
        :param text: What should be said
        :param loud: Whether to speak loudly
        :return: None
        """

        # Check if user has access
        if interaction.user.id not in self.bot.permitted_discord_user_ids:
            await interaction.response.send_message(embed=embed_not_permitted, file=File("image/profile/banner.png"), ephemeral=True, delete_after=embed_delete_after)
            return

        # Start generation
        try:

            # Show transcript and recording indicator
            recording_embed = Embed(description=f"-# {self.bot.fetched_emojis['Processing']} ​ ​ ​ **{character}** is recording...")
            transcript_embed = Embed(color=data_characters[character], description=escape_markdown(text)).set_author(name=character, icon_url=self.bot.fetched_emojis['OG_' + character.replace(' ', '').replace('.', '')].url)
            await interaction.response.send_message(embeds=[recording_embed, transcript_embed])

            # Log the interaction
            await self.bot.logging_channel.send(embed=Embed(description=f"```{text}```\n{interaction.user.mention}"))

            # Speak text using voice file for Gary
            if character == "Gary":
                seg = voice_gary

            # Speak line for all other characters
            else:
                seg = await speak(character, text, "uberduck")

            # Apply gain
            if loud:
                seg = seg.apply_gain(gain_voice_distort)
                seg = seg.apply_gain(gain_voice_loud - seg.dBFS)
            else:
                seg = seg.apply_gain(gain_voice - seg.dBFS)

            # Apply audio filter
            seg = high_pass_filter(seg, cutoff_filter)

            # Export and send the file
            with BytesIO() as output:
                seg.export(output, "mp3", bitrate="128k")
                await interaction.edit_original_response(embeds=[transcript_embed], attachments=[
                    File(output, character + ": " + text.replace("/", "\\").replace("\n", " ") + ".mp3")])

        # Generation failed
        except Exception as exception:

            # Log error
            logger.warning(exception)

            # Show failed message
            with BytesIO() as output:
                voice_failed.export(output, "wav")
                await interaction.edit_original_response(embed=embed_failed, attachments=[File(output, "Failed.wav")])


    @command(name="chat", description="Chat with an OG character.")
    @describe(character="Who to chat with.", message="What to say to them.")
    async def chat(self, interaction: Interaction, character: characters, message: Range[str, char_limit_min, char_limit_max]):
        """
        Chat with one of the characters from OG episodes.
        :param interaction: Interaction created by the command
        :param character: Who to chat with
        :param message: What to say to them
        :return: None
        """

        # Check if user has access
        if interaction.user.id not in self.bot.permitted_discord_user_ids:
            await interaction.response.send_message(embed=embed_not_permitted, file=File("image/profile/banner.png"), ephemeral=True, delete_after=embed_delete_after)
            return

        # Start generation
        try:

            # Show user's own message
            user_embed = Embed(description=escape_markdown(message), color=int(extract_colors(image=interaction.user.display_avatar.url)[0].hex[1:], 16)).set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
            await interaction.response.send_message(embeds=[user_embed])

            # Log interaction
            await self.bot.logging_channel.send(embed=Embed(description=f"```{message}```\n{interaction.user.mention}"))

            # Small delay for visual effect
            await sleep(1)

            # Show typing indicator
            typing_embed = Embed(description=f"-# {self.bot.fetched_emojis['Processing']} ​ ​ ​ **{character}** is typing...")
            await interaction.edit_original_response(embeds=[user_embed, typing_embed])

            # Generate chat response
            response = await write(f"Write a response as {character} from SpongeBob. Only respond with {character}'s response using the format: {character}: <response>. The message says: \"{message}\".")
            output = escape_markdown(response.split(":", 1)[1].strip()[:char_limit_max].strip())

            # Show character's response
            character_embed = Embed(description=output, color=data_characters[character]).set_author(name=character, icon_url=self.bot.fetched_emojis['OG_' + character.replace(' ', '').replace('.', '')].url)
            await interaction.edit_original_response(embeds=[user_embed, character_embed])

        # Generation failed
        except Exception as exception:

            # Log error
            logger.warning(exception)

            # Show failed message
            with BytesIO() as output:
                voice_failed.export(output, "wav")
                await interaction.edit_original_response(embed=embed_failed, attachments=[File(output, "Failed.wav")])


async def setup(bot):
    """
    Register the OG cog with the bot.
    :param bot: The bot instance
    :return: None
    """

    # Register cog
    await bot.add_cog(OG(bot))
