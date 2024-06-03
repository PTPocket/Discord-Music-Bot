import discord
import cog.helper.Setting   as     Setting
from datetime               import datetime
from discord.ext            import commands, tasks
from datetime               import datetime
from cog.helper.Functions   import *
from cog.helper.MusicSearch import *
from cog.helper.Log     import *


SHORT_COMMANDS = ['p', 'h', 's', 'r', 'prev', 'previous']
PREFIXS = ['!','/', '?']

class ExtraCogFunctions(commands.Cog):
    def __init__(self, bot:commands.Bot, client_id, client_secret, data, gui_print):
        self.bot = bot
        self.client_id = client_id
        self.client_secret = client_secret
        self.data = data
        self.gui_print = gui_print
        self.gui_loop.start()
        self.disconnect_check.start()

############# LISTENERS ########################################################################
    # Keep music player at bottom of channel
    @commands.Cog.listener() 
    async def on_message(self, message):
        guildName = message.guild.name
        guildID = message.guild.id
        command = str(message.content).split(' ')[0]
        prefix = command[:1]
        com = command[1:].lower()
        if message.author.id != self.bot.user.id \
            and message.channel.id == self.data.get_message(guildID).channel.id\
            and prefix not in PREFIXS\
            and com not in SHORT_COMMANDS:
            await GUI_HANDLER(self, guildID, edit=False)

    # RESET BOT FOR GUILD IF DISCONNECTED FROM VOICE CHANNEL
    @commands.Cog.listener()
    async def on_voice_state_update(self, member:discord.member.Member, before, after):
        if after.channel is not None:return
        users = self.bot.get_channel(before.channel.id).members
        if users == []: return
        guildName = member.guild.name
        guildID= member.guild.id
        connected_user_ids = [user.id for user in users]

        #Disconnects if bot is only one is channel
        if (len(connected_user_ids) == 1 and self.bot.user.id in connected_user_ids) or \
           (len(connected_user_ids) == 2 and self.bot.user.id in connected_user_ids and 990490227401453618 in connected_user_ids):
            voice_client = self.bot.get_guild(guildID).voice_client
            self.data.reset(guildID)
            if voice_client is not None:
                if voice_client.is_playing() or voice_client.is_paused():
                    self.gui_print.add(guildID)
                    voice_client.stop()
                await voice_client.disconnect()
            log(guildName, 'disconnected (empty)', before.channel.name)
            await GUI_HANDLER(self, guildID)
            return

######## LOOP TO AUTO CHANGE GUI ##############################################################
    @tasks.loop(seconds = 5)
    async def gui_loop(self):
        while self.gui_print:
            guildID = self.gui_print.pop()
            await GUI_HANDLER(self, guildID)

####### Auto Disconnect Bot After X Seconds idle
    @tasks.loop(minutes=3)
    async def disconnect_check(self):
        all_voice_connections = self.bot.voice_clients
        for voice in all_voice_connections:    
            guildID = voice.guild.id
            last_idle = self.data.get_time(guildID)
            if last_idle is None or voice.is_playing():
                self.data.set_idle_timestamp(guildID)
                continue
            time_passed = (datetime.today()-last_idle).seconds
            timeout = Setting.get_timeout()
            if  time_passed > timeout:
                self.data.full_reset(guildID)
                channelName = voice.channel.name
                await voice.disconnect()
                await GUI_HANDLER(self, guildID)
                log(voice.guild.name, 'disconnected (timeout)', channelName)
