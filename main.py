"""
AI Sponge Lite is a Discord bot that generates parody AI Sponge audio episodes, chats, and TTS inspired by
[AI Sponge Rehydrated](https://aisponge.riskivr.com/).

Written by Jeremy Noesen
"""

from os import getenv
from discord import Intents
from discord.app_commands import AppInstallationType, AppCommandContext
from dotenv import load_dotenv
from discord.ext.commands import Bot
from asyncio import run

# Load environment variables from .env file
load_dotenv()

# List of cogs to load
COGS = [
    "cogs.patrons",
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

        super().__init__(command_prefix="/", intents=Intents.default(), allowed_installs=AppInstallationType(guild=True, user=False), allowed_contexts=AppCommandContext(guild=True, dm_channel=False, private_channel=True))

        # Initialize an empty list to store Discord user IDs of Patreon subscribers, which will be accessed throughout the bot
        self.subscribed_discord_user_ids = []


    async def setup_hook(self):
        """
        Load cogs and sync slash commands globally
        :return: None
        """

        # Load each cog from the COGS list
        for cog in COGS:
            await self.load_extension(cog)
            print(f"Loaded cog: {cog}")

        # Sync slash commands globally
        await self.tree.sync()
        print("Slash commands synced globally")


    async def on_ready(self):
        """
        Show when the bot has finished loading and is ready to use
        :return: None
        """

        print(f"Logged in as {self.user} (ID: {self.user.id})")


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