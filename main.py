"""
AI Sponge Lite is a Discord bot that generates parody AI Sponge audio episodes, chats, and TTS inspired by
[AI Sponge Rehydrated](https://aisponge.riskivr.com/).

Written by Jeremy Noesen
"""

from os import getenv, listdir
from discord import Intents, Game
from discord.app_commands import AppInstallationType, AppCommandContext
from dotenv import load_dotenv
from discord.ext.commands import Bot
from asyncio import run

# Load environment variables from .env file
load_dotenv(override=True)

# List of cogs to load
COGS = [
    "cogs.access",
    "cogs.standard",
    "cogs.news"
]


class AISpongeLite(Bot):
    """
    Main bot class for AI Sponge Lite
    """


    def __init__(self):
        """
        Initialize the bot with command prefix, intents, and allowed contexts
        """

        super().__init__(command_prefix="/", intents=Intents.default(), allowed_installs=AppInstallationType(guild=True, user=False), allowed_contexts=AppCommandContext(guild=True, dm_channel=False, private_channel=True), activity=Game("4.1.0"))

        # Initialize variables used throughout the bot
        self.permitted_discord_user_ids = {int(x) for x in getenv("DISCORD_ADMIN_USER_IDS").split(",")}
        self.fetched_emojis = {}
        self.logging_channel = None


    async def setup_hook(self):
        """
        Upload assets, load cogs, and sync slash commands globally.
        :return: None
        """

        # Set bot avatar if it is missing
        if self.user.avatar is None:
            with open("image/profile/avatar.gif", "rb") as file:
                await self.user.edit(avatar=file.read())
                print("Uploaded avatar")

        # Set bot banner if it is missing
        if (await self.fetch_user(self.user.id)).banner is None:
            with open("image/profile/banner.png", "rb") as file:
                await self.user.edit(banner=file.read())
                print("Uploaded banner")

        # Fetch all application emojis
        self.fetched_emojis = {e.name: e for e in await self.fetch_application_emojis()}
        print(f"Fetched emojis: {set(self.fetched_emojis.keys())}")

        # Create missing application emojis
        for emoji_file in listdir("image/emoji"):
            emoji_name = emoji_file.split(".")[0]
            if emoji_name not in self.fetched_emojis.keys():
                with open(f"image/emoji/{emoji_file}", "rb") as file:
                    self.fetched_emojis[emoji_name] = await self.create_application_emoji(name=emoji_name, image=file.read())
                    print(f"Created emoji: {emoji_name}")

        # Set logging channel
        self.logging_channel = await self.fetch_channel(int(getenv("DISCORD_LOGGING_CHANNEL_ID")))
        print(f"Set logging channel: {self.logging_channel}")

        # Load each cog from the COGS list
        for cog in COGS:
            await self.load_extension(cog)
            print(f"Loaded cog: {cog}")

        # Sync slash commands globally
        await self.tree.sync()
        print("Slash commands synced")


    async def on_ready(self):
        """
        Indicate that the bot is ready.
        :return: None
        """

        print(f"Logged in: {self.user}")


async def main():
    """
    Main function to create an instance of the bot and start it using the token from environment variables
    :return: None
    """

    bot = AISpongeLite()
    async with bot:
        await bot.start(getenv("DISCORD_BOT_TOKEN"))


# Run the bot
if __name__ == "__main__":
    run(main())