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


FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
FFMPEG_LOC = "C:\\Users\\p\\Downloads\\ffmpeg\\bin\\ffmpeg.exe"
LOCAL_MUSIC_PATH1 = "C:\\Users\\p\\Documents\\SERVER\\music\\Formatted"
LOCAL_MUSIC_PATH = 'S:\\music\\Formatted'

class MusicCog(commands.Cog):
    def __init__(self, bot:commands.Bot, data:Guild_Music_Properties, gui_print:set, spotify:spotipy.Spotify):
        self.bot = bot
        self.spotify = spotify
        self.data = data
        self.gui_print = gui_print
        self.gui_loop.start()
        self.disconnect_check.start()
        self.funcList = {
                'p'         : self.play_ctx,
                'play'      : self.play_ctx,
                's'         : self.skip_ctx,
                'skip'      : self.skip_ctx,
                'n'         : self.skip_ctx,
                'next'      : self.skip_ctx,
                'prev'      : self.previous_ctx,
                'previous'  : self.previous_ctx,
                'playrandom': self.playrandom_ctx,
                'pr'        : self.playrandom_ctx,
                'shuffle'   : self.shuffle_ctx, 
                'sh'        : self.shuffle_ctx, 
                'pause'     : self.pause_ctx,
                'pa'        : self.pause_ctx,
                'r'         : self.resume_ctx,
                'resume'    : self.resume_ctx,
                'loop'      : self.loop_ctx,
                'l'         : self.loop_ctx,
                'flush'     : self.flush_ctx,
                'f'         : self.flush_ctx,
                'join'      : self.join_ctx,
                'j'      : self.join_ctx,
                'h'         : self.help_ctx,
                'help'      : self.help_ctx,
                'reset'     : self.reset_ctx,
                'generate'  : self.generate_ctx,
                'switch_algorithm' : self.switch_algorithm_ctx,
                'prefix'    : self.prefix_ctx}
        
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
                flac_song_list = os.listdir(LOCAL_MUSIC_PATH)
                song = random.choice(flac_song_list)
                path = LOCAL_MUSIC_PATH + '\\'+ song
                song_metadata = TinyTag.get(path)
                print(song_metadata)
                title = song_metadata.title
                author = song_metadata.artist
                song = {
                    'title' : title, 
                    'author': author, 
                    'url'   : f'{LOCAL_MUSIC_PATH}\\{song}',
                    'source': 'local'}
                self.data.add_song(guildID, song)
            if self.data.empty_queue(guildID):
                self.data.set_playing(guildID, False)
                self.data.set_idle_timestamp(guildID)
                self.gui_print.add(str(guildID))
                log(guildName, 'music player', 'finished')
                return
            
            #Moves song from queue to current
            song = self.data.get_current(guildID)
            if song['source'] == 'local':
                player = FFmpegPCMAudio(
                    song['url'],
                    executable=FFMPEG_LOC)
            elif song['source'] == 'query':
                query = song['query']
                song = SearchYoutube(query)
                player = FFmpegPCMAudio(
                    song['url'],
                    **FFMPEG_OPTIONS,
                    executable= FFMPEG_LOC)
            elif song['source'] == 'YTsong':
                player = FFmpegPCMAudio(
                    song['url'],
                    **FFMPEG_OPTIONS,
                    executable= FFMPEG_LOC)
            elif song['source'] == 'spotify':
                song = GetSpotifyTrack(self.spotify, song['url'])
                self.data.set_current(guildID, song)
                song = self.data.get_current(guildID)
                query = song['query']
                song = SearchYoutube(query)
                player = FFmpegPCMAudio(
                    song['url'],
                    **FFMPEG_OPTIONS,
                    executable= FFMPEG_LOC)
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
    async def music_player_start(self, user, guildName, guildID, voice_client, channel):
        try:
            voice_client = await voice_connect(user, guildName, guildID, voice_client)
            self.data.set_channel(guildID, channel)
            if voice_client.is_playing() == voice_client.is_paused() == self.data.get_playing(guildID) == False:
                await channel.send(embed=embed.now_playing_prompt(self.bot, self.data.get_current(guildID), guildID))
                self.data.set_playing(guildID, True)
                log(guildName, 'MUSIC PLAYER', 'starting')
                self.music_player(guildName, guildID, voice_client)
        except Exception as e:
            error_log('music_player_start', e, guildName=guildName)
        
