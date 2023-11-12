import discord, asyncio
from discord.ext import commands
from config import TOKEN
from datetime import datetime
#Cog import
from cog.cog import Music_Cog, send_log

#Discord Bot Setup
intents = discord.Intents.default()
intents.message_content = True

client = commands.Bot(command_prefix="master pocket bot ", intents = intents)


@client.event
async def on_ready():
    send_log(None, client.user, 'Connected to Discord')

async def main():
    async with client:
        try:
            await client.add_cog(Music_Cog(client))
            await client.start(TOKEN)
            print('READY')
        except Exception as e:
            print(e)

asyncio.run(main())