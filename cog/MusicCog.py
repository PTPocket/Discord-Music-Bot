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
SHORT_COMMANDS = ['p','play','pr','play_random','shuffle','prev','previous','s','skip','n','next', 'pause', 'resume','l','loop','r','reset','f','h','g','generate']
PREFIXS = ['!','/', '?']

class MusicCog(commands.Cog):
    def __init__(self, bot:commands.Bot, data:Guild_Music_Properties, gui_print:set, client_id, client_secret):
        self.bot = bot
        self.client_id = client_id
        self.client_secret = client_secret
        self.data = data
        self.gui_print = gui_print
        self.gui_loop.start()
        self.disconnect_check.start()
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
                self.gui_print.add(guildID)
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
                self.data.set_current(guildID, song)
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
            log(guildName, "now playing", f'\"{song["title"]} by {song['author']}\"')
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
        try:
            voice_client = await voice_connect(user, guildName, guildID, voice_client)
            if voice_client.is_playing() == voice_client.is_paused() == self.data.get_playing(guildID) == False:
                self.data.set_playing(guildID, True)
                log(guildName, 'MUSIC PLAYER', 'starting')
                self.music_player(guildName, guildID, voice_client)
        except Exception as e:
            error_log('music_player_start', e, guildName=guildName)
        
