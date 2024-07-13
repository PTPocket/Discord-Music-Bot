import discord
import time
import random
import asyncio

from discord                import app_commands, FFmpegPCMAudio
from discord.ext            import commands, tasks
from cog.helper.Embed       import Embeds
from cog.helper.PrintHandler import PrintHandler
from cog.helper.GuildData   import GuildData
import cog.helper.Setting   as     Setting
from cog.helper.Log         import *
from cog.helper.Functions   import *
from cog.helper.SearchMusic import MusicOrb
from GlobVar                import FFMPEG_EXE_PATH


FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

def timeIt(start):
    print(time.perf_counter()-start)

class MusicCog(commands.Cog):
    def __init__(self, bot:commands.Bot):
        self.funcList = {
            'p'         : self.play,
            'play'      : self.play,
            's'         : self.skip,
            'skip'      : self.skip,
            'n'         : self.skip,
            'next'      : self.skip,
            'prev'      : self.previous,
            'previous'  : self.previous,
            'playrandom': self.playrandom,
            'pr'        : self.playrandom,
            'shuffle'   : self.shuffle, 
            'sh'        : self.shuffle, 
            'pause'     : self.pause,
            'pa'        : self.pause,
            'r'         : self.resume,
            'resume'    : self.resume,
            'loop'      : self.loop,
            'l'         : self.loop,
            'flush'     : self.flush,
            'f'         : self.flush,
            'join'      : self.join,
            'j'         : self.join,
            'h'         : self.help,
            'help'      : self.help,
            'reset'     : self.reset,
            'generate'  : self.generate,
            'switch_algorithm' : self.switch_algorithm,
            'prefix'    : self.prefix,
            'slashcommand' : self.slashcommand}
        self.bot = bot
        self.dataObj = GuildData()
        self.embObj = Embeds(self.bot, self.dataObj)
        self.pHandler = PrintHandler(self, self.bot, self.dataObj, self.embObj)
        self.music = MusicOrb(self.bot, self.dataObj, self.embObj)
        self.gui_print = set()
        self.gui_loop.start()
        self.disconnect_check.start()

    #MUSIC PLAYER LOOP (not recursive)
    def music_player(self, guildName, guildID, voice_client, recall = False, last_pos = None):
        try:
            pos = self.dataObj.get_pos(guildID)
            if last_pos == pos or pos is None:
                self.dataObj.pos_forward(guildID)
            # else:
            #     pos = last_pos
            #     while pos != self.dataObj.get_pos(guildID):
            #         pos = self.dataObj.get_pos(guildID)
            #         time.sleep(1.5)
            if self.dataObj.get_loop(guildID) is True:
                self.dataObj.pos_backward(guildID)
            if self.dataObj.empty_queue(guildID) and self.dataObj.get_random(guildID) is True:
                song = self.music.GetRandom()#Get Random may give errors causing problems to musc player
                self.dataObj.add_song(guildID, song)
            if self.dataObj.empty_queue(guildID):
                self.dataObj.set_playing(guildID, False)
                self.dataObj.set_idle_timestamp(guildID)
                self.gui_print.add(str(guildID))
                log(guildName, 'music player', 'finished')
                return
            
            #Moves song from queue to current
            song = self.dataObj.get_current(guildID)
            if song['source'] in ['query', 'spotify']:
                query = song['query']
                song = self.music.SearchYoutube(query)
                player = FFmpegPCMAudio(
                    song['query'],
                    **FFMPEG_OPTIONS,
                    executable= FFMPEG_EXE_PATH)
            elif song['source'] == 'searched':
                song['source'] = 'query'
                
                player = FFmpegPCMAudio(
                    song['query'],
                    **FFMPEG_OPTIONS,
                    executable= FFMPEG_EXE_PATH)
                song['query'] = song['url']
                self.dataObj.set_current(guildID, song)
            elif song['source'] == 'spotify':
                song = self.music.GetSpotify(song['url'])
                self.dataObj.set_current(guildID, song)
                song = self.music.SearchYoutube(song['query'])
                player = FFmpegPCMAudio(
                    song['query'],
                    **FFMPEG_OPTIONS,
                    executable= FFMPEG_EXE_PATH)
            else: #LOCAL SONG
                player = FFmpegPCMAudio(
                    song['query'],
                    executable=FFMPEG_EXE_PATH)
            #Queues New Print Statement for GUI
            #Put here cause it will change entered query title to the video title in GUI
            if recall is True:
                self.gui_print.add(guildID)
            player = discord.PCMVolumeTransformer(player, volume=0.16)
            self.dataObj.set_idle_timestamp(guildID)
            log(guildName, "now playing", song)
            pos = self.dataObj.get_pos(guildID)
            voice_client.play(player, after= lambda x=None: self.music_player(guildName, guildID, voice_client, recall=True, last_pos = pos))
            return False
        except Exception as e:
            error_log('music_player', e, guildName=guildName)
            log('music_player', 'restarting')
            self.music_player(guildName, guildID, voice_client, recall=True, last_pos = pos)
            return True
    #CHECKS IF MUSIC_PLAYER LOOP SHOULD START
    async def music_player_start(self, user, guildName, guildID, voice_client):
        async with self.dataObj.get_musicplayerLock(guildID): 
            try:
                voice_client = self.bot.get_guild(guildID).voice_client
                voice_client = await voice_connect(user, voice_client)
                if voice_client.is_playing() == voice_client.is_paused() == self.dataObj.get_playing(guildID) == False:
                    self.dataObj.set_playing(guildID, True)
                    await self.pHandler.nowPlayingHandler(guildID)                
                    log(guildName, 'MUSIC PLAYER', 'starting')
                    self.music_player(guildName, guildID, voice_client)
            except Exception as e:
                error_log('music_player_start', e, guildName=guildName)

