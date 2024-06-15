import discord
import time
import random
import asyncio

from discord                 import app_commands, FFmpegPCMAudio
from discord.ext             import commands, tasks
from cog.helper              import embed
from cog.helper.GuildData    import Guild_Music_Properties
from tinytag                 import TinyTag
import cog.helper.Setting    as     Setting
from cog.helper.Log          import *
from cog.helper.Functions    import *
from cog.helper.MusicSearch  import *
from Paths                   import FFMPEG_EXE_PATH



FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

def timeIt(start):
    print(time.perf_counter()-start)

class MusicCog(commands.Cog):
    def __init__(self, bot:commands.Bot, data:Guild_Music_Properties, gui_print:set, spotify:spotipy.Spotify):
        self.bot = bot
        self.spotify = spotify
        self.data = data
        self.gui_print = gui_print
        self.gui_loop.start()
        self.disconnect_check.start()
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
        
    #MUSIC PLAYER LOOP (not recursive)
    def music_player(self, guildName, guildID, voice_client, recall = False, last_pos = None):
        try:
            pos = self.data.get_pos(guildID)
            if last_pos == pos or pos is None:
                self.data.pos_forward(guildID)
            # else:
            #     pos = last_pos
            #     while pos != self.data.get_pos(guildID):
            #         pos = self.data.get_pos(guildID)
            #         time.sleep(1.5)
            if self.data.get_loop(guildID) is True:
                self.data.pos_backward(guildID)
            if self.data.empty_queue(guildID) and self.data.get_random(guildID) is True:
                song = GetRandom(self.bot)#Get Random may give errors causing problems to musc player
                self.data.add_song(guildID, song)
            if self.data.empty_queue(guildID):
                self.data.set_playing(guildID, False)
                self.data.set_idle_timestamp(guildID)
                self.gui_print.add(str(guildID))
                log(guildName, 'music player', 'finished')
                return
            
            #Moves song from queue to current
            song = self.data.get_current(guildID)
            if song['source'] in ['query', 'spotify']:
                query = song['query']
                song = SearchYoutube(query)
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
                self.data.set_current(guildID, song)
            elif song['source'] == 'spotify':
                song = GetSpotifyTrack(self.spotify, song['url'])
                self.data.set_current(guildID, song)
                song = SearchYoutube(song['query'])
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
            self.data.set_idle_timestamp(guildID)
            log(guildName, "now playing", song)
            pos = self.data.get_pos(guildID)
            voice_client.play(player, after= lambda x=None: self.music_player(guildName, guildID, voice_client, recall=True, last_pos = pos))
            return False
        except Exception as e:
            error_log('music_player', e, guildName=guildName)
            log('music_player', 'restarting')
            self.music_player(guildName, guildID, voice_client, recall=True, last_pos = pos)
            return True
    #CHECKS IF MUSIC_PLAYER LOOP SHOULD START
    async def music_player_start(self, user, guildName, guildID, voice_client):
        async with self.data.get_musicplayerLock(guildID): 
            try:
                voice_client = await voice_connect(user, guildName, guildID, voice_client)
                if voice_client.is_playing() == voice_client.is_paused() == self.data.get_playing(guildID) == False:
                    self.data.set_playing(guildID, True)
                    await nowPlayingHandler(self, guildID)                
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

        if await valid_play_command(self.data, user, channel, voice_client) is False:return
        
        if query == '' or query.count(' ') == len(query):
            msg = embed.no_query_prompt()
            await channel.send(embed = msg, delete_after=Setting.get_promptDelay())
            await GUI_HANDLER(self, channel, guildID)
            return
        
        try:
            if 'music.youtube.com' in query:
                song_data = GetYTMusic(query)
                if type(song_data) is list:
                    playlistType = 'YTMusic'
                    playlist_emb = queuePlaylist(guildName,guildID,song_data,playlistType,self.data)
                    msg = embed.queued_playlist_prompt(self.bot, playlist_emb, len(song_data), query, 'YTMusic')
                    await channel.send(embed=msg, delete_after=Setting.get_promptDelay()*30)
                    await self.music_player_start(user, guildName, guildID, voice_client)
                    await GUI_HANDLER(self, channel, guildID)                    
                    return
                if type(song_data) is dict:
                    self.data.add_song(guildID, song_data)
                    log(guildName, "queued", song_data)
                    msg = embed.queue_prompt(self.bot, song_data, guildID)
                    await channel.send(embed= msg, delete_after=Setting.get_promptDelay())
                    await self.music_player_start(user, guildName, guildID, voice_client)
                    await GUI_HANDLER(self, channel, guildID)
                    return
                msg = embed.invalid_link(query, 'YTMusic')
                await channel.send(embed= msg, delete_after=Setting.get_promptDelay())
                log(guildName,'invalid ytmusic url', query)
                await GUI_HANDLER(self, channel, guildID)
                return
            
            if 'youtube.com/' in query:
                song_data = GetYT(query)
                if type(song_data) is dict:
                    self.data.add_song(guildID, song_data)
                    log(guildName, "QUEUED", song_data)
                    msg = embed.queue_prompt(self.bot, song_data, guildID)
                    await channel.send(embed= msg, delete_after=Setting.get_promptDelay())
                    await self.music_player_start(user, guildName, guildID, voice_client)
                    await GUI_HANDLER(self, channel, guildID)
                    return
                if type(song_data) is list:
                    playlistType = 'Youtube'
                    playlist_emb = queuePlaylist(guildName,guildID, song_data, playlistType, self.data)                    
                    msg = embed.queued_playlist_prompt(self.bot, playlist_emb, len(song_data), query, 'Youtube')
                    await channel.send(embed = msg, delete_after=Setting.get_promptDelay()*30)
                    await self.music_player_start(user, guildName, guildID, voice_client)
                    await GUI_HANDLER(self, channel, guildID)
                    return
                msg = embed.invalid_link(query, 'Youtube')
                await channel.send(embed= msg, delete_after=Setting.get_promptDelay())
                log(guildName,'invalid youtube url', query)
                await GUI_HANDLER(self, channel, guildID)
                return
            
            if 'open.spotify.com' in query:
                song_data = GetSpotify(self.spotify, query)
                if type(song_data) is dict:
                    self.data.add_song(guildID, song_data)
                    log(guildName, "QUEUED", song_data)
                    msg = embed.queue_prompt(self.bot, song_data, guildID)
                    await channel.send(embed= msg, delete_after=Setting.get_promptDelay())
                    await self.music_player_start(user, guildName, guildID, voice_client)
                    await GUI_HANDLER(self, channel, guildID)
                    return
                if type(song_data) is list:
                    playlistType = 'Spotify'
                    playlist = song_data
                    playlist_emb = queuePlaylist(guildName,guildID,playlist,playlistType,self.data)
                    msg = embed.queued_playlist_prompt(self.bot, playlist_emb, len(playlist), query, 'Spotify')
                    await channel.send(embed= msg, delete_after=Setting.get_promptDelay()*30)
                    await self.music_player_start(user, guildName, guildID, voice_client)
                    await GUI_HANDLER(self, channel, guildID)
                    return
                log(guildName,'invalid spotify url', query)
                msg = embed.invalid_link(query, 'Spotify')
                await channel.send(embed= msg, delete_after=Setting.get_promptDelay())
                await GUI_HANDLER(self, channel, guildID)
                return
            
            if 'https://' in query:
                msg = embed.invalid_link(query)
                await channel.send(embed= msg, delete_after=Setting.get_promptDelay())
                log(guildName,'invalid url', query)
                await GUI_HANDLER(self, channel, guildID)
                return
            
            #query is not a link
            searchAlgorithm = Setting.get_searchAlgorithm(guildID)
            if searchAlgorithm == 'spotify':
                song = SearchSpotify(self.spotify, query)
            elif searchAlgorithm == 'youtube':
                song = SearchYoutube(query)
            else:
                song = None
            if song is None:
                await channel.send(embed = embed.no_search_result_prompt(query), delete_after=Setting.get_promptDelay())
                await GUI_HANDLER(self, channel, guildID)
                return
            self.data.add_song(guildID, song)
            log(guildName, "QUEUED", song)
            msg = embed.queue_prompt(self.bot, song, guildID)
            await channel.send(embed = msg, delete_after=Setting.get_promptDelay())
            await self.music_player_start(user, guildName, guildID, voice_client)
            await GUI_HANDLER(self, channel, guildID)
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
            if await valid_play_command(self.data, user, channel, voice_client) is False:return
            if self.data.switch_random(guildID) is True:
                log(guildName, 'RANDOM', 'On')
            else: 
                log(guildName, 'RANDOM', 'Off')
            await channel.send(embed = embed.random_prompt(self.data.get_random(guildID)), delete_after=Setting.get_promptDelay())
            await self.music_player_start(user, guildName, guildID, voice_client)
            await GUI_HANDLER(self, channel, guildID)
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
            if await valid_command(self.data, user, channel, voice_client) is False : return
            song = self.data.get_current(guildID)
            library = self.data.get_queue(guildID)+self.data.get_history(guildID)
            if library == [] and song is None:
                await channel.send(embed= embed.no_songs_prompt(), delete_after=Setting.get_promptDelay())
                await GUI_HANDLER(self, channel, guildID)
                return
            random.shuffle(library)
            if song is not None:
                library.insert(0, song)
            self.data.set_new_library(guildID, library)
            if self.data.get_playing(guildID) is True:
                await channel.send(embed= embed.shuffle_prompt(), delete_after=Setting.get_promptDelay())
                await GUI_HANDLER(self, channel, guildID)
                return
            await channel.send(embed= embed.shuffle_prompt(), delete_after=Setting.get_promptDelay())
            await self.music_player_start(user, guildName, guildID, voice_client)
            
            await GUI_HANDLER(self, channel, guildID)
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
            if await valid_command(self.data, user, channel, voice_client) is False:return
            song= self.data.get_current(guildID)
            self.data.pos_forward(guildID)
            if song is None:
                await channel.send(embed= embed.no_songs_prompt(), delete_after=Setting.get_promptDelay())
                await GUI_HANDLER(self, channel, guildID)
                return
            if (voice_client.is_playing() or voice_client.is_paused()):
                self.data.set_loop(guildID, False)
                voice_client.stop()
                await channel.send(embed= embed.skip_prompt(song), delete_after=Setting.get_promptDelay())
                await GUI_HANDLER(self, channel, guildID)
                return
            await channel.send(embed= embed.skip_prompt(song), delete_after=Setting.get_promptDelay())
            await GUI_HANDLER(self, channel, guildID)
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
            if await valid_command(self.data, user, channel, voice_client) is False:return
            self.data.pos_backward(guildID)
            song= self.data.get_current(guildID) 
            if song is None:
                await channel.send(embed= embed.no_songs_prompt(), delete_after=Setting.get_promptDelay())
                await GUI_HANDLER(self, channel, guildID)
                return
            self.data.set_loop(guildID, False)
            if voice_client.is_playing() or voice_client.is_paused():
                voice_client.stop()
                await channel.send(embed= embed.previous_prompt(song), delete_after=Setting.get_promptDelay())
                await GUI_HANDLER(self, channel, guildID)
                return
            await channel.send(embed= embed.previous_prompt(song), delete_after=Setting.get_promptDelay())
            await GUI_HANDLER(self, channel, guildID)
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
            if await valid_command(self.data, user, channel, voice_client) is False:return
            song = self.data.get_current(guildID)
            if voice_client.is_playing() and not voice_client.is_paused():
                log(guildName, 'PAUSED', song)
                voice_client.pause()
                await channel.send(embed= embed.pause_prompt(song), delete_after=Setting.get_promptDelay())
                await GUI_HANDLER(self, channel, guildID)
                return
            if not voice_client.is_playing() and voice_client.is_paused():
                await channel.send(embed= embed.already_paused_prompt(song), delete_after=Setting.get_promptDelay())
                await GUI_HANDLER(self, channel, guildID)
                return
            await channel.send(embed= embed.no_songs_prompt(), delete_after=Setting.get_promptDelay())
            await GUI_HANDLER(self, channel, guildID)
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
            if await valid_command(self.data, user, channel, voice_client) is False:return
            song = self.data.get_current(guildID)
            if not voice_client.is_playing() and voice_client.is_paused():
                log(guildName, 'resume', song)
                voice_client.resume()
                await channel.send(embed= embed.resume_prompt(song), delete_after=Setting.get_promptDelay())
                await GUI_HANDLER(self, channel, guildID)
                return
            if voice_client.is_playing() and not voice_client.is_paused():
                await channel.send(embed= embed.already_playing_prompt(song), delete_after=Setting.get_promptDelay())
                await GUI_HANDLER(self, channel, guildID)
                return
            await channel.send(embed= embed.no_songs_prompt('Resume'), delete_after=Setting.get_promptDelay())
            await GUI_HANDLER(self, channel, guildID)
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
            if await valid_command(self.data, user, channel, voice_client) is False:return
            if voice_client.is_playing() or voice_client.is_paused():
                song = self.data.get_current(guildID)
                self.data.switch_loop(guildID)
                self.data.set_random(guildID, False)
                loop_var = self.data.get_loop(guildID)
                if loop_var is True:
                    log(guildName, 'now looping', song)
                else:
                    log(guildName, 'stopped looping', song)
                loop_var = self.data.get_loop(guildID)
                song= self.data.get_current(guildID) 
                await channel.send(embed= embed.loop_prompt(loop_var, song), delete_after=Setting.get_promptDelay())
                await GUI_HANDLER(self, channel, guildID)
                return
            await channel.send(embed= embed.no_songs_prompt('loop'), delete_after=Setting.get_promptDelay())
            await GUI_HANDLER(self, channel, guildID)
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
            if await valid_play_command(self.data, user, channel, voice_client) is False:
                return
            self.data.full_reset(guildID)
            if voice_client is not None:
                channel_name = voice_client.channel.name
                if voice_client.is_playing() or voice_client.is_paused():
                    voice_client.stop()
                await voice_client.disconnect()
                log(guildName, 'DISCONNECTED (user reset)', channel_name)
            self.data.full_reset(guildID)
            await channel.send(embed= embed.reset_prompt(), delete_after=Setting.get_promptDelay())
            await GUI_HANDLER(self, channel, guildID)
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
            if await valid_play_command(self.data, user, channel, voice_client) is False:
                return
            self.data.reset(guildID)
            if voice_client is not None:
                if voice_client.is_playing() or voice_client.is_paused():
                    voice_client.stop()
            self.data.full_reset(guildID)
            msg = embed.flush_prompt()
            await channel.send(embed=msg, delete_after=Setting.get_promptDelay())
            await GUI_HANDLER(self, channel, guildID)
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
        self.data.initialize(guildID)
        try:
            await printHelpPrompt(channel, self.bot, guildID)
            await asyncio.sleep(Setting.get_promptDelay())
            await GUI_HANDLER(self, channel, guildID)
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
        self.data.initialize(guildID)
        try:
            new_channel = await create_bot_channel(message.guild)
            if new_channel is None: 
                await channel.send(embed=embed.already_generated_prompt())
                return
            await printHelpPrompt(new_channel, self.bot, guildID, permanent = True)
            await GUI_HANDLER(self, new_channel, guildID)
            await channel.send(embed=embed.generated_prompt())
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
            if await valid_join_command(self.data, user, channel, voice_client) is False:return
            voice_client = await voice_connect(user, guildName, guildID, voice_client)
            await channel.send(embed= embed.joined_prompt(voice_client.channel), delete_after=Setting.get_promptDelay())
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
        self.data.initialize(guildID)
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
        self.data.initialize(guildID)
        try:
            if prefix == ''or  ' ' in prefix:
                await channel.send(embed= embed.blank_prefix_prompt(prefix), delete_after=Setting.get_promptDelay())
                return
            Setting.set_guildPrefix(guildID, prefix)
            log(guildName, 'changed prefix', prefix)
            await channel.send(embed= embed.changed_prefix_prompt(prefix), delete_after=Setting.get_promptDelay())
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
                await nowPlayingHandler(self, guildID)
                await GUI_HANDLER(self, None, int(guildID))
        except Exception as e:
            error_log('gui_loop', e)

