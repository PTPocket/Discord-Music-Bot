import discord, asyncio
from discord.ext import commands
#Cog import
from cog.MusicCog          import MusicCog
#Extra Functions
from cog.helper.GuildData import Guild_Music_Properties
from cog.helper.Log        import *
import cog.helper.Setting  as     Setting
#SECRET KEYS
from config import TOKEN, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET


if __name__ == '__main__':
    #Discord Bot Setup##################################################
    intents = discord.Intents.default()
    intents.message_content = True
    client = commands.Bot(command_prefix=['/','!', '?'], intents = intents)
    Setting.initialize_settings()
    data = Guild_Music_Properties()
    gui_print = set()
    @client.event
    async def on_ready():
        log(None, client.user, 'Connected to Discord')

    async def main():
        async with client:
            try:
                await client.add_cog(MusicCog(client, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, data, gui_print))
                await client.start(TOKEN)
            except Exception as e:
                print(e)

    asyncio.run(main())