####### MAIN FUNCTIONS ######################################################

    async def play(self, message, query):
        if type(message) == discord.Interaction:
            user = message.user
        else: user = message.author
        user = user
        guildName = message.guild.name
        guildID   = message.guild.id
        channel = message.channel
        voice_client = self.bot.get_guild(guildID).voice_client
        log(guildName, 'command', 'play')
        try:
            if await self.validate_play_commands(user, channel, voice_client) is False:return
            if query == '' or query.count(' ') == len(query):
                msg = self.embObj.no_query_prompt()
                await channel.send(embed = msg, delete_after=Setting.get_promptDelay())
                await self.pHandler.GUI_HANDLER(channel)
                return
            result = await self.music.Search(channel, query)
            if result is not False:
                await self.music_player_start(user, guildName, guildID, voice_client)
            await self.pHandler.GUI_HANDLER(channel)
            return
        except Exception as e:
            error_log('play', e, guildName=guildName)

    async def playrandom(self, message):
        
        if type(message) == discord.Interaction:
            user = message.user
        else: user = message.author
        user = user
        guildName = message.guild.name
        guildID   = message.guild.id
        channel = message.channel
        voice_client = self.bot.get_guild(guildID).voice_client
        log(guildName, 'command', 'play_random')
        try:
            if await self.validate_play_commands(user, channel, voice_client) is False:return
            if self.dataObj.switch_random(guildID) is True:
                log(guildName, 'RANDOM', 'On')
            else: 
                log(guildName, 'RANDOM', 'Off')
            await channel.send(embed = self.embObj.random_prompt(self.dataObj.get_random(guildID)), delete_after=Setting.get_promptDelay())
            await self.music_player_start(user, guildName, guildID, voice_client)
            await self.pHandler.GUI_HANDLER(channel)
        except Exception as e:
            error_log('play_random', e, guildName=guildName)
    
    async def shuffle(self, message):
        if type(message) == discord.Interaction:
            user = message.user
        else: user = message.author
        user = user
        guildName = message.guild.name
        guildID   = message.guild.id
        channel = message.channel
        voice_client = self.bot.get_guild(guildID).voice_client
        log(guildName, 'command', 'shuffle')
        try:
            if await self.validate_command(user, channel, voice_client) is False : return
            song = self.dataObj.get_current(guildID)
            library = self.dataObj.get_queue(guildID)+self.dataObj.get_history(guildID)
            if library == [] and song is None:
                await channel.send(embed= self.embObj.no_songs_prompt(), delete_after=Setting.get_promptDelay())
                await self.pHandler.GUI_HANDLER(channel)
                return
            random.shuffle(library)
            if song is not None:
                library.insert(0, song)
            self.dataObj.set_new_library(guildID, library)
            if self.dataObj.get_playing(guildID) is True:
                await channel.send(embed= self.embObj.shuffle_prompt(), delete_after=Setting.get_promptDelay())
                await self.pHandler.GUI_HANDLER(channel)
                return
            await channel.send(embed= self.embObj.shuffle_prompt(), delete_after=Setting.get_promptDelay())
            await self.music_player_start(user, guildName, guildID, voice_client)
            
            await self.pHandler.GUI_HANDLER(channel)
        except Exception as e:
            error_log('shuffle', e)
    
    async def skip(self, message):
        if type(message) == discord.Interaction:
            user = message.user
        else: user = message.author
        user = user
        guildName = message.guild.name
        guildID   = message.guild.id
        channel = message.channel
        voice_client = self.bot.get_guild(guildID).voice_client
        log(guildName, 'command', 'skip')
        try:
            if await self.validate_command(user, channel, voice_client) is False:return
            song= self.dataObj.get_current(guildID)
            self.dataObj.pos_forward(guildID)
            if song is None:
                await channel.send(embed= self.embObj.no_songs_prompt(), delete_after=Setting.get_promptDelay())
                await self.pHandler.GUI_HANDLER(channel)
                return
            if (voice_client.is_playing() or voice_client.is_paused()):
                self.dataObj.set_loop(guildID, False)
                voice_client.stop()
                await channel.send(embed= self.embObj.skip_prompt(song), delete_after=Setting.get_promptDelay())
                await self.pHandler.GUI_HANDLER(channel)
                return
            await channel.send(embed= self.embObj.skip_prompt(song), delete_after=Setting.get_promptDelay())
            await self.pHandler.GUI_HANDLER(channel)
        except Exception as e:
            error_log('skip', e)

    async def previous(self, message):
        if type(message) == discord.Interaction:
            user = message.user
        else: user = message.author
        user = user
        guildName = message.guild.name
        guildID   = message.guild.id
        channel = message.channel
        voice_client = self.bot.get_guild(guildID).voice_client
        log(guildName, 'command', 'previous')
        try:
            if await self.validate_command(user, channel, voice_client) is False:return
            self.dataObj.pos_backward(guildID)
            song= self.dataObj.get_current(guildID) 
            if song is None:
                await channel.send(embed= self.embObj.no_songs_prompt(), delete_after=Setting.get_promptDelay())
                await self.pHandler.GUI_HANDLER(channel)
                return
            self.dataObj.set_loop(guildID, False)
            if voice_client.is_playing() or voice_client.is_paused():
                voice_client.stop()
                await channel.send(embed= self.embObj.previous_prompt(song), delete_after=Setting.get_promptDelay())
                await self.pHandler.GUI_HANDLER(channel)
                return
            await channel.send(embed= self.embObj.previous_prompt(song), delete_after=Setting.get_promptDelay())
            await self.pHandler.GUI_HANDLER(channel)
            await self.music_player_start(user, guildName, guildID, voice_client)
        except Exception as e:
            error_log('previous_ctx', e, guildName= guildName)
    
    async def pause(self, message):
        if type(message) == discord.Interaction:
            user = message.user
        else: user = message.author
        user = user
        guildName = message.guild.name
        guildID   = message.guild.id
        channel = message.channel
        voice_client = self.bot.get_guild(guildID).voice_client
        log(guildName, 'command', 'pause')
        try:
            if await self.validate_command(user, channel, voice_client) is False:return
            song = self.dataObj.get_current(guildID)
            if voice_client.is_playing() and not voice_client.is_paused():
                log(guildName, 'PAUSED', song)
                voice_client.pause()
                await channel.send(embed= self.embObj.pause_prompt(song), delete_after=Setting.get_promptDelay())
                await self.pHandler.GUI_HANDLER(channel)
                return
            if not voice_client.is_playing() and voice_client.is_paused():
                await channel.send(embed= self.embObj.already_paused_prompt(song), delete_after=Setting.get_promptDelay())
                await self.pHandler.GUI_HANDLER(channel)
                return
            await channel.send(embed= self.embObj.no_songs_prompt(), delete_after=Setting.get_promptDelay())
            await self.pHandler.GUI_HANDLER(channel)
        except Exception as e:
            error_log('pause', e, guildName=guildName)
            
    async def resume(self, message):
        if type(message) == discord.Interaction:
            user = message.user
        else: user = message.author
        user = user
        guildName = message.guild.name
        guildID   = message.guild.id
        channel = message.channel
        voice_client = self.bot.get_guild(guildID).voice_client
        log(guildName, 'command', 'pause')
        try:
            if await self.validate_command(user, channel, voice_client) is False:return
            song = self.dataObj.get_current(guildID)
            if not voice_client.is_playing() and voice_client.is_paused():
                log(guildName, 'resume', song)
                voice_client.resume()
                await channel.send(embed= self.embObj.resume_prompt(song), delete_after=Setting.get_promptDelay())
                await self.pHandler.GUI_HANDLER(channel)
                return
            if voice_client.is_playing() and not voice_client.is_paused():
                await channel.send(embed= self.embObj.already_playing_prompt(song), delete_after=Setting.get_promptDelay())
                await self.pHandler.GUI_HANDLER(channel)
                return
            await channel.send(embed= self.embObj.no_songs_prompt('Resume'), delete_after=Setting.get_promptDelay())
            await self.pHandler.GUI_HANDLER(channel)
        except Exception as e:
            error_log('resume', e, guildName= guildName)

    async def loop(self, message):
        if type(message) == discord.Interaction:
            user = message.user
        else: user = message.author
        user = user
        guildName = message.guild.name
        guildID   = message.guild.id
        channel = message.channel
        voice_client = self.bot.get_guild(guildID).voice_client
        log(guildName, 'command', 'loop')
        try:
            if await self.validate_command(user, channel, voice_client) is False:return
            if voice_client.is_playing() or voice_client.is_paused():
                song = self.dataObj.get_current(guildID)
                self.dataObj.switch_loop(guildID)
                self.dataObj.set_random(guildID, False)
                loop_var = self.dataObj.get_loop(guildID)
                if loop_var is True:
                    log(guildName, 'now looping', song)
                else:
                    log(guildName, 'stopped looping', song)
                loop_var = self.dataObj.get_loop(guildID)
                song= self.dataObj.get_current(guildID) 
                await channel.send(embed= self.embObj.loop_prompt(loop_var, song), delete_after=Setting.get_promptDelay())
                await self.pHandler.GUI_HANDLER(channel)
                return
            await channel.send(embed= self.embObj.no_songs_prompt('loop'), delete_after=Setting.get_promptDelay())
            await self.pHandler.GUI_HANDLER(channel)
        except Exception as e:
            error_log('loop', e, guildName= guildName)
    
    async def reset(self, message):
        if type(message) == discord.Interaction:
            user = message.user
        else: user = message.author
        user = user
        guildName = message.guild.name
        guildID   = message.guild.id
        channel = message.channel
        voice_client = self.bot.get_guild(guildID).voice_client
        log(guildName, 'command', 'reset')
        try:
            if await self.validate_play_commands(user, channel, voice_client) is False:
                return
            self.dataObj.full_reset(guildID)
            if voice_client is not None:
                channel_name = voice_client.channel.name
                if voice_client.is_playing() or voice_client.is_paused():
                    voice_client.stop()
                await voice_client.disconnect()
                log(guildName, 'DISCONNECTED (user reset)', channel_name)
            self.dataObj.full_reset(guildID)
            await channel.send(embed= self.embObj.reset_prompt(), delete_after=Setting.get_promptDelay())
            await self.pHandler.GUI_HANDLER(channel)
        except Exception as e:
            error_log('reset', e, guildName= guildName)

    async def flush(self, message):
        if type(message) == discord.Interaction:
            user = message.user
        else: user = message.author
        user = user
        guildName = message.guild.name
        guildID   = message.guild.id
        channel = message.channel
        voice_client = self.bot.get_guild(guildID).voice_client
        log(guildName, 'command', 'flush')
        try:
            if await self.validate_play_commands(user, channel, voice_client) is False:
                return
            self.dataObj.reset(guildID)
            if voice_client is not None:
                if voice_client.is_playing() or voice_client.is_paused():
                    voice_client.stop()
            self.dataObj.full_reset(guildID)
            msg = self.embObj.flush_prompt()
            await channel.send(embed=msg, delete_after=Setting.get_promptDelay())
            await self.pHandler.GUI_HANDLER(channel)
        except Exception as e:
            error_log('flush', e, guildName= guildName)

    async def help(self, message):
        if type(message) == discord.Interaction:
            user = message.user
        else: user = message.author
        user = user
        guildName = message.guild.name
        guildID   = message.guild.id
        channel = message.channel
        log(guildName, 'command', 'help')
        self.dataObj.initialize(guildID)
        try:
            await self.pHandler.printHelpPrompt(channel)
            await asyncio.sleep(Setting.get_promptDelay())
            await self.pHandler.GUI_HANDLER(channel)
        except Exception as e:
            error_log('help', e, guildName= guildName)

    async def generate(self, message):
        if type(message) == discord.Interaction:
            user = message.user
        else: user = message.author
        user = user
        guildName = message.guild.name
        guildID   = message.guild.id
        channel = message.channel
        log(guildName, 'command', 'generate')
        self.dataObj.initialize(guildID)
        try:
            new_channel = await create_bot_channel(message.guild)
            if new_channel is None: 
                await channel.send(embed=self.embObj.already_generated_prompt())
                return
            await self.pHandler.printHelpPrompt(new_channel, permanent = True)
            await self.pHandler.GUI_HANDLER(new_channel)
            await channel.send(embed=self.embObj.generated_prompt())
        except Exception as e:
            error_log('generate', e)
    
    async def join(self, message):
        if type(message) == discord.Interaction:
            user = message.user
        else: user = message.author
        user = user
        guildName = message.guild.name
        guildID   = message.guild.id
        channel = message.channel
        voice_client = self.bot.get_guild(guildID).voice_client
        log(guildName, 'command', 'join')
        try:
            if await self.validate_join_command(user, channel, voice_client) is False:return
            voice_client = await voice_connect(user, voice_client)
            await channel.send(embed= self.embObj.joined_prompt(voice_client.channel), delete_after=Setting.get_promptDelay())
        except Exception as e:
            error_log('join', e)

    async def switch_algorithm(self, message):
        if type(message) == discord.Interaction:
            user = message.user
        else: user = message.author
        user = user
        guildName = message.guild.name
        guildID   = message.guild.id
        channel = message.channel
        log(guildName, 'command', 'switch_algorithm')
        self.dataObj.initialize(guildID)
        try:
            view = SearchAlgorithmView(self, user)
            await channel.send(view=view, delete_after=Setting.get_promptDelay())
        except Exception as e:
            error_log('switch_algorithm', e)

    async def prefix(self, message, prefix:str):
        if type(message) == discord.Interaction:
            user = message.user
        else: user = message.author
        user = user
        guildName = message.guild.name
        guildID   = message.guild.id
        channel = message.channel
        log(guildName, 'command', 'prefix')
        self.dataObj.initialize(guildID)
        try:
            if prefix == ''or  ' ' in prefix:
                await channel.send(embed= self.embObj.blank_prefix_prompt(prefix), delete_after=Setting.get_promptDelay())
                return
            Setting.set_guildPrefix(guildID, prefix)
            log(guildName, 'changed prefix', prefix)
            await channel.send(embed= self.embObj.changed_prefix_prompt(prefix), delete_after=Setting.get_promptDelay())
        except Exception as e:
            error_log('prefix', e)

    async def slashcommand(self, message):
        return

