import openai
import discord
from datetime import datetime
from discord.ext import commands, tasks

MODEL_GPT4O_MINI = 'gpt-4o-mini'
SYSTEM_CHARACTERISTICS = 'You are a helpful assistant named PocBot created by Pocket Man. You keep your responses as short. Do not add any unnecessary information.'
MAX_TOKENS = 1000
TEMPERATURE = 1

class ChannelInformation():
    def __init__(self):
        self.channels = {}
        self.prev_msg_timestamp = {}
        self.msg_history = {}
    
    def GetTimestamps(self):
        return self.prev_msg_timestamp.copy()
    
    def GetChannel(self, channel_id):
        return self.channels.get(channel_id)
    
    def GetMsgHistory(self, channel_id):
        return self.msg_history.get(channel_id)
    
    def SaveUserPrompt(self, channel:discord.channel.TextChannel, prompt:str):
        channel_id = channel.id
        if channel_id not in self.msg_history.keys():
            self.msg_history[channel_id] = []
        self.channels[channel_id] = channel
        self.msg_history[channel_id].append({"role": "user", "content": prompt})
        self.prev_msg_timestamp[channel_id] = datetime.now()
        return
    
    def SaveAssistantPrompt(self, channel:discord.channel.TextChannel, prompt:str):
        channel_id = channel.id
        self.msg_history[channel_id].append({"role": "assistant", "content": prompt})
        
    def RemoveChannel(self, channel_id):
        self.channels.pop(channel_id)
        self.prev_msg_timestamp.pop(channel_id)
        self.msg_history.pop(channel_id)

class GPTCog(commands.Cog):
    def __init__(self, bot:commands.Bot, openai_api_key:str):
        self.bot = bot
        openai.api_key = openai_api_key
        self.channel_info = ChannelInformation()
        self.PurgeChannels.start()
    
    @commands.Cog.listener() 
    async def on_message(self, message:discord.message.Message):
        try:
            if self.bot.user.id == message.author.id:
                return
            if type(message.channel) == discord.channel.DMChannel:
                response = await self.GPTResponse(message.channel, message.content)
                await message.channel.send(response)
            elif message.channel.name == 'pocbot-ama':
                response = await self.GPTResponse(message.channel, message.content)
                await message.channel.send(response)
            return
        except Exception as e:
            print(e)
    
    async def GPTResponse(self,  channel:discord.channel.TextChannel, prompt:str):
        self.channel_info.SaveUserPrompt(channel, prompt)
        print(self.channel_info.GetMsgHistory(channel.id))
        # Modify the API call to use OpenAI's chat completions
        response = openai.chat.completions.create(
            model=MODEL_GPT4O_MINI,
            messages= [{"role": "system", "content" : SYSTEM_CHARACTERISTICS}] + self.channel_info.GetMsgHistory(channel.id),
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE
        )
        
        gpt_output = response.choices[0].message.content
        self.channel_info.SaveAssistantPrompt(channel, gpt_output)
        return gpt_output
    
    @tasks.loop(seconds=180)
    async def PurgeChannels(self):
        timestamps = self.channel_info.GetTimestamps()
        curr_time = datetime.today()
        to_delete = []
        for channel_id in timestamps:
            prev_time = timestamps.get(channel_id)
            diff_time = (curr_time-prev_time).seconds
            if diff_time > 180:
                to_delete.append(channel_id)
                channel = self.channel_info.GetChannel(channel_id)
                self.channel_info.RemoveChannel(channel_id)
                if type(channel) != discord.channel.DMChannel:
                    await channel.purge()
                    await channel.send("Hi! Ask me anything.")