import discord, asyncio, os
from discord.ext    import commands
#Cog import
from cog.music_cog  import MusicCog
from cog.ClaudeCog  import ClaudeCog
from cog.GPTCog     import GPTCog
#Extra Functions
from cog.helper.log import *
import cog.helper.setting  as     Setting
#SECRET KEYS
from dotenv import load_dotenv



def configure():
    load_dotenv()
    log(None, 'Loaded', 'api keys')

if __name__ == '__main__':
    #Discord Bot Setup##################################################
    intents = discord.Intents.default()
    intents.message_content = True
    client = commands.Bot(command_prefix=['//'], intents = intents)
    Setting.initialize_settings()
    initialize_Log()
    @client.event
    async def on_ready():
        activity = discord.CustomActivity('The Music Bot')
        await client.change_presence(activity=activity)
        log(None, str(client.user), 'Connected to Discord')

    async def main():
        configure()
        bot_api_key = str(os.getenv('TOKEN'))
        async with client:
            try:
                await client.add_cog(MusicCog(client))
                #await client.add_cog(ClaudeCog(client))
                await client.add_cog(GPTCog(client))
                await client.start(bot_api_key, reconnect=True)
            except Exception as e:
                print(e)

    asyncio.run(main())