######## LOOP TO AUTO CHANGE GUI ##############################################################
    @tasks.loop(seconds = 5)
    async def gui_loop(self):
        try:
            while self.gui_print:
                guildID = self.gui_print.pop()
                await self.pHandler.nowPlayingHandler(guildID)
                await self.pHandler.GUI_HANDLER(None, int(guildID))
        except Exception as e:
            error_log('gui_loop', e)

####### Auto Disconnect Bot After X Seconds idle
    @tasks.loop(minutes=5)
    async def disconnect_check(self):
        try:
            all_voice_connections = self.bot.voice_clients
            for voice in all_voice_connections:    
                if voice is None or not voice.is_connected():
                    continue
                guildID = voice.guild.id
                last_idle = self.dataObj.get_time(guildID)
                if last_idle is None or voice.is_playing():
                    self.dataObj.set_idle_timestamp(guildID)
                    continue
                time_passed = (datetime.today()-last_idle).seconds
                timeout = Setting.get_timeout()
                if  time_passed > timeout:
                    self.dataObj.full_reset(guildID)
                    channelName = voice.channel.name
                    await voice.disconnect()
                    log(voice.guild.name, 'disconnected (timeout)', channelName)
        except Exception as e:
            error_log('disconnect_check', e)


############# LISTENERS #######################################################################
    # Keep music player at bottom of channel and listens for commands
    # CHECKS TEXT COMMANDS AND CALLS IF VALID
    @commands.Cog.listener() 
    async def on_message(self, message:discord.message.Message):
        if message is None:
            return
        guildName = message.guild.name
        guildID = message.guild.id
        channel = message.channel
        user = message.author
        content = str(message.content)
        try:
            try:
                first_space = content.index(' ')
                command = content[:first_space]
                query = content[first_space+1:]
            except: 
                command = content
                query = ''
            self.dataObj.initialize(guildID)
            guildPrefix = Setting.get_guildPrefix(guildID).lower()
            prefix = str(command[:len(guildPrefix)]).lower()
            command = str(command[len(guildPrefix):]).lower()
            if message.author.id != self.bot.user.id \
                and message.channel.id == Setting.get_channelID(guildID)\
                and prefix not in guildPrefix\
                and command not in self.funcList:
                await message.delete()
                return
            if guildPrefix != prefix: return
            if command in self.funcList:
                if command in ['p','play','changeprefix']:
                    log(guildName, 'access','granted')
                    await self.funcList[command](message, query)
                else:
                    log(guildName, 'access','granted')
                    await self.funcList[command](message)
            if message.author.id != self.bot.user.id and message.channel.id == Setting.get_channelID(guildID):
                await message.delete()
        except Exception as e :
            error_log('on_message', e)
        
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
            self.dataObj.reset(guildID)
            if voice_client is not None:
                if voice_client.is_playing() or voice_client.is_paused():
                    voice_client.stop()
                await voice_client.disconnect()
            log(guildName, 'disconnected (empty)', before.channel.name)
            return

    @commands.Cog.listener()
    async def on_guild_join(self, guild:discord.guild.Guild):
        try:
            guildID = guild.id
            self.dataObj.initialize(guildID)
            new_channel = await create_bot_channel(guild)
            if new_channel is None: 
                return
            await self.pHandler.printHelpPrompt(new_channel, permanent=True)
            await self.pHandler.GUI_HANDLER(new_channel, guildID)
        except Exception as e:
            error_log('on_guild_join',e)


    @commands.command(name= "sync")
    async def sync(self,ctx):
        guildName = ctx.guild.name
        try:
            sync_num = await ctx.bot.tree.sync()
            log(guildName, 'synced commands', sync_num)
            await ctx.send(embed= self.embObj.synced_prompt())
        except Exception as e:
            print(e)