#######PLAY FUNCTIONS######################################################
    @app_commands.check(valid_play_command_slash)
    @app_commands.command(name= "play", description="Play a song or playlist with name or playlist url")
    async def play(self, interaction:discord.Interaction, query:str):
        user = interaction.user
        guildName = interaction.user.guild.name
        guildID = interaction.user.guild.id
        voice_client = interaction.client.get_guild(guildID).voice_client
        channel = interaction.channel
        log(guildName, 'command', 'play')
        self.data.initialize(guildID)
        await interaction.response.defer(thinking=True)
        try:
            if 'music.youtube.com' in query:
                song_data = GetYTMusic(query)
                if type(song_data) is list:
                    playlistType = 'YTMusic'
                    playlist_emb = queuePlaylist(guildName,guildID,song_data, playlistType,self.data)
                    msg = embed.queued_playlist_prompt(self.bot, playlist_emb, len(song_data), query, 'YTMusic')
                    await interaction.followup.send(embed=msg)
                    await self.music_player_start(user, guildName, guildID, voice_client, channel)
                    await GUI_HANDLER(self, guildID, channel)
                    return
                if type(song_data) is dict:
                    self.data.add_song(guildID, song_data)
                    log(guildName, "queued", song_data)
                    msg = embed.queue_prompt(self.bot, song_data, guildID)
                    await interaction.followup.send(embed= msg)
                    await self.music_player_start(user, guildName, guildID, voice_client, channel)
                    await GUI_HANDLER(self, guildID, channel)
                    return
                msg = embed.invalid_link(query, 'YTMusic Song')
                await interaction.followup.send(embed= msg, ephemeral=True)
                log(guildName,'invalid ytmusic url', query)
                return
            
            if 'youtube.com' in query:
                song_data = GetYT(query)
                if type(song_data) is dict:
                    self.data.add_song(guildID, song_data)
                    log(guildName, "QUEUED", song_data)
                    msg = embed.queue_prompt(self.bot, song_data, guildID)
                    await interaction.followup.send(embed= msg)
                    await self.music_player_start(user, guildName, guildID, voice_client, channel)
                    await GUI_HANDLER(self, guildID, channel)
                    return
                if type(song_data) is list:
                    playlistType = 'Youtube'
                    playlist_emb = queuePlaylist(guildName, guildID, song_data, playlistType, self.data)      
                    msg = embed.queued_playlist_prompt(self.bot, playlist_emb, len(song_data), query, 'Youtube')
                    await interaction.followup.send(embed = msg)              
                    await self.music_player_start(user, guildName, guildID, voice_client, channel)
                    await GUI_HANDLER(self, guildID, channel)
                    return
                log(guildName,'invalid youtube url', query)
                msg = embed.invalid_link(query, 'Youtube')
                await interaction.followup.send(embed= msg, ephemeral=True)
                await GUI_HANDLER(self, guildID, channel)
                return
            
            if 'open.spotify.com' in query:
                song_data = GetSpotify(self.spotify, query)
                if type(song_data) is dict:
                    self.data.add_song(guildID, song_data)
                    log(guildName, "QUEUED", song_data)
                    msg = embed.queue_prompt(self.bot, song_data, guildID)
                    await interaction.followup.send(embed= msg)
                    await self.music_player_start(user, guildName, guildID, voice_client, channel)
                    await GUI_HANDLER(self, guildID, channel)
                    return
                if type(song_data) is list:
                    playlistType = 'Spotify'
                    playlist = song_data
                    playlist_emb = queuePlaylist(guildName,guildID,playlist,playlistType,self.data)
                    msg = embed.queued_playlist_prompt(self.bot, playlist_emb, len(playlist), query, 'Spotify')
                    await interaction.followup.send(embed= msg)
                    await self.music_player_start(user, guildName, guildID, voice_client, channel)
                    await GUI_HANDLER(self, guildID, channel)
                    return
                
                msg = embed.invalid_link(query, 'Spotify')
                await interaction.followup.send(embed= msg, ephemeral=True)
                await GUI_HANDLER(self, guildID, channel)
                log(guildName,'invalid spotify url', query)
                return

            if 'https://' in query:
                log(guildName,'invalid url', query)
                msg = embed.invalid_link(query)
                await interaction.followup.send(embed= msg, ephemeral=True)
                await GUI_HANDLER(self, guildID, channel)
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
                await interaction.followup.send(embed = embed.no_search_result_prompt(query), ephemeral=True)
                await GUI_HANDLER(self, guildID, channel)
                return
            self.data.add_song(guildID, song)
            log(guildName, "QUEUED", f'{query} (query)')
            await interaction.followup.send(embed = embed.queue_prompt(self.bot, song, guildID))
            await self.music_player_start(user, guildName, guildID, voice_client, channel)
            await GUI_HANDLER(self, guildID, channel)
        except Exception as e:
            error_log('play', e, guildName=guildName)
    
    @app_commands.check(valid_play_command_slash)
    @app_commands.command(name= "playrandom", description="Play random songs from pocket bot library forever")
    async def playrandom(self, interaction:discord.Interaction): 
        try:
            user = interaction.user
            guildName = interaction.user.guild.name
            guildID = interaction.user.guild.id
            channel = interaction.channel
            voice_client = interaction.client.get_guild(guildID).voice_client
            log(guildName, 'command', 'play_random')
            self.data.initialize(guildID)
            if self.data.switch_random(guildID) is True:
                log(guildName, 'RANDOM', 'On')
            else: 
                log(guildName, 'RANDOM', 'Off')
            await interaction.response.send_message(embed= embed.random_prompt(self.data.get_random(guildID)))
            await self.music_player_start(user, guildName, guildID, voice_client, channel)
            await GUI_HANDLER(self, guildID, channel)
        except Exception as e:
            error_log('play_random', e)

    @app_commands.check(valid_command_slash)
    @app_commands.command(name= "skip", description="Skips song")
    async def skip(self, interaction:discord.Interaction):
        try:
            guildName = interaction.user.guild.name
            guildName = interaction.user.guild.name
            guildID = interaction.user.guild.id
            channel = interaction.channel
            voice_client = interaction.client.get_guild(guildID).voice_client
            log(guildName, 'command', 'skip')
            self.data.initialize(guildID)
            self.data.set_loop(guildID, False)
            song= self.data.get_current(guildID)
            self.data.pos_forward(guildID)
            if song is None:
                await interaction.response.send_message(embed= embed.no_songs_prompt())
                await GUI_HANDLER(self, guildID, channel)
                return
            if (voice_client.is_playing() or voice_client.is_paused()):
                voice_client.stop()
                await interaction.response.send_message(embed= embed.skip_prompt(song))
                await GUI_HANDLER(self, guildID, channel)
                return
            await interaction.response.send_message(embed= embed.skip_prompt(song))
            await GUI_HANDLER(self, guildID, channel)
        except Exception as e:
            error_log('skip', e)

    @app_commands.check(valid_command_slash)
    @app_commands.command(name= "next", description="Goes to next song")
    async def next(self, interaction:discord.Interaction):
        try:
            guildName = interaction.user.guild.name
            guildName = interaction.user.guild.name
            guildID = interaction.user.guild.id
            channel = interaction.channel
            voice_client = interaction.client.get_guild(guildID).voice_client
            log(guildName, 'command', 'next')
            self.data.initialize(guildID)
            self.data.set_loop(guildID, False)
            song= self.data.get_current(guildID)
            self.data.pos_forward(guildID)
            if song is None:
                await interaction.response.send_message(embed= embed.no_songs_prompt())
                await GUI_HANDLER(self, guildID, channel)
                return
            if (voice_client.is_playing() or voice_client.is_paused()):
                voice_client.stop()
                await interaction.response.send_message(embed= embed.skip_prompt(song))
                await GUI_HANDLER(self, guildID, channel)
                return
            await interaction.response.send_message(embed= embed.skip_prompt(song))
            await GUI_HANDLER(self, guildID, channel)
        except Exception as e:
            error_log('next', e)
    
    @app_commands.check(valid_command_slash)
    @app_commands.command(name= "previous", description="Previous song")
    async def previous(self, interaction:discord.Interaction):
        try:
            user = interaction.user
            guildName = interaction.user.guild.name
            guildID = interaction.user.guild.id
            channel = interaction.channel
            voice_client = interaction.client.get_guild(guildID).voice_client
            log(guildName, 'COMMAND', 'previous')
            self.data.initialize(guildID)
            self.data.pos_backward(guildID)
            song= self.data.get_current(guildID) 
            if song is None:
                await interaction.response.send_message(embed= embed.no_songs_prompt())
                await GUI_HANDLER(self, guildID, channel)
                return
            self.data.set_loop(guildID, False)
            if voice_client.is_playing() or voice_client.is_paused():
                voice_client.stop()
                await interaction.response.send_message(embed= embed.previous_prompt(song))
                await GUI_HANDLER(self, guildID, channel)
                return
            await interaction.response.send_message(embed= embed.previous_prompt(song))
            await GUI_HANDLER(self, guildID, channel)
            await self.music_player_start(user, guildName, guildID, voice_client, channel)
            return
        except Exception as e:
            error_log('previous', e, guildName= guildName)

    @app_commands.check(valid_command_slash)
    @app_commands.command(name= "pause", description="Pause song")
    async def pause(self, interaction:discord.Interaction):
        try:
            guildName = interaction.user.guild.name
            guildID = interaction.user.guild.id
            channel = interaction.channel
            voice_client = interaction.client.get_guild(guildID).voice_client
            log(guildName, 'COMMAND', 'pause')
            self.data.initialize(guildID)
            song = self.data.get_current(guildID)
            if voice_client.is_playing() and not voice_client.is_paused():
                log(guildName, 'PAUSED', song)
                voice_client.pause()
                await interaction.response.send_message(embed= embed.pause_prompt(song))
                await GUI_HANDLER(self, guildID, channel)
                return
            if not voice_client.is_playing() and voice_client.is_paused():
                await interaction.response.send_message(embed= embed.already_paused_prompt(song))
                await GUI_HANDLER(self, guildID, channel)
                return
            await interaction.response.send_message(embed= embed.no_songs_prompt())
            await GUI_HANDLER(self, guildID, channel)
        except Exception as e:
            error_log('pause', e)
        await interaction.delete_original_response()

    @app_commands.check(valid_command_slash)
    @app_commands.command(name= "resume", description="Resume song")
    async def resume(self, interaction:discord.Interaction):
        try:
            guildName = interaction.user.guild.name
            guildID = interaction.user.guild.id
            channel = interaction.channel
            voice_client = interaction.client.get_guild(guildID).voice_client
            log(guildName, 'COMMAND', 'previous')
            self.data.initialize(guildID)
            song = self.data.get_current(guildID)
            if not voice_client.is_playing() and voice_client.is_paused():
                log(guildName, 'RESUME', song)
                voice_client.resume()
                await interaction.response.send_message(embed= embed.resume_prompt(song))
                await GUI_HANDLER(self, guildID, channel)
                return
            if voice_client.is_playing() and not voice_client.is_paused():
                await interaction.response.send_message(embed= embed.already_playing_prompt(song))
                await GUI_HANDLER(self, guildID, channel)
                return
            await interaction.response.send_message(embed= embed.no_songs_prompt())
            await GUI_HANDLER(self, guildID, channel)
        except Exception as e:
            error_log('RESUME', e)

    @app_commands.check(valid_command_slash)
    @app_commands.command(name= "shuffle", description="Shuffle song")
    async def shuffle(self, interaction:discord.Interaction):
        try:
            user = interaction.user
            guildName = interaction.user.guild.name
            guildID = interaction.user.guild.id
            channel = interaction.channel
            voice_client = interaction.client.get_guild(guildID).voice_client
            log(guildName, 'COMMAND', 'shuffle')
            self.data.initialize(guildID)
            current_song = self.data.get_current(guildID)
            library = self.data.get_queue(guildID)+self.data.get_history(guildID)
            if library == [] and current_song is None:
                await interaction.response.send_message(embed= embed.no_songs_prompt())
                await GUI_HANDLER(self, guildID, channel)
                return
            random.shuffle(library)
            if current_song is not None:
                library.insert(0, current_song)
            self.data.set_new_library(guildID, library)
            await interaction.response.send_message(embed= embed.shuffle_prompt())
            await GUI_HANDLER(self, guildID, channel)
            await self.music_player_start(user, guildName, guildID, voice_client, channel)
        except Exception as e:
            error_log('shuffle', e, guildName= guildName)

    @app_commands.check(valid_command_slash)
    @app_commands.command(name= "loop", description="Loop current song")
    async def loop(self, interaction:discord.Interaction):
        try:
            guildName = interaction.user.guild.name
            guildID = interaction.user.guild.id
            channel = interaction.channel
            voice_client = interaction.client.get_guild(guildID).voice_client
            log(guildName, 'COMMAND', 'loop')
            self.data.initialize(guildID)
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
            await interaction.response.send_message(embed= embed.loop_prompt(loop_var, song))
            await GUI_HANDLER(self, guildID, channel)
            return
        except Exception as e:
            error_log('loop', e, guildName= guildName)
    
    @app_commands.check(valid_command_slash)
    @app_commands.command(name= "flush", description="Empty current data and stop music player")
    async def flush(self, interaction:discord.Interaction):
        try:
            guildName = interaction.user.guild.name
            guildID = interaction.user.guild.id
            channel = interaction.channel
            voice_client = interaction.client.get_guild(guildID).voice_client
            log(guildName, 'COMMAND', 'flush')
            await interaction.response.defer()
            self.data.initialize(guildID)
            self.data.reset(guildID)
            await GUI_HANDLER(self, guildID, channel)
            if voice_client.is_playing() or voice_client.is_paused():
                voice_client.stop()
            self.data.full_reset(guildID)
            await interaction.followup.send(embed= embed.flush_prompt())
    
        except Exception as e:
            error_log('flush', e, guildName= guildName)

    @app_commands.check(valid_command_slash)
    @app_commands.command(name= "reset", description="Full reset bot")
    async def reset(self, interaction:discord.Interaction):
        try:
            guildName = interaction.user.guild.name
            guildID = interaction.user.guild.id
            channel = interaction.channel
            voice_client = interaction.client.get_guild(guildID).voice_client
            log(guildName, 'COMMAND', 'reset')
            self.data.initialize(guildID)
            self.data.full_reset(guildID)
            if voice_client is not None:
                channel_name = voice_client.channel.name
                if voice_client.is_playing() or voice_client.is_paused():
                    voice_client.stop()
                await voice_client.disconnect()
                log(guildName, 'DISCONNECTED (force)', channel_name)
            await interaction.response.send_message(embed= embed.reset_prompt())
            await GUI_HANDLER(self, guildID, channel)
        except Exception as e:
            error_log('reset', e, guildName= guildName)

    @app_commands.check(valid_play_command_slash)
    @app_commands.command(name= "join", description="Bot joins your current voice channel")
    async def join(self, interaction:discord.Interaction):
        try:
            user = interaction.user
            guildName = interaction.user.guild.name
            guildID = interaction.user.guild.id
            self.data.initialize(guildID)
            voice_client = interaction.client.get_guild(guildID).voice_client
            voice_client = await voice_connect(user, guildName, guildID, voice_client)
            await interaction.response.send_message(embed= embed.joined_prompt(voice_client.channel))
        except Exception as e:
            error_log('join', e)

    @app_commands.command(name= "help", description="Shows bot use information")
    async def help(self, interaction:discord.Interaction):
        guildName = interaction.user.guild.name
        guildID = interaction.user.guild.id
        channel = interaction.channel
        log(guildName, 'command', 'help')
        self.data.initialize(guildID)
        await printHelpPrompt(interaction, self.bot, guildID)
        await asyncio.sleep(Setting.get_helpPromptDelay())
        await GUI_HANDLER(self,guildID, channel)

    @app_commands.command(name= "generate", description="Creates a dedicated text channel for PocBot's Music Interface")
    async def generate(self, interaction:discord.Interaction):
        try:
            guildName = interaction.user.guild.name
            guildID = interaction.user.guild.id
            log(guildName, 'command', 'generate')
            self.data.initialize(guildID)
            channel = await create_bot_channel(self.data, interaction.guild)
            if channel is None: 
                await interaction.response.send_message(embed= embed.already_generated_prompt())
                return
            if channel == 'error':
                return
            await printHelpPrompt(interaction, self.bot, guildID)
            await GUI_HANDLER(self, guildID, channel.id)
            await interaction.response.send_message(embed=embed.generated_prompt())
        except Exception as e:
            error_log('generate', e)

    @app_commands.command(name= "switch_algorithm", description="Change the music search algorithm")
    async def switch_algorithm(self, interaction:discord.Interaction):
        try:
            user = interaction.user
            guildName = interaction.user.guild.name
            guildID = interaction.user.guild.id
            log(guildName, 'command', 'switchalgorithm')
            self.data.initialize(guildID)
            view = SearchAlgorithmView(self, user)
            await interaction.response.send_message(view=view, ephemeral=True)
        except Exception as e:
            error_log('switchalgorithm', e)

    @app_commands.command(name= "prefix", description="Change command prefix")
    async def prefix(self, interaction:discord.Interaction, prefix:str):
        try:
            user = interaction.user
            guildName = interaction.user.guild.name
            guildID = interaction.user.guild.id
            log(guildName, 'command', 'prefix')
            self.data.initialize(guildID)
            if prefix == '' or  ' ' in prefix:
                await interaction.response.send_message(embed= embed.blank_prefix_prompt(prefix))
                return
            Setting.set_guildPrefix(guildID, prefix)
            log(guildName, 'changed prefix', prefix)
            await interaction.response.send_message(embed= embed.changed_prefix_prompt(prefix))
        except Exception as e:
            error_log('prefix', e)

    @app_commands.command(name= "slashcommand", description="What does this do?")
    async def slashcommand(self, interaction:discord.Interaction):
        await interaction.response.defer()
        await interaction.delete_original_response()
