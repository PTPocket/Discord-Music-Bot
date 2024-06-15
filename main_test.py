import discord, asyncio
from discord.ext import commands
#Cog import
from cog.MusicCog          import MusicCog
#Extra Functions
from cog.helper.GuildData import Guild_Music_Properties
from cog.helper.Log        import *
import cog.helper.Setting  as     Setting
import cog.helper.InvalidUrlFile as InvalidUrl
#SECRET KEYS
from dotenv import load_dotenv
#spotify api
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy


def configure():
    load_dotenv()
    log(None, 'Loaded', 'api keys')

if __name__ == '__main__':
    #Discord Bot Setup##################################################
    intents = discord.Intents.default()
    intents.message_content = True
    client = commands.Bot(command_prefix=['//'], intents = intents)
    Setting.initialize_settings()
    InvalidUrl.initialize()
    data = Guild_Music_Properties()
    gui_print = set()
    @client.event
    async def on_ready():
        activity = discord.CustomActivity('The Music Bot')
        await client.change_presence(activity=activity)
        log(None, client.user, 'Connected to Discord')

    async def main():
        configure()
        bot_api_key = os.getenv('TEST_TOKEN')
        spotify_client_id = os.getenv('SPOTIFY_CLIENT_ID')
        spotify_client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
        client_credentials_manager = SpotifyClientCredentials(client_id=spotify_client_id, client_secret=spotify_client_secret)
        spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

        async with client:
            try:
                await client.add_cog(MusicCog(client, data, gui_print, spotify))
                await client.start(bot_api_key, reconnect=True)
            except Exception as e:
                print(e)

    asyncio.run(main())