### VALIDATOR FUNCTIONS ################################
    async def validate_command(self, ctx:commands.context.Context):
        guildID = ctx.guild.id
        content = ctx.message.content
        guildPrefix = Setting.get_guildPrefix(guildID)
        prefix = content[:len(guildPrefix)]
        return prefix.lower() == guildPrefix.lower()

    # Allows if user is in the same channel as bot
    # or if user is in voice channel and bot is not
    async def validate_play_commands(self, user, channel, voice_client):
        guildName = channel.guild.name
        guildID   = channel.guild.id
        self.dataObj.initialize(guildID)
        if user.voice is None:
            authorized = False
            msg = self.embObj.user_disconnected_prompt()
        elif voice_client is None or not voice_client.is_connected():
            authorized = True
        elif user.voice.channel.id == voice_client.channel.id:
            authorized = True
        else:
            authorized = False
            msg = self.embObj.invalid_channel_prompt(voice_client.channel)
        if not authorized:
            log(guildName, 'ACCESS DENIED', user)
            await channel.send(embed= msg, delete_after=Setting.get_promptDelay())
        else:
            log(guildName, 'ACCESS GRANTED', user)
            self.dataObj.set_channel(guildID, channel)
        return authorized

    # Allows if user is in the same channel as bot
    async def validate_command(self, user, channel, voice_client):
        guildName = channel.guild.name
        guildID   = channel.guild.id
        self.dataObj.initialize(guildID)
        if user.voice is None:
            authorized = False
            msg = self.embObj.user_disconnected_prompt()
        elif voice_client is None:
            authorized = False
            msg = self.embObj.bot_disconnected_prompt()
        elif not voice_client.is_connected():
            authorized = False
            msg = self.embObj.bot_disconnected_prompt()
        elif voice_client.channel.id == user.voice.channel.id:
            authorized =  True
        else: 
            msg = self.embObj.invalid_channel_prompt(voice_client.channel)
            authorized =  False
        if authorized is False:
            log(guildName, 'ACCESS DENIED', user)
            await channel.send(embed= msg, delete_after=Setting.get_promptDelay())
        else: 
            log(guildName, 'ACCESS GRANTED', user) 
            self.dataObj.set_channel(guildID, channel)
        return authorized

    async def validate_join_command(self, user, channel, voice_client):
        guildName = channel.guild.name
        guildID   = channel.guild.id
        self.dataObj.initialize(guildID)
        if user.voice is None:
            authorized = False
            msg = self.embObj.user_disconnected_prompt()
        elif voice_client is None or not voice_client.is_connected():
            authorized = True
        elif user.voice.channel.id == voice_client.channel.id:
            authorized = False
            msg = self.embObj.already_joined_prompt(voice_client.channel)
        else:
            authorized = False
            msg = self.embObj.already_joined_prompt(voice_client.channel)
        if not authorized:
            log(guildName, 'ACCESS DENIED', user)
            await channel.send(embed= msg, delete_after=Setting.get_promptDelay())
        else:
            log(guildName, 'ACCESS GRANTED', user)
            self.dataObj.set_channel(guildID, channel)
        return authorized