### TEXT COMMANDS ##############################################################

    async def play_ctx(self, message:discord.message.Message, query):
        query = query
        user = message.author
        guildName = str(message.channel.guild.name)
        guildID = message.channel.guild.id
        channel = message.channel
        voice_client = self.bot.get_guild(guildID).voice_client
        log(guildName, 'command', 'play_ctx')
        self.data.initialize(guildID)
        if await valid_play_command_ctx(self.bot, message) is False:return
        if query == '' or query.count(' ') == len(query):
            msg = embed.no_query_prompt()
            await channel.send(embed = msg)
            await GUI_HANDLER(self, guildID, channel)
            return
        try:
            if 'music.youtube.com' in query:
                song_data = GetYTMusic(query)
                if type(song_data) is list:
                    playlistType = 'YTMusic'
                    playlist_emb = queuePlaylist(guildName,guildID,song_data,playlistType,self.data)
                    msg = embed.queued_playlist_prompt(self.bot, playlist_emb, len(song_data), query, 'YTMusic')
                    await channel.send(embed=msg)
                    await self.music_player_start(user, guildName, guildID, voice_client, channel)
                    await GUI_HANDLER(self, guildID, channel)                    
                    return
                if type(song_data) is dict:
                    self.data.add_song(guildID, song_data)
                    log(guildName, "queued", song_data)
                    msg = embed.queue_prompt(self.bot, song_data, guildID)
                    await channel.send(embed= msg)
                    await self.music_player_start(user, guildName, guildID, voice_client, channel)
                    await GUI_HANDLER(self, guildID, channel)
                    return
                msg = embed.invalid_link(query, 'YTMusic')
                await channel.send(embed= msg)
                log(guildName,'invalid ytmusic url', query)
                await GUI_HANDLER(self, guildID, channel)
                return
            
            if 'youtube.com/' in query:
                song_data = GetYT(query)
                if type(song_data) is dict:
                    self.data.add_song(guildID, song_data)
                    log(guildName, "QUEUED", song_data)
                    msg = embed.queue_prompt(self.bot, song_data, guildID)
                    await channel.send(embed= msg)
                    await self.music_player_start(user, guildName, guildID, voice_client, channel)
                    await GUI_HANDLER(self, guildID, channel)
                    return
                if type(song_data) is list:
                    playlistType = 'Youtube'
                    playlist_emb = queuePlaylist(guildName,guildID, song_data, playlistType, self.data)                    
                    msg = embed.queued_playlist_prompt(self.bot, playlist_emb, len(song_data), query, 'Youtube')
                    await channel.send(embed = msg)
                    await self.music_player_start(user, guildName, guildID, voice_client, channel)
                    await GUI_HANDLER(self, guildID, channel)
                    return
                msg = embed.invalid_link(query, 'Youtube')
                await channel.send(embed= msg)
                log(guildName,'invalid youtube url', query)
                await GUI_HANDLER(self, guildID, channel)
                return
            
            if 'open.spotify.com' in query:
                song_data = GetSpotify(self.spotify, query)
                if type(song_data) is dict:
                    self.data.add_song(guildID, song_data)
                    log(guildName, "QUEUED", song_data)
                    msg = embed.queue_prompt(self.bot, song_data, guildID)
                    await channel.send(embed= msg)
                    await self.music_player_start(user, guildName, guildID, voice_client, channel)
                    await GUI_HANDLER(self, guildID, channel)
                    return
                if type(song_data) is list:
                    playlistType = 'Spotify'
                    playlist = song_data
                    playlist_emb = queuePlaylist(guildName,guildID,playlist,playlistType,self.data)
                    msg = embed.queued_playlist_prompt(self.bot, playlist_emb, len(playlist), query, 'Spotify')
                    await channel.send(embed= msg)
                    await self.music_player_start(user, guildName, guildID, voice_client, channel)
                    await GUI_HANDLER(self, guildID, channel)
                    return
                log(guildName,'invalid spotify url', query)
                msg = embed.invalid_link(query, 'Spotify')
                await channel.send(embed= msg)
                await GUI_HANDLER(self, guildID, channel)
                return
            
            if 'https://' in query:
                msg = embed.invalid_link(query)
                await channel.send(embed= msg)
                log(guildName,'invalid url', query)
                await GUI_HANDLER(self, guildID, channel)
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
                await channel.send(embed = embed.no_search_result_prompt(query))
                await GUI_HANDLER(self, guildID, channel)
                return
            self.data.add_song(guildID, song)
            log(guildName, "QUEUED", song)
            msg = embed.queue_prompt(self.bot, song, guildID)
            await channel.send(embed = msg)
            await self.music_player_start(user, guildName, guildID, voice_client, channel)
            await GUI_HANDLER(self, guildID, channel)
            return
        except Exception as e:
            error_log('play_tc', e, guildName=guildName)

    async def playrandom_ctx(self, message:discord.message.Message):
        try:
            user = message.author
            guildName = str(message.channel.guild.name)
            guildID = message.channel.guild.id
            channel = message.channel
            voice_client = self.bot.get_guild(guildID).voice_client
            log(guildName, 'command', 'play_random_tc')
            self.data.initialize(guildID)
            if await valid_play_command_ctx(self.bot, message) is False:return
            if self.data.switch_random(guildID) is True:
                log(guildName, 'RANDOM', 'On')
            else: 
                log(guildName, 'RANDOM', 'Off')
            await channel.send(embed = embed.random_prompt(self.data.get_random(guildID)))
            await self.music_player_start(user, guildName, guildID, voice_client, channel)
            await GUI_HANDLER(self, guildID, channel)
        except Exception as e:
            error_log('play_random_tc', e, guildName=guildName)
    
    async def shuffle_ctx(self, message:discord.message.Message):
        try:
            user = message.author
            guildName = str(message.channel.guild.name)
            guildID = message.channel.guild.id
            channel = message.channel
            voice_client = self.bot.get_guild(guildID).voice_client
            log(guildName, 'command', 'shuffle_ctx')
            self.data.initialize(guildID)
            if await valid_command_ctx(self.bot, message) is False : return
            song = self.data.get_current(guildID)
            library = self.data.get_queue(guildID)+self.data.get_history(guildID)
            if library == [] and song is None:
                await channel.send(embed= embed.no_songs_prompt())
                await GUI_HANDLER(self, guildID, channel)
                return
            random.shuffle(library)
            if song is not None:
                library.insert(0, song)
            self.data.set_new_library(guildID, library)
            if self.data.get_playing(guildID) is True:
                await channel.send(embed= embed.shuffle_prompt())
                await GUI_HANDLER(self, guildID, channel)
                return
            await channel.send(embed= embed.shuffle_prompt())
            await self.music_player_start(user, guildName, guildID, voice_client, channel)
            
            await GUI_HANDLER(self, guildID, channel)
        except Exception as e:
            error_log('shuffle_ctx', e)
    
    async def skip_ctx(self, message:discord.message.Message):
        try:
            user = message.author
            guildName = str(message.channel.guild.name)
            guildID = message.channel.guild.id
            channel = message.channel
            voice_client = self.bot.get_guild(guildID).voice_client
            log(guildName, 'command', 'skip_ctx')
            self.data.initialize(guildID)
            if await valid_command_ctx(self.bot, message) is False:return
            song= self.data.get_current(guildID)
            self.data.pos_forward(guildID)
            if song is None:
                await channel.send(embed= embed.no_songs_prompt())
                await GUI_HANDLER(self, guildID, channel)
                return
            if (voice_client.is_playing() or voice_client.is_paused()):
                self.data.set_loop(guildID, False)
                voice_client.stop()
                await channel.send(embed= embed.skip_prompt(song))
                await GUI_HANDLER(self, guildID, channel)
                return
            await channel.send(embed= embed.skip_prompt(song))
            await GUI_HANDLER(self, guildID, channel)
        except Exception as e:
            error_log('skip_ctx', e)

    async def previous_ctx(self, message:discord.message.Message):
        try:
            user = message.author
            guildName = str(message.channel.guild.name)
            guildID = message.channel.guild.id
            channel = message.channel
            voice_client = self.bot.get_guild(guildID).voice_client
            log(guildName, 'COMMAND', 'previous_ctx')
            self.data.initialize(guildID)
            if await valid_command_ctx(self.bot, message) is False:return
            self.data.pos_backward(guildID)
            song= self.data.get_current(guildID) 
            if song is None:
                await channel.send(embed= embed.no_songs_prompt())
                await GUI_HANDLER(self, guildID, channel)
                return
            self.data.set_loop(guildID, False)
            if voice_client.is_playing() or voice_client.is_paused():
                voice_client.stop()
                await channel.send(embed= embed.previous_prompt(song))
                await GUI_HANDLER(self, guildID, channel)
                return
            await channel.send(embed= embed.previous_prompt(song))
            await GUI_HANDLER(self, guildID, channel)
            await self.music_player_start(user, guildName, guildID, voice_client, channel)
        except Exception as e:
            error_log('previous_ctx', e, guildName= guildName)
    
    async def pause_ctx(self, message:discord.message.Message):
        try:
            user = message.author
            guildName = str(message.channel.guild.name)
            guildID = message.channel.guild.id
            channel = message.channel
            voice_client = self.bot.get_guild(guildID).voice_client
            log(guildName, 'COMMAND', 'pause_ctx')
            self.data.initialize(guildID)
            if await valid_command_ctx(self.bot, message) is False:return
            song = self.data.get_current(guildID)
            if voice_client.is_playing() and not voice_client.is_paused():
                log(guildName, 'PAUSED', song)
                voice_client.pause()
                await channel.send(embed= embed.pause_prompt(song))
                await GUI_HANDLER(self, guildID, channel)
                return
            if not voice_client.is_playing() and voice_client.is_paused():
                await channel.send(embed= embed.already_paused_prompt(song))
                await GUI_HANDLER(self, guildID, channel)
                return
            await channel.send(embed= embed.no_songs_prompt())
            await GUI_HANDLER(self, guildID, channel)
        except Exception as e:
            error_log('pause_ctx', e, guildName=guildName)
            
    async def resume_ctx(self, message:discord.message.Message):
        try:
            user = message.author
            guildName = str(message.channel.guild.name)
            guildID = message.channel.guild.id
            channel = message.channel
            voice_client = self.bot.get_guild(guildID).voice_client
            log(guildName, 'COMMAND', 'resume_ctx')
            self.data.initialize(guildID)
            if await valid_command_ctx(self.bot, message) is False:return
            song = self.data.get_current(guildID)
            if not voice_client.is_playing() and voice_client.is_paused():
                log(guildName, 'resume_ctx', song)
                voice_client.resume()
                await channel.send(embed= embed.resume_prompt(song))
                await GUI_HANDLER(self, guildID, channel)
                return
            if voice_client.is_playing() and not voice_client.is_paused():
                await channel.send(embed= embed.already_playing_prompt(song))
                await GUI_HANDLER(self, guildID, channel)
                return
            await channel.send(embed= embed.no_songs_prompt('Resume'))
            await GUI_HANDLER(self, guildID, channel)
        except Exception as e:
            error_log('resume_ctx', e, guildName= guildName)

    async def loop_ctx(self, message:discord.message.Message):
        try:
            user = message.author
            guildName = str(message.channel.guild.name)
            guildID = message.channel.guild.id
            channel = message.channel
            voice_client = self.bot.get_guild(guildID).voice_client
            log(guildName, 'COMMAND', 'loop_ctx')
            self.data.initialize(guildID)
            if await valid_command_ctx(self.bot, message) is False:return
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
                await channel.send(embed= embed.loop_prompt(loop_var, song))
                await GUI_HANDLER(self, guildID, channel)
                return
            await channel.send(embed= embed.no_songs_prompt('loop'))
            await GUI_HANDLER(self, guildID, channel)
        except Exception as e:
            error_log('loop_ctx', e, guildName= guildName)
    
    async def reset_ctx(self, message:discord.message.Message):
        try:
            user = message.author
            guildName = str(message.channel.guild.name)
            guildID = message.channel.guild.id
            channel = message.channel
            voice_client = self.bot.get_guild(guildID).voice_client
            log(guildName, 'command', 'reset_ctx')
            self.data.initialize(guildID)
            if await valid_play_command_ctx(self.bot,message) is False:
                return
            self.data.full_reset(guildID)
            await GUI_HANDLER(self, guildID, channel)
            if voice_client is not None:
                channel_name = voice_client.channel.name
                if voice_client.is_playing() or voice_client.is_paused():
                    voice_client.stop()
                await voice_client.disconnect()
                log(guildName, 'DISCONNECTED (force)', channel_name)
            self.data.full_reset(guildID)
            await channel.send(embed= embed.reset_prompt())
        except Exception as e:
            error_log('reset_ctx', e, guildName= guildName)

    async def flush_ctx(self, message:discord.message.Message):
        try:
            user = message.author
            guildName = str(message.channel.guild.name)
            guildID = message.channel.guild.id
            channel = message.channel
            voice_client = self.bot.get_guild(guildID).voice_client
            log(guildName, 'command', 'flush_ctx')
            self.data.initialize(guildID)
            if await valid_play_command_ctx(self.bot, message) is False:
                return
            self.data.reset(guildID)
            await GUI_HANDLER(self, guildID, channel)
            if voice_client is not None:
                if voice_client.is_playing() or voice_client.is_paused():
                    voice_client.stop()
            self.data.full_reset(guildID)
            msg = embed.flush_prompt()
            await channel.send(embed=msg)
        except Exception as e:
            error_log('flush_ctx', e, guildName= guildName)

    async def help_ctx(self, message:discord.message.Message):
        user = message.author
        guildName = str(message.channel.guild.name)
        guildID = message.channel.guild.id
        channel = message.channel
        log(guildName, 'command', 'help_ctx')
        self.data.initialize(guildID)
        try:
            await printHelpPrompt(channel, self.bot, guildID)
            await asyncio.sleep(Setting.get_helpPromptDelay())
            await GUI_HANDLER(self,guildID, channel)
        except Exception as e:
            error_log('help_ctx', e, guildName= guildName)

    async def generate_ctx(self, message:discord.message.Message):
        try:
            user = message.author
            guildName = str(message.channel.guild.name)
            guildID = message.channel.guild.id
            channel = message.channel
            log(guildName, 'command', 'generate_ctx')
            self.data.initialize(guildID)
            channel = await create_bot_channel(self.data, message.guild)
            if channel is None: 
                await channel.send(embed=embed.already_generated_prompt())
                return
            await printHelpPrompt(channel, self.bot, guildID)
            await GUI_HANDLER(self, guildID, channel.id)
            await channel.send(embed=embed.generated_prompt())
        except Exception as e:
            error_log('generate_ctx', e)
    
    async def join_ctx(self, message:discord.message.Message):
        user = message.author
        guildName = str(message.channel.guild.name)
        guildID = message.channel.guild.id
        channel = message.channel
        voice_client = self.bot.get_guild(guildID).voice_client
        self.data.initialize(guildID)
        if await valid_play_command_ctx(self.bot,message) is False:
            return
        voice_client = await voice_connect(user, guildName, guildID, voice_client)
        await channel.send(embed= embed.joined_prompt(voice_client.channel))

    async def switch_algorithm_ctx(self, message:discord.message.Message):
        try:
            user = message.author
            guildName = str(message.channel.guild.name)
            guildID = message.channel.guild.id
            channel = message.channel
            log(guildName, 'command', 'switch_algorithm_ctx')
            self.data.initialize(guildID)
            view = SearchAlgorithmView(self, user)
            await channel.send(view=view, delete_after=Setting.get_helpPromptDelay())
        except Exception as e:
            error_log('switch_algorithm_ctx', e)

    async def prefix_ctx(self, message:discord.Interaction, prefix:str):
        try:
            user = message.author
            guildName = str(message.channel.guild.name)
            guildID = message.channel.guild.id
            channel = message.channel
            log(guildName, 'command', 'prefix_ctx')
            self.data.initialize(guildID)
            if prefix == ''or  ' ' in prefix:
                await channel.send(embed= embed.blank_prefix_prompt(prefix))
                return
            Setting.set_guildPrefix(guildID, prefix)
            log(guildName, 'changed prefix', prefix)
            await channel.send(embed= embed.changed_prefix_prompt(prefix))
        except Exception as e:
            error_log('prefix_ctx', e)

    async def slashcommand_ctx(self, message:discord.Interaction):
        return
