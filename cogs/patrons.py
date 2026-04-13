"""
Module to fetch Patreon subscribers, used to determine command permissions.

Written by Jeremy Noesen
"""

from os import getenv
from patreon import API
from discord.ext.tasks import loop
from discord.ext.commands import Cog


class Patrons(Cog):
    """
    Cog for fetching Patreon subscribers.
    """


    def __init__(self, bot):
        """
        Initialize the cog
        :param bot: The bot instance
        """

        self.bot = bot
        self.fetch_patrons.start()


    @loop(minutes=5)
    async def fetch_patrons(self):
        """
        Fetch active Patreon subscriber Discord user IDs, storing them in a global set.
        :return: None
        """

        # Create a set to store updated set of Discord user IDs
        fetched_discord_user_ids = {int(x) for x in getenv("DISCORD_ADMIN_USER_IDS").split(",")}

        # Log in to Patreon API
        api_client = API(getenv("PATREON_ACCESS_TOKEN"))

        # Loop through paginated responses to fetch all members of the Patreon campaign
        cursor = None
        while True:

            # Fetch a page of members, including their social connections and patron status
            members_response = api_client.get_campaigns_by_id_members(getenv("PATREON_CAMPAIGN_ID"), 1000, cursor=cursor, includes=["user"], fields={"member": ["patron_status"], "user": ["social_connections"]})

            # Iterate through the members in the response
            for member in members_response.data():

                # Check if the member is an active patron and has a linked Discord account, then add their Discord user ID to the set
                discord_id = member.relationship('user').attribute('social_connections').get('discord')
                if member.attribute('patron_status') == 'active_patron' and discord_id is not None:
                    fetched_discord_user_ids.add(int(discord_id.get("user_id")))

            # Check if there is a next page of results
            try:
                cursor = api_client.extract_cursor(members_response)
            except Exception:
                break

        # Update the global set of Discord user IDs with the new set
        self.bot.subscribed_discord_user_ids = fetched_discord_user_ids


async def setup(bot):
    """
    Register the Patrons cog with the bot.
    :param bot: The bot instance
    :return: None
    """

    # Register cog
    await bot.add_cog(Patrons(bot))