####################### SLASH COMMANDS #####################################################################
    @app_commands.command(name= "play", description="Play a song or playlist with name or playlist url")
    async def play_slash(self, interaction:discord.Interaction, query:str):
        await interaction.response.defer()
        await self.play(interaction, query)
        await interaction.delete_original_response()

    @app_commands.command(name= "playrandom", description="Play random songs from pocket bot library forever")
    async def playrandom_slash(self, interaction:discord.Interaction): 
        await interaction.response.defer()
        await self.playrandom(interaction)
        await interaction.delete_original_response()

    @app_commands.command(name= "skip", description="Skips song")
    async def skip_slash(self, interaction:discord.Interaction):
        await interaction.response.defer()
        await self.skip(interaction)
        await interaction.delete_original_response()

    @app_commands.command(name= "next", description="Goes to next song")
    async def next_slash(self, interaction:discord.Interaction):
        await interaction.response.defer()
        await self.skip(interaction)
        await interaction.delete_original_response()
    
    @app_commands.command(name= "previous", description="Previous song")
    async def previous_slash(self, interaction:discord.Interaction):
        await interaction.response.defer()
        await self.previous(interaction)
        await interaction.delete_original_response()

    @app_commands.command(name= "pause", description="Pause song")
    async def pause_slash(self, interaction:discord.Interaction):
        await interaction.response.defer()
        await self.pause(interaction)
        await interaction.delete_original_response()

    @app_commands.command(name= "resume", description="Resume song")
    async def resume_slash(self, interaction:discord.Interaction):
        await interaction.response.defer()
        await self.resume(interaction)
        await interaction.delete_original_response()

    @app_commands.command(name= "shuffle", description="Shuffle song")
    async def shuffle_slash(self, interaction:discord.Interaction):
        await interaction.response.defer()
        await self.shuffle(interaction)
        await interaction.delete_original_response()

    @app_commands.command(name= "loop", description="Loop current song")
    async def loop_slash(self, interaction:discord.Interaction):
        await interaction.response.defer()
        await self.loop(interaction)
        await interaction.delete_original_response()
    
    @app_commands.command(name= "flush", description="Empty current dataObj and stop music player")
    async def flush_slash(self, interaction:discord.Interaction):
        await interaction.response.defer()
        await self.flush(interaction)
        await interaction.delete_original_response()
    @app_commands.command(name= "reset", description="Full reset bot")
    async def reset_slash(self, interaction:discord.Interaction):
        await interaction.response.defer()
        await self.reset(interaction)
        await interaction.delete_original_response()

    @app_commands.command(name= "join", description="Bot joins your current voice channel")
    async def join_slash(self, interaction:discord.Interaction):
        await interaction.response.defer()
        await self.join(interaction)
        await interaction.delete_original_response()
    @app_commands.command(name= "help", description="Shows bot use information")
    async def help_slash(self, interaction:discord.Interaction):
        await interaction.response.defer()
        await self.help(interaction)
        await interaction.delete_original_response()

    @app_commands.command(name= "generate", description="Creates a dedicated text channel for PocBot's Music Interface")
    async def generate_slash(self, interaction:discord.Interaction):
        await interaction.response.defer()
        await self.generate(interaction)
        await interaction.delete_original_response()

    @app_commands.command(name= "switch_algorithm", description="Change the music search algorithm")
    async def switch_algorithm_slash(self, interaction:discord.Interaction):
        await interaction.response.defer()
        await self.switch_algorithm(interaction)
        await interaction.delete_original_response()

    @app_commands.command(name= "prefix", description="Change command prefix")
    async def prefix_slash(self, interaction:discord.Interaction, prefix:str):
        await interaction.response.defer()
        await self.prefix(interaction, prefix)
        await interaction.delete_original_response()
    
    @app_commands.command(name= "slashcommand", description="What does this do?")
    async def slashcommand_slash(self, interaction:discord.Interaction):
        await interaction.response.defer()
        await self.slashcommand(interaction)
        await interaction.delete_original_response()