############# LISTENERS ########################################################################
    # Keep music player at bottom of channel and listens for commands
    @commands.Cog.listener() 
    async def on_message(self, message:discord.message.Message):
        try:
            guildName = message.guild.name
            guildID = message.guild.id
            channel = message.channel
            user = message.author
            content = str(message.content)
            try:
                first_space = content.index(' ')
                command = content[:first_space]
                query = content[first_space+1:]
            except: 
                command = content
                query = ''
            
            guildPrefix = Setting.get_guildPrefix(guildID).lower()
            prefix = str(command[:len(guildPrefix)]).lower()
            command = str(command[len(guildPrefix):]).lower()
            if message.author.id != self.bot.user.id \
                and message.channel.id == Setting.get_channelID(guildID)\
                and prefix not in guildPrefix\
                and command not in self.funcList:
                await GUI_HANDLER(self, guildID, message.channel.id)
            if guildPrefix != prefix: return
            if command in self.funcList:
                if command in ['p','play','changeprefix']:
                    log(guildName, 'access','granted')
                    await self.funcList[command](message, query)
                else:
                    log(guildName, 'access','granted')
                    await self.funcList[command](message)
        except Exception as e :
            print(e)
        

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
            await GUI_HANDLER(self, guildID, None)
            return
        
    @commands.Cog.listener()
    async def on_guild_join(self, guild:discord.guild.Guild):
        try:
            guildID = guild.id
            self.data.initialize(guildID)
            channel = await create_bot_channel(self.data, guild)
            if channel is None: 
                return
            await printHelpPrompt(channel, self.bot, guildID)
            await GUI_HANDLER(self, guildID, channel.id)
        except Exception as e:
            print(e)


######## LOOP TO AUTO CHANGE GUI ##############################################################
    @tasks.loop(seconds = 5)
    async def gui_loop(self):
        try:
            while self.gui_print:
                guildID = self.gui_print.pop()
                if type(guildID) is str:
                    guildID = int(guildID)
                    channel = self.data.get_channel(guildID)
                    await channel.send(embed=embed.finished_prompt())
                    await GUI_HANDLER(self, guildID, None)
                    continue
                channel = self.data.get_channel(guildID)
                if channel.id != Setting.get_channelID(guildID):
                    await channel.send(embed=embed.now_playing_prompt(self.bot, self.data.get_current(guildID), guildID))
                await GUI_HANDLER(self, guildID, None)
        except Exception as e:
            error_log('gui_loop', e, self.gui_print)

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
                    await GUI_HANDLER(self, guildID, None)
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
