import discord, asyncio
from discord.ext import commands
from discord.ui           import View, Select, Button
#Cog import
from cog.MusicCog          import MusicCog
#Extra Functions
from cog.helper.GuildData import Guild_Music_Properties
from cog.helper.Log       import *
import cog.helper.Setting as      Setting
#SECRET KEYS
from dotenv import load_dotenv



def configure():
    load_dotenv()
    log(None, 'Loaded', 'api keys')


if __name__ == '__main__':
    #Discord Bot Setup##################################################
    intents = discord.Intents.default()
    intents.message_content = True
    client = commands.Bot(command_prefix=['/'], intents = intents)
    Setting.initialize_settings()
    data = Guild_Music_Properties()
    gui_print = set()
    @client.event
    async def on_ready():
        try:
            activity = discord.CustomActivity('Music Bot')
            await client.change_presence(activity=activity)
            log(None, client.user, 'Connected to Discord')
        except Exception as e:
            print(e)
    async def main():
        configure()
        bot_api_key = os.getenv('TEST_TOKEN')
        spotify_client_id = os.getenv('SPOTIFY_CLIENT_ID')
        spotify_client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
        
        async with client:
            try:
                await client.add_cog(MusicCog(client, data, gui_print, spotify_client_id, spotify_client_secret))
                await client.start(bot_api_key)
            except Exception as e:
                print(e)
    asyncio.run(main())