############# LISTENERS ########################################################################
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
            self.data.initialize(guildID)
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
            self.data.reset(guildID)
            if voice_client is not None:
                if voice_client.is_playing() or voice_client.is_paused():
                    self.gui_print.add(guildID)
                    voice_client.stop()
                await voice_client.disconnect()
            log(guildName, 'disconnected (empty)', before.channel.name)
            await GUI_HANDLER(self, None, guildID)
            return
        
    @commands.Cog.listener()
    async def on_guild_join(self, guild:discord.guild.Guild):
        try:
            guildID = guild.id
            self.data.initialize(guildID)
            new_channel = await create_bot_channel(self.data, guild)
            if new_channel is None: 
                return
            await printHelpPrompt(new_channel, self.bot, guildID, permanent=True)
            await GUI_HANDLER(self, new_channel, guildID)
        except Exception as e:
            error_log('on_guild_join',e)


####### Auto Disconnect Bot After X Seconds idle
    @tasks.loop(minutes=5)
    async def disconnect_check(self):
        try:
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
                    await GUI_HANDLER(self, None, guildID)
                    log(voice.guild.name, 'disconnected (timeout)', channelName)
        except Exception as e:
            error_log('disconnect_check', e)

    @commands.command(name= "sync")
    async def sync(self,ctx):
        guildName = ctx.guild.name
        try:
            sync_num = await ctx.bot.tree.sync()
            log(guildName, 'synced commands', sync_num)
            await ctx.send(embed= embed.synced_prompt())
        except Exception as e:
            print(e)
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
    
    @app_commands.command(name= "flush", description="Empty current data and stop music player")
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

