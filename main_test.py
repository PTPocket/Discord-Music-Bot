import discord, asyncio
from discord.ext import commands

#Cog import
from cog.cog import Music_Cog
from cog.helper.functions import log

#SECRET KEYS
from config import TEST_TOKEN, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET


if __name__ == '__main__':
    #Discord Bot Setup##################################################
    intents = discord.Intents.default()
    intents.message_content = True
    client = commands.Bot(command_prefix=['/','!', '?'], intents = intents)

    @client.event
    async def on_ready():
        log(None, client.user, 'Connected to Discord')

    async def main():
        async with client:
            try:
                await client.add_cog(Music_Cog(client, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET))
                await client.start(TEST_TOKEN)
            except Exception as e:
                print(e)

    asyncio.run(main())