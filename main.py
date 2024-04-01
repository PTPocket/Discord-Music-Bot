import discord, asyncio
from discord.ext import commands
from config import TOKEN, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET
from datetime import datetime
#Cog import
from cog.cog import Music_Cog, log

#Discord Bot Setup
intents = discord.Intents.default()
intents.message_content = True

client = commands.Bot(command_prefix="pocket music ", intents = intents)


@client.event
async def on_ready():
    log(None, client.user, 'Connected to Discord')

async def main():
    async with client:
        try:
            await client.add_cog(Music_Cog(client, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET))
            await client.start(TOKEN)
            print('READY')
        except Exception as e:
            print(e)

asyncio.run(main())