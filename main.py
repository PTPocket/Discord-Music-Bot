import discord, asyncio
from discord.ext import commands
from config import TEST_TOKEN, TOKEN
from datetime import datetime
#Cog import
from cog.cog import music_cog

#Discord Bot Setup
intents = discord.Intents.default()
intents.message_content = True

client = commands.Bot(command_prefix="master pocket bot ", intents = intents)
def print_log(text):
    time= str(datetime.now())
    msg = f"{time} | Master Pocket Bot - {text}"
    print(msg)

@client.event
async def on_ready():
    print_log(f"DISCORD CONNECTED -> {client.user}")
    client.description("hello")


    
async def main():
    async with client:
        try:
            await client.add_cog(music_cog(client))

            print_log("LOADED -> music cog")

            await client.start(TOKEN)
        except Exception as e:
            print_log(e)
            print_log("ERROR -> starting bot")

asyncio.run(main())