#######PLAY FUNCTIONS######################################################
    @app_commands.check(valid_play_command_slash)
    @app_commands.command(name= "play", description="Play Song or Playlist with the Title or Link (Spotify, YouTube, YTMusic)")
    async def play(self, interaction:discord.Interaction, title_or_link:str):
        user = interaction.user
        guildName = interaction.user.guild.name
        guildID = interaction.user.guild.id
        voice_client = interaction.client.get_guild(guildID).voice_client
        channelID = interaction.channel_id
        log(guildName, 'command', 'play')
        self.data.initialize(guildID)
        await interaction.response.defer(thinking=True)
        try:
            if 'music.youtube.com' in title_or_link:
                song_data = GetYTMusic(title_or_link)
                if type(song_data) == list:
                    song_data = GetYTMPlaylist(title_or_link)
                    if song_data is None:
                        msg = embed.invalid_link(self.bot, title_or_link, 'YTMusic Playlist')
                        await interaction.followup.send(embed= msg, ephemeral=True)
                        await GUI_HANDLER(self, guildID, channelID)
                        return
                    playlistType = 'YTMusic'
                    playlist_emb = queuePlaylist(guildName,guildID,song_data, playlistType,self.data)
                    msg = embed.queued_playlist_prompt(self.bot, playlist_emb, len(song_data), title_or_link, 'YTMusic')
                    await interaction.followup.send(embed=msg)
                    await self.music_player_start(user, guildName, guildID, voice_client)
                    await GUI_HANDLER(self, guildID, channelID)
                    return
                if type(song_data) == dict:
                    if song_data is None:
                        msg = embed.invalid_link(self.bot, title_or_link, 'YTMusic Song')
                        await interaction.followup.send(embed= msg, ephemeral=True)
                        await GUI_HANDLER(self, guildID, channelID)
                        return
                    self.data.add_song(guildID, song_data)
                    prompt = song_data['title'] + ' by ' + song_data['author']
                    log(guildName, "queued", f"{prompt} (ytmusic)" )
                    msg = embed.queue_prompt(self.bot, prompt)
                    await interaction.followup.send(embed= msg)
                    await self.music_player_start(user, guildName, guildID, voice_client)
                    await GUI_HANDLER(self, guildID, channelID)
                    return
                msg = embed.invalid_link(self.bot, title_or_link, 'YTMusic Song')
                await interaction.followup.send(embed= msg, ephemeral=True)
                error_log('play', 'invalid ytmusic link', title_or_link, guildName=guildName)
                return
            
            if 'youtube.com' in title_or_link:
                song_data = GetYT(title_or_link)
                if type(song_data) == dict:
                    if song_data is None:
                        msg = embed.invalid_link(self.bot, title_or_link, 'Youtube Song')
                        await interaction.followup.send(embed= msg, ephemeral=True)
                        await GUI_HANDLER(self, guildID, channelID)
                        return
                    self.data.add_song(guildID, song_data)
                    log(guildName, "QUEUED", f"{song_data['title']} (youtube)" )
                    msg = embed.queue_prompt(self.bot, song_data['title'])
                    await interaction.followup.send(embed= msg)
                    await self.music_player_start(user, guildName, guildID, voice_client)
                    await GUI_HANDLER(self, guildID, channelID)
                    return
                if type(song_data) == list:
                    if song_data is None:
                        msg = embed.invalid_link(self.bot, title_or_link, 'YT Playlist')
                        await interaction.followup.send(embed= msg, ephemeral=True)
                        await GUI_HANDLER(self, guildID, channelID)
                        return
                    playlistType = 'Youtube'
                    playlist_emb = queuePlaylist(guildName, guildID, song_data, playlistType, self.data)      
                    msg = embed.queued_playlist_prompt(self.bot, playlist_emb, len(song_data), title_or_link, 'Youtube')
                    await interaction.followup.send(embed = msg)              
                    await self.music_player_start(user, guildName, guildID, voice_client)
                    await GUI_HANDLER(self, guildID, channelID)
                    return
                msg = embed.invalid_link(self.bot, title_or_link, 'Youtube')
                await interaction.followup.send(embed= msg, ephemeral=True)
                await GUI_HANDLER(self, guildID, channelID)
                error_log('play', 'invalid youtube link', title_or_link, guildName=guildName)
                return
            
            if 'open.spotify.com' in title_or_link:
                song_data = GetSpotify(title_or_link, self.client_id, self.client_secret)
                if song_data is None:
                    msg = embed.invalid_link(self.bot, title_or_link, 'Spotify')
                    await interaction.followup.send(embed= msg, ephemeral=True)
                    await GUI_HANDLER(self, guildID, channelID)
                    return
                if type(song_data) is dict:
                    self.data.add_song(guildID, song_data)
                    full_title = song_data['title'] + ' by ' + song_data['author']
                    log(guildName, "QUEUED", f"{full_title} (spotify)" )
                    msg = embed.queue_prompt(self.bot, full_title)
                    await interaction.followup.send(embed= msg)
                    await self.music_player_start(user, guildName, guildID, voice_client)
                    await GUI_HANDLER(self, guildID, channelID)
                    return
                if type(song_data) is list:
                    playlistType = 'Spotify'
                    playlist = song_data
                    playlist_emb = queuePlaylist(guildName,guildID,playlist,playlistType,self.data)
                    msg = embed.queued_playlist_prompt(self.bot, playlist_emb, len(playlist), title_or_link, 'Spotify')
                    await interaction.followup.send(embed= msg)
                    await self.music_player_start(user, guildName, guildID, voice_client)
                    await GUI_HANDLER(self, guildID, channelID)
                    return
                
                msg = embed.invalid_link(self.bot, title_or_link, 'Spotify')
                await interaction.followup.send(embed= msg, ephemeral=True)
                await GUI_HANDLER(self, guildID, channelID)
                error_log('play', 'invalid spotify link', title_or_link, guildName=guildName)
                return

            if 'https://' in title_or_link:
                error_log('play', 'invalid link', title_or_link, guildName=guildName)
                msg = embed.invalid_link(self.bot, title_or_link)
                await interaction.followup.send(embed= msg, ephemeral=True)
                await GUI_HANDLER(self, guildID, channelID)
                return
            
            #title_or_link is not a link
            song = {
                'title' : title_or_link, 
                'author': None,
                'query' : title_or_link,
                'source': 'query'} 
            self.data.add_song(guildID, song)
            log(guildName, "QUEUED", f'{title_or_link} (query)')
            await interaction.followup.send(embed = embed.queue_prompt(self.bot, title_or_link))
            await self.music_player_start(user, guildName, guildID, voice_client)
            await GUI_HANDLER(self, guildID, channelID)
        except Exception as e:
            error_log('play', e, guildName=guildName)
    @app_commands.check(valid_play_command_slash)
    @app_commands.command(name= "play_random", description="Play random songs from pocket bot library forever")
    async def play_random(self, interaction:discord.Interaction): 
        try:
            user = interaction.user
            guildName = interaction.user.guild.name
            guildID = interaction.user.guild.id
            channelID = interaction.channel_id
            voice_client = interaction.client.get_guild(guildID).voice_client
            log(guildName, 'command', 'play_random')
            self.data.initialize(guildID)
            if self.data.switch_random(guildID) is True:
                log(guildName, 'RANDOM', 'On')
            else: 
                log(guildName, 'RANDOM', 'Off')
            await interaction.response.send_message(embed= embed.random_prompt(self.bot, self.data.get_random(guildID)))
            await self.music_player_start(user, guildName, guildID, voice_client)
            await GUI_HANDLER(self, guildID, channelID)
        except Exception as e:
            error_log('play_random', e)

    @app_commands.check(valid_command_slash)
    @app_commands.command(name= "skip", description="Skips song")
    async def skip(self, interaction:discord.Interaction):
        try:
            guildName = interaction.user.guild.name
            guildName = interaction.user.guild.name
            guildID = interaction.user.guild.id
            channelID = interaction.channel_id
            voice_client = interaction.client.get_guild(guildID).voice_client
            log(guildName, 'command', 'skip')
            self.data.initialize(guildID)
            self.data.set_loop(guildID, False)
            song= self.data.get_current(guildID)
            self.data.pos_forward(guildID)
            if song is None:
                await interaction.response.send_message(embed= embed.nothing_prompt(self.bot, 'skip'))
                await GUI_HANDLER(self, guildID, channelID)
                return
            song_name = f'{song['title']} by {song['author']}'
            if (voice_client.is_playing() or voice_client.is_paused()):
                voice_client.stop()
                await interaction.response.send_message(embed= embed.skip_prompt(self.bot, song_name))
                await GUI_HANDLER(self, guildID, channelID)
                return
            await interaction.response.send_message(embed= embed.skip_prompt(self.bot, song_name))
            await GUI_HANDLER(self, guildID, channelID)
        except Exception as e:
            error_log('skip', e)

    @app_commands.check(valid_command_slash)
    @app_commands.command(name= "next", description="Goes to next song")
    async def next(self, interaction:discord.Interaction):
        try:
            guildName = interaction.user.guild.name
            guildName = interaction.user.guild.name
            guildID = interaction.user.guild.id
            channelID = interaction.channel_id
            voice_client = interaction.client.get_guild(guildID).voice_client
            log(guildName, 'command', 'next')
            self.data.initialize(guildID)
            self.data.set_loop(guildID, False)
            song= self.data.get_current(guildID)
            self.data.pos_forward(guildID)
            if song is None:
                await interaction.response.send_message(embed= embed.nothing_prompt(self.bot, 'skip'))
                await GUI_HANDLER(self, guildID, channelID)
                return
            song_name = f'{song['title']} by {song['author']}'
            if (voice_client.is_playing() or voice_client.is_paused()):
                voice_client.stop()
                await interaction.response.send_message(embed= embed.skip_prompt(self.bot, song_name))
                await GUI_HANDLER(self, guildID, channelID)
                return
            await interaction.response.send_message(embed= embed.skip_prompt(self.bot, song_name))
            await GUI_HANDLER(self, guildID, channelID)
        except Exception as e:
            error_log('next', e)
    
    @app_commands.check(valid_command_slash)
    @app_commands.command(name= "previous", description="Previous song")
    async def previous(self, interaction:discord.Interaction):
        try:
            user = interaction.user
            guildName = interaction.user.guild.name
            guildID = interaction.user.guild.id
            channelID = interaction.channel_id
            voice_client = interaction.client.get_guild(guildID).voice_client
            log(guildName, 'COMMAND', 'previous')
            self.data.initialize(guildID)
            self.data.pos_backward(guildID)
            self.data.set_loop(guildID, False)
            song= self.data.get_current(guildID) 
            song_name = f'{song['title']} by {song['author']}'
            if voice_client.is_playing() or voice_client.is_paused():
                voice_client.stop()
                await interaction.response.send_message(embed= embed.previous_prompt(self.bot, song_name))
                await GUI_HANDLER(self, guildID, channelID)
                return
            await interaction.response.send_message(embed= embed.previous_prompt(self.bot, song_name))
            await GUI_HANDLER(self, guildID, channelID)
            await self.music_player_start(user, guildName, guildID, voice_client)
            return
        except Exception as e:
            error_log('previous', e, guildName= guildName)

    @app_commands.check(valid_command_slash)
    @app_commands.command(name= "pause", description="Pause song")
    async def pause(self, interaction:discord.Interaction):
        try:
            guildName = interaction.user.guild.name
            guildID = interaction.user.guild.id
            channelID = interaction.channel_id
            voice_client = interaction.client.get_guild(guildID).voice_client
            log(guildName, 'COMMAND', 'pause')
            self.data.initialize(guildID)
            if voice_client.is_playing() and not voice_client.is_paused():
                song = self.data.get_current(guildID)
                song_name = f'{song['title']} by {song['author']}'
                log(guildName, 'PAUSED', song_name)
                voice_client.pause()
                await interaction.response.send_message(embed= embed.pause_prompt(self.bot, song_name))
                await GUI_HANDLER(self, guildID, channelID)
                return
            await interaction.response.send_message(embed= embed.nothing_prompt(self.bot, 'Pause'))
            await GUI_HANDLER(self, guildID, channelID)
        except Exception as e:
            error_log('pause', e)
        await interaction.delete_original_response()

    @app_commands.check(valid_command_slash)
    @app_commands.command(name= "resume", description="Resume song")
    async def resume(self, interaction:discord.Interaction):
        try:
            guildName = interaction.user.guild.name
            guildID = interaction.user.guild.id
            channelID = interaction.channel_id
            voice_client = interaction.client.get_guild(guildID).voice_client
            log(guildName, 'COMMAND', 'previous')
            self.data.initialize(guildID)
            if not voice_client.is_playing() and voice_client.is_paused():
                song = self.data.get_current(guildID)
                song_name = f'{song['title']} by {song['author']}'
                log(guildName, 'RESUME', song_name)
                voice_client.resume()
                await interaction.response.send_message(embed= embed.resume_prompt(self.bot, song_name))
                await GUI_HANDLER(self, guildID, channelID)
                return
            await interaction.response.send_message(embed= embed.nothing_prompt(self.bot, 'resume'))
            await GUI_HANDLER(self, guildID, channelID)
        except Exception as e:
            error_log('RESUME', e)

    @app_commands.check(valid_command_slash)
    @app_commands.command(name= "shuffle", description="Shuffle song")
    async def shuffle(self, interaction:discord.Interaction):
        try:
            user = interaction.user
            guildName = interaction.user.guild.name
            guildID = interaction.user.guild.id
            channelID = interaction.channel_id
            voice_client = interaction.client.get_guild(guildID).voice_client
            log(guildName, 'COMMAND', 'shuffle')
            self.data.initialize(guildID)
            current_song = self.data.get_current(guildID)
            library = self.data.get_queue(guildID)+self.data.get_history(guildID)
            if library == [] and current_song is None:
                await interaction.response.send_message(embed= embed.nothing_prompt('shuffle'))
                await GUI_HANDLER(self, guildID, channelID)
                return
            random.shuffle(library)
            if current_song is not None:
                library.insert(0, current_song)
            self.data.set_new_library(guildID, library)
            await interaction.response.send_message(embed= embed.shuffle_prompt(self.bot))
            await GUI_HANDLER(self, guildID, channelID)
            await self.music_player_start(user, guildName, guildID, voice_client)
        except Exception as e:
            error_log('shuffle', e, guildName= guildName)

    @app_commands.check(valid_command_slash)
    @app_commands.command(name= "loop", description="Loop current song")
    async def loop(self, interaction:discord.Interaction):
        try:
            guildName = interaction.user.guild.name
            guildID = interaction.user.guild.id
            channelID = interaction.channel_id
            voice_client = interaction.client.get_guild(guildID).voice_client
            log(guildName, 'COMMAND', 'loop')
            self.data.initialize(guildID)
            if voice_client.is_playing() or voice_client.is_paused():
                song = self.data.get_current(guildID)
                self.data.switch_loop(guildID)
                self.data.set_random(guildID, False)
                loop_var = self.data.get_loop(guildID)
                if loop_var is True:
                    log(guildName, 'now looping', f'{song['title']} by {song['author']}')
                else:
                    log(guildName, 'stopped looping', f'{song['title']} by {song['author']}')
            loop_var = self.data.get_loop(guildID)
            song= self.data.get_current(guildID) 
            song_name = f'{song['title']} by {song['author']}'            
            await interaction.response.send_message(embed= embed.loop_prompt(self.bot, loop_var, song_name))
            await GUI_HANDLER(self, guildID, channelID)
            return
        except Exception as e:
            error_log('loop', e, guildName= guildName)
    
    @app_commands.check(valid_command_slash)
    @app_commands.command(name= "flush", description="Empty current data and stop music player")
    async def flush(self, interaction:discord.Interaction):
        try:
            guildName = interaction.user.guild.name
            guildID = interaction.user.guild.id
            channelID = interaction.channel_id
            voice_client = interaction.client.get_guild(guildID).voice_client
            log(guildName, 'COMMAND', 'flush')
            self.data.initialize(guildID)
            self.data.reset(guildID)
            if voice_client.is_playing() or voice_client.is_paused():
                voice_client.stop()
            self.data.full_reset(guildID)
            await interaction.response.send_message(embed= embed.flush_prompt(self.bot))
            await GUI_HANDLER(self, guildID, channelID)
        except Exception as e:
            error_log('flush', e, guildName= guildName)

    @app_commands.check(valid_command_slash)
    @app_commands.command(name= "reset", description="Full reset bot")
    async def reset(self, interaction:discord.Interaction):
        try:
            guildName = interaction.user.guild.name
            guildID = interaction.user.guild.id
            channelID = interaction.channel_id
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
            await interaction.response.send_message(embed= embed.reset_prompt(self.bot))
            await GUI_HANDLER(self, guildID, channelID)
        except Exception as e:
            error_log('reset', e, guildName= guildName)

    @app_commands.command(name= "help", description="Shows bot use information")
    async def help(self, interaction:discord.Interaction):
        guildName = interaction.user.guild.name
        guildID = interaction.user.guild.id
        channelID = interaction.channel_id
        log(guildName, 'command', 'help')
        self.data.initialize(guildID)
        msg = embed.HelpPrompt(self.bot)
        await interaction.response.send_message(embed= msg)
        await asyncio.sleep(Setting.get_helpPromptDelay())
        await GUI_HANDLER(self,guildID, channelID)

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
            helpEmb = embed.HelpPrompt(self.bot)
            await channel.send(embed=helpEmb)
            await GUI_HANDLER(self, guildID, channel.id)
            await interaction.response.send_message(embed=embed.generated_prompt(self.bot))
        except Exception as e:
            error_log('generate_ctx', e)


  #@commands.check(valid_play_command_slash2)
    @commands.command(aliases = ['p','P', 'play','PLAY'])
    async def play_ctx(self, ctx:commands.context.Context):
        title_or_link = ctx.message.content.strip()[3:]
        user = ctx.author
        guildName = str(ctx.guild)
        guildID = ctx.guild.id
        channelID = ctx.channel.id
        voice_client = self.bot.get_guild(guildID).voice_client
        log(guildName, 'command', 'play')
        self.data.initialize(guildID)
        if await valid_play_command_ctx(self.bot, ctx) is False:return
        if title_or_link == '' or title_or_link.count(' ') == len(title_or_link):
            msg = embed.no_query_prompt(self.bot)
            await ctx.send(embed = msg, ephemeral = True)
            await GUI_HANDLER(self, guildID, channelID)
            return
        try:
            if 'music.youtube.com' in title_or_link:
                song_data = GetYTMusic(title_or_link)
                if type(song_data) == list:
                    if song_data is None:
                        msg = embed.invalid_link(self.bot, title_or_link, 'YTMusic Playlist')
                        await ctx.send(embed= msg, ephemeral=True)
                        await GUI_HANDLER(self, guildID, channelID)
                        return
                    playlistType = 'YTMusic'
                    playlist_emb = queuePlaylist(guildName,guildID,song_data,playlistType,self.data)
                    msg = embed.queued_playlist_prompt(self.bot, playlist_emb, len(song_data), title_or_link, 'YTMusic')
                    await ctx.send(embed=msg)
                    await self.music_player_start(user, guildName, guildID, voice_client)
                    await GUI_HANDLER(self, guildID, channelID)                    
                    return
                if '/watch?v=' in title_or_link:
                    song_data = GetYTMSong(title_or_link)
                    if song_data is None:
                        msg = embed.invalid_link(self.bot, title_or_link, 'YTMusic Song')
                        await ctx.send(embed= msg, ephemeral=True)
                        await GUI_HANDLER(self, guildID, channelID)
                        return
                    self.data.add_song(guildID, song_data)
                    prompt = song_data['title'] + ' by ' + song_data['author']
                    log(guildName, "queued", f"{prompt} (ytmusic)" )
                    msg = embed.queue_prompt(self.bot, prompt)
                    await ctx.send(embed= msg)
                    await self.music_player_start(user, guildName, guildID, voice_client)
                    await GUI_HANDLER(self, guildID, channelID)
                    return
                msg = embed.invalid_link(self.bot, title_or_link, 'YTMusic Song')
                await ctx.send(embed= msg, ephemeral=True)
                error_log('play_tc', 'invalid ytmusic link', title_or_link, guildName=guildName)
                await GUI_HANDLER(self, guildID, channelID)
                return
            
            if 'youtube.com/' in title_or_link:
                song_data = GetYT(title_or_link)
                if type(song_data) == dict:
                    if song_data is None:
                        msg = embed.invalid_link(self.bot, title_or_link, 'Youtube Song')
                        await ctx.send(embed= msg, ephemeral=True)
                        await GUI_HANDLER(self, guildID, channelID)
                        return
                    self.data.add_song(guildID, song_data)
                    full_title = song_data['title'] + ' by ' + song_data['author']
                    log(guildName, "QUEUED", f"{full_title} (youtube)" )
                    msg = embed.queue_prompt(self.bot, full_title)
                    await ctx.send(embed= msg)
                    await self.music_player_start(user, guildName, guildID, voice_client)
                    await GUI_HANDLER(self, guildID, channelID)
                    return
                if type(song_data) == list:
                    if song_data is None:
                        msg = embed.invalid_link(self.bot, title_or_link, 'YT Playlist')
                        await ctx.send(embed= msg, ephemeral=True)
                        await GUI_HANDLER(self, guildID, channelID)
                        return
                    playlistType = 'Youtube'
                    playlist_emb = queuePlaylist(guildName,guildID, song_data, playlistType, self.data)                    
                    msg = embed.queued_playlist_prompt(self.bot, playlist_emb, len(song_data), title_or_link, 'Youtube')
                    await ctx.send(embed = msg)
                    await self.music_player_start(user, guildName, guildID, voice_client)
                    await GUI_HANDLER(self, guildID, channelID)
                    return
                msg = embed.invalid_link(self.bot, title_or_link, 'Youtube')
                await ctx.send(embed= msg, ephemeral=True)
                error_log('play_tc', 'invalid youtube link', title_or_link, guildName=guildName)
                await GUI_HANDLER(self, guildID, channelID)
                return
            
            if 'open.spotify.com' in title_or_link:
                song_data = GetSpotify(title_or_link, self.client_id, self.client_secret)
                if song_data is None:
                    msg = embed.invalid_link(self.bot, title_or_link, 'Spotify')
                    await ctx.send(embed= msg, ephemeral=True)
                    await GUI_HANDLER(self, guildID, channelID)
                    return
                if type(song_data) is dict:
                    self.data.add_song(guildID, song_data)
                    full_title = song_data['title'] + ' by ' + song_data['author']
                    log(guildName, "QUEUED", f"{full_title} (spotify)" )
                    msg = embed.queue_prompt(self.bot, full_title)
                    await ctx.send(embed= msg)
                    await self.music_player_start(user, guildName, guildID, voice_client)
                    await GUI_HANDLER(self, guildID, channelID)
                    return
                if type(song_data) is list:
                    playlistType = 'Spotify'
                    playlist = song_data
                    playlist_emb = queuePlaylist(guildName,guildID,playlist,playlistType,self.data)
                    msg = embed.queued_playlist_prompt(self.bot, playlist_emb, len(playlist), title_or_link, 'Spotify')
                    await ctx.send(embed= msg)
                    await self.music_player_start(user, guildName, guildID, voice_client)
                    await GUI_HANDLER(self, guildID, channelID)
                    return
                
                msg = embed.invalid_link(self.bot, title_or_link, 'Spotify')
                await ctx.send(embed= msg, ephemeral=True)
                error_log('play_tc', 'invalid spotify link', title_or_link, guildName=guildName)
                await GUI_HANDLER(self, guildID, channelID)
                return

            if 'https://' in title_or_link:
                msg = embed.invalid_link(self.bot, title_or_link)
                await ctx.send(embed= msg, ephemeral=True)
                error_log('play_tc', 'invalid link', title_or_link, guildName=guildName)
                await GUI_HANDLER(self, guildID, channelID)
                return
            
            #title_or_link is not a link
            song = {
                'title' : title_or_link, 
                'author': None,
                'query' : title_or_link,
                'source': 'query'} 
            self.data.add_song(guildID, song)
            log(guildName, "QUEUED", f'{title_or_link} (query)')
            msg = embed.queue_prompt(self.bot, title_or_link)
            await ctx.send(embed = msg)
            await self.music_player_start(user, guildName, guildID, voice_client)
            await GUI_HANDLER(self, guildID, channelID)
            return
        except Exception as e:
            error_log('play_tc', e, guildName=guildName)

    @commands.command(aliases = ['pr','PR', 'play_random', 'PLAY_RANDOM'])
    async def play_random_ctx(self, ctx:commands.context.Context):
        try:
            user = ctx.author
            guildName = str(ctx.guild)
            guildID = ctx.guild.id
            voice_client = self.bot.get_guild(guildID).voice_client
            channelID = ctx.channel.id
            log(guildName, 'command', 'play_random_tc')
            self.data.initialize(guildID)
            if await valid_play_command_ctx(self.bot,ctx) is False:return
            if self.data.switch_random(guildID) is True:
                log(guildName, 'RANDOM', 'On')
            else: 
                log(guildName, 'RANDOM', 'Off')
            await ctx.send(embed = embed.random_prompt(self.bot, self.data.get_random(guildID)))
            await self.music_player_start(user, guildName, guildID, voice_client)
            await GUI_HANDLER(self, guildID, channelID)
        except Exception as e:
            error_log('play_random_tc', e, guildName=guildName)
    
    @commands.command(aliases = ['shuffle', 'SHUFFLE'])
    async def shuffle_ctx(self, ctx:commands.context.Context):
        try:
            user = ctx.author
            guildName = str(ctx.guild)
            guildID = ctx.guild.id
            voice_client = self.bot.get_guild(guildID).voice_client
            channelID = ctx.channel.id
            log(guildName, 'command', 'shuffle_ctx')
            self.data.initialize(guildID)
            if await valid_command_ctx(self.bot, ctx) is False : return
            song = self.data.get_current(guildID)
            library = self.data.get_queue(guildID)+self.data.get_history(guildID)
            if library == [] and song is None:
                await ctx.send(embed= embed.nothing_prompt('shuffle'))
                await GUI_HANDLER(self, guildID, channelID)
                return
            random.shuffle(library)
            if song is not None:
                library.insert(0, song)
            self.data.set_new_library(guildID, library)
            if self.data.get_playing(guildID) is True:
                await ctx.send(embed= embed.shuffle_prompt(self.bot))
                await GUI_HANDLER(self, guildID, channelID)
                return
            await ctx.send(embed= embed.shuffle_prompt(self.bot))
            await self.music_player_start(user, guildName, guildID, voice_client)
            
            await GUI_HANDLER(self, guildID, channelID)
        except Exception as e:
            error_log('shuffle_ctx', e)
    
    @commands.command(aliases = ['prev', 'PREV', 'previous', 'PREVIOUS'])
    async def previous_ctx(self, ctx:commands.context.Context):
        try:
            user = ctx.author
            guildName = str(ctx.guild)
            guildID = ctx.guild.id
            channelID = ctx.channel.id
            voice_client = self.bot.get_guild(guildID).voice_client
            log(guildName, 'COMMAND', 'previous_ctx')
            self.data.initialize(guildID)
            if await valid_command_ctx(self.bot, ctx) is False:return
            self.data.pos_backward(guildID)
            self.data.set_loop(guildID, False)
            song= self.data.get_current(guildID) 
            if song is None:
                await ctx.send(embed= embed.nothing_prompt(self.bot, 'Go Back To'))
                await GUI_HANDLER(self, guildID, channelID)
                return
            song_name = f'{song['title']} by {song['author']}'
            if voice_client.is_playing() or voice_client.is_paused():
                voice_client.stop()
                await ctx.send(embed= embed.previous_prompt(self.bot, song_name))
                await GUI_HANDLER(self, guildID, channelID)
                return
            await ctx.send(embed= embed.previous_prompt(self.bot, song_name))
            await self.music_player_start(user, guildName, guildID, voice_client)

            await GUI_HANDLER(self, guildID, channelID)
        except Exception as e:
            error_log('previous_ctx', e, guildName= guildName)
    
    @commands.command(aliases = ['s','S', 'skip', 'SKIP', 'n', 'N', 'next', 'NEXT'])
    async def skip_ctx(self, ctx:commands.context.Context):
        try:
            guildName = str(ctx.guild)
            guildID = ctx.guild.id
            voice_client = self.bot.get_guild(guildID).voice_client
            channelID = ctx.channel.id
            log(guildName, 'command', 'skip_ctx')
            self.data.initialize(guildID)
            if await valid_command_ctx(self.bot, ctx) is False:return
            song= self.data.get_current(guildID)
            self.data.pos_forward(guildID)
            if song is None:
                await ctx.send(embed= embed.nothing_prompt(self.bot, 'skip'))
                await GUI_HANDLER(self, guildID, channelID)
                return
            song_name = f'{song['title']} by {song['author']}'
            if (voice_client.is_playing() or voice_client.is_paused()):
                song = self.data.get_current(guildID)
                self.data.set_loop(guildID, False)
                voice_client.stop()
                log(guildName, 'skipped', song_name)
                await ctx.send(embed= embed.skip_prompt(self.bot, song_name))
                await GUI_HANDLER(self, guildID, channelID)
                return
            await ctx.send(embed= embed.skip_prompt(self.bot, song_name))
            
            await GUI_HANDLER(self, guildID, channelID)
        except Exception as e:
            error_log('skip_ctx', e)

    @commands.command(aliases = ['pause', 'PAUSE'])
    async def pause_ctx(self, ctx:commands.context.Context):
        try:
            guildName = str(ctx.guild)
            guildID = ctx.guild.id
            channelID = ctx.channel.id
            voice_client = self.bot.get_guild(guildID).voice_client
            log(guildName, 'COMMAND', 'pause_ctx')
            self.data.initialize(guildID)
            if await valid_command_ctx(self.bot, ctx) is False:return
            if voice_client.is_playing() and not voice_client.is_paused():
                song = self.data.get_current(guildID)
                song_name = f'{song['title']} by {song['author']}'
                log(guildName, 'PAUSED', song_name)
                voice_client.pause()
                await ctx.send(embed= embed.pause_prompt(self.bot, song_name))
                await GUI_HANDLER(self, guildID, channelID)
                return
            await ctx.send(embed= embed.nothing_prompt(self.bot, 'Pause'))
            
            await GUI_HANDLER(self, guildID, channelID)
            
        except Exception as e:
            error_log('pause_ctx', e, guildName=guildName)
            
    @commands.command(aliases = ['resume', 'RESUME'])
    async def resume_ctx(self, ctx:commands.context.Context):
        try:
            guildName = str(ctx.guild)
            guildID = ctx.guild.id
            channelID = ctx.channel.id
            voice_client = self.bot.get_guild(guildID).voice_client
            log(guildName, 'COMMAND', 'resume_ctx')
            self.data.initialize(guildID)
            if await valid_command_ctx(self.bot, ctx) is False:return
            if not voice_client.is_playing() and voice_client.is_paused():
                song = self.data.get_current(guildID)
                song_name = f'{song['title']} by {song['author']}'
                log(guildName, 'resume_ctx', song_name)
                voice_client.resume()
                await ctx.send(embed= embed.resume_prompt(self.bot, song_name))
                
                await GUI_HANDLER(self, guildID, channelID)
                return
            await ctx.send(embed= embed.nothing_prompt(self.bot, 'Resume'))
            
            await GUI_HANDLER(self, guildID, channelID)
        except Exception as e:
            error_log('resume_ctx', e, guildName= guildName)

    @commands.command(aliases = ['l', 'L', 'loop', 'Loop'])
    async def loop_ctx(self, ctx:commands.context.Context):
        try:
            guildName = str(ctx.guild)
            guildID = ctx.guild.id
            channelID = ctx.channel.id
            voice_client = self.bot.get_guild(guildID).voice_client
            log(guildName, 'COMMAND', 'loop_ctx')
            self.data.initialize(guildID)
            if await valid_command_ctx(self.bot, ctx) is False:return
            if voice_client.is_playing() or voice_client.is_paused():
                song = self.data.get_current(guildID)
                self.data.switch_loop(guildID)
                self.data.set_random(guildID, False)
                loop_var = self.data.get_loop(guildID)
                if loop_var is True:
                    log(guildName, 'now looping', f'{song['title']} by {song['author']}')
                else:
                    log(guildName, 'stopped looping', f'{song['title']} by {song['author']}')
                loop_var = self.data.get_loop(guildID)
                song= self.data.get_current(guildID) 
                song_name = f'{song['title']} by {song['author']}'            
                await ctx.send(embed= embed.loop_prompt(self.bot, loop_var, song_name))
                
                await GUI_HANDLER(self, guildID, channelID)
                return
            await ctx.send(embed= embed.nothing_prompt(self.bot, 'loop'))
            
            await GUI_HANDLER(self, guildID, channelID)
        except Exception as e:
            error_log('loop_ctx', e, guildName= guildName)
    
    @commands.command(aliases = ['r', 'R', 'reset','RESET'])
    async def reset_ctx(self, ctx:commands.context.Context):
        try:
            guildName = str(ctx.guild)
            guildID = ctx.guild.id
            channelID = ctx.channel.id
            voice_client = self.bot.get_guild(guildID).voice_client
            log(guildName, 'command', 'reset_ctx')
            self.data.initialize(guildID)
            if await valid_play_command_ctx(self.bot,ctx) is False:
                return
            self.data.full_reset(guildID)
            if voice_client is not None:
                channel_name = voice_client.channel.name
                if voice_client.is_playing() or voice_client.is_paused():
                    voice_client.stop()
                await voice_client.disconnect()
                log(guildName, 'DISCONNECTED (force)', channel_name)
            self.data.full_reset(guildID)
            await ctx.send(embed= embed.reset_prompt(self.bot))
            
            await GUI_HANDLER(self, guildID, channelID)
        except Exception as e:
            error_log('reset_ctx', e, guildName= guildName)

    @commands.command(aliases = ['f','F'])
    async def flush_ctx(self, ctx:commands.context.Context):
        try:
            guildName = str(ctx.guild)
            guildID = ctx.guild.id
            channelID = ctx.channel.id
            voice_client = self.bot.get_guild(guildID).voice_client
            log(guildName, 'command', 'flush_ctx')
            self.data.initialize(guildID)
            if await valid_play_command_ctx(self.bot,ctx) is False:
                return
            self.data.reset(guildID)
            if voice_client is not None:
                if voice_client.is_playing() or voice_client.is_paused():
                    voice_client.stop()
            self.data.full_reset(guildID)
            msg = embed.flush_prompt(self.bot)
            await ctx.send(embed=msg)
            
            await GUI_HANDLER(self, guildID, channelID)
        except Exception as e:
            error_log('flush_ctx', e, guildName= guildName)

    @commands.command(aliases = ['h','H'])
    async def help_ctx(self, ctx:commands.context.Context):
        guildName = str(ctx.guild)
        guildID = ctx.guild.id
        channelID = ctx.channel.id
        log(guildName, 'command', 'help_ctx')
        self.data.initialize(guildID)
        msg = embed.HelpPrompt(self.bot)
        await ctx.send(embed= msg)
        await asyncio.sleep(Setting.get_helpPromptDelay())
        await GUI_HANDLER(self,guildID, channelID)

    @commands.command(aliases = ['g','generate'])
    async def generate_ctx(self, ctx:commands.context.Context):
        try:
            guildID = ctx.guild.id
            guildName = str(ctx.guild)
            log(guildName, 'command', 'generate_ctx')
            self.data.initialize(guildID)
            channel = await create_bot_channel(self.data, ctx.guild)
            if channel is None: 
                await ctx.send(embed=embed.already_generated_prompt())
                return
            helpEmb = embed.HelpPrompt(self.bot)
            await channel.send(embed=helpEmb)
            await GUI_HANDLER(self, guildID, channel.id)
            await ctx.send(embed=embed.generated_prompt(self.bot))
        except Exception as e:
            error_log('generate_ctx', e)

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
            and message.channel.id == Setting.get_channelID(guildID)\
            and prefix not in PREFIXS\
            and com not in SHORT_COMMANDS:
            await GUI_HANDLER(self, guildID, message.channel.id)

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
                print('here')
                return
            helpEmb = embed.HelpPrompt(self.bot)
            await channel.send(embed=helpEmb)
            await GUI_HANDLER(self, guildID, channel.id)
        except Exception as e:
            print(e)


######## LOOP TO AUTO CHANGE GUI ##############################################################
    @tasks.loop(seconds = 5)
    async def gui_loop(self):
        try:
            while self.gui_print:
                guildID = self.gui_print.pop()
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
        except Exception as e:
            print(e)
