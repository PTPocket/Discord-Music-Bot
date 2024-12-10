import anthropic
import discord
from datetime import datetime
from discord.ext import commands, tasks


MODEL_SONNET = 'claude-3-5-sonnet-20241022'
MODEL_OPUS   = 'claude-3-opus-20240229	'
MODEL_HAIKU = 'claude-3-5-haiku-20241022'
SYSTEM_CHARACTERISTICS = 'You are a helpful assistant named PocBot created by Pocket Man. You keep your responses as short.'
MAX_TOKENS = 1000
TEMPERATURE = 1

class ClaudeCog(commands.Cog):
    def __init__(self, bot:commands.Bot):
        self.bot = bot
        self.client = anthropic.Anthropic()

        self.last_message_time = {}
        self.user_message_history = {}

            
    @commands.Cog.listener() 
    async def on_message(self, message:discord.message.Message):
        user_id = message.author.id
        if self.bot.user.id == user_id:
            return
        if type(message.channel) == discord.channel.DMChannel:
            response = await self.ClaudeResponse(user_id, message.content)
            await message.channel.send(response)
        elif message.channel.name == 'pocbot-ama':
            response = await self.ClaudeResponse(user_id, message.content)
            await message.channel.send(response)
        return


    async def ClaudeResponse(self, user_id, prompt):
        self.CheckTime(user_id)
        self.RecordMessage(user_id, prompt)
        output = self.client.messages.create(
            model       = MODEL_HAIKU,
            system      = SYSTEM_CHARACTERISTICS,
            max_tokens  = MAX_TOKENS,
            temperature = TEMPERATURE,
            messages    = self.user_message_history[user_id]
        )
        claude_output = output.content[0].text

        self.RecordMessage(user_id, claude_output, assistant=True)
        return claude_output
    
    def RecordMessage(self, user_id, prompt, assistant = False):
        if user_id not in self.user_message_history.keys():
            self.user_message_history[user_id] = []
        if assistant is False:
            self.user_message_history[user_id].append({"role": "user", "content": prompt})
            self.last_message_time[user_id] = datetime.today()
        else:
            self.user_message_history[user_id].append({"role": "assistant", "content": prompt})  

    def CheckTime(self, user_id):
        if user_id not in self.last_message_time:
            return
        prev_time = self.last_message_time[user_id]
        curr_time = datetime.today()
        diff_time = curr_time-prev_time
        if diff_time.seconds > 180:
            self.last_message_time.pop(user_id)
            self.user_message_history.pop(user_id)
        