"""
AI Sponge Lite is a Discord bot that generates parody AI Sponge audio episodes, chats, and TTS inspired by
[AI Sponge Rehydrated](https://aisponge.riskivr.com/).

Written by Jeremy Noesen
"""

from logging import getLogger
from os import getenv, listdir
from discord import Intents, Game, utils
from discord.app_commands import AppInstallationType, AppCommandContext
from dotenv import load_dotenv
from discord.ext.commands import Bot

# Set up logger
utils.setup_logging()
logger = getLogger(__name__)

# Load environment variables from .env file
load_dotenv(override=True)

# List of cogs to load
cogs = [
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

        super().__init__(command_prefix="/", intents=Intents.default(), allowed_installs=AppInstallationType(guild=True, user=False), allowed_contexts=AppCommandContext(guild=True, dm_channel=False, private_channel=True), activity=Game("4.1.3"))

        # Initialize variables used throughout the bot
        self.permitted_discord_user_ids = {int(x) for x in str(getenv("DISCORD_ADMIN_USER_IDS")).split(",")}
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
                logger.info("Uploaded avatar")

        # Set bot banner if it is missing
        if (await self.fetch_user(self.user.id)).banner is None:
            with open("image/profile/banner.png", "rb") as file:
                await self.user.edit(banner=file.read())
                logger.info("Uploaded banner")

        # Fetch all application emojis
        self.fetched_emojis = {e.name: e for e in await self.fetch_application_emojis()}
        logger.info(f"Fetched emojis: {set(self.fetched_emojis.keys())}")

        # Create missing application emojis
        for emoji_file in listdir("image/emoji"):
            emoji_name = emoji_file.split(".")[0]
            if emoji_name not in self.fetched_emojis.keys():
                with open(f"image/emoji/{emoji_file}", "rb") as file:
                    self.fetched_emojis[emoji_name] = await self.create_application_emoji(name=emoji_name, image=file.read())
                    logger.info(f"Created emoji: {emoji_name}")

        # Set logging channel
        self.logging_channel = await self.fetch_channel(int(str(getenv("DISCORD_LOGGING_CHANNEL_ID"))))
        logger.info(f"Set logging channel: {self.logging_channel}")

        # Load each cog from the COGS list
        for cog in cogs:
            await self.load_extension(cog)
            logger.info(f"Loaded cog: {cog}")

        # Sync slash commands globally
        await self.tree.sync()
        logger.info("Slash commands synced")


    async def on_ready(self):
        """
        Indicate that the bot is ready.
        :return: None
        """

        logger.info(f"Logged in: {self.user}")


# Run the bot
if __name__ == "__main__":
    AISpongeLite().run(str(getenv("DISCORD_BOT_TOKEN")), log_handler=None)