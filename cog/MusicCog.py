import discord, time
from discord                import app_commands, FFmpegPCMAudio
from discord.ext            import commands, tasks
from cog.helper             import embed
from cog.helper.GuildData   import Guild_Music_Properties

from cog.helper.Log         import *
from cog.helper.Functions   import *
from cog.helper.MusicSearch import *
import cog.helper.Setting   as     Setting

FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
FFMPEG_LOC = "C:\\Users\\p\\Downloads\\ffmpeg\\bin\\ffmpeg.exe"
LOCAL_MUSIC_PATH = "C:\\Users\\p\\Documents\\SERVER\\music\\Formatted"

SHORT_COMMANDS = ['p','play','s','skip','pre','previous', 'pause', 'resume','shuffle','pr', 'play_random','r','reset','f','h']
PREFIXS = ['!','/', '?']

class MusicCog(commands.Cog):
    def __init__(self, bot:commands.Bot, data:Guild_Music_Properties, gui_print, client_id, client_secret):
        self.bot = bot
        self.client_id = client_id
        self.client_secret = client_secret
        self.data = data
        self.gui_print = gui_print
        self.gui_loop.start()
        self.disconnect_check.start()

    #MUSIC PLAYER LOOP (not recursive)
    def music_player(self, guildName, guildID, voice_client, recall = False):
        try:
            if recall is True:
                self.data.current_to_history(guildID)
            check_features(self.data, guildID)
            if self.data.empty_queue(guildID):
                self.data.set_idle_timestamp(guildID)
                self.gui_print.add(guildID)
                log(guildName, 'music player', 'finished')
                return
            #Moves song from queue to current
            self.data.queue_to_current(guildID)
            song = self.data.get_current_song(guildID)

            if song['source'] == 'local':
                player = FFmpegPCMAudio(
                    song['url'],
                    executable=FFMPEG_LOC)
            elif song['source'] == 'query':
                query = song['query']
                song = SearchYoutube(query)
                self.data.set_current_song(guildID, song)
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
            voice_client.play(player, after= lambda x=None: self.music_player(guildName, guildID, voice_client, recall=True))
            return False
        except Exception as e:
            error_log('music_player', e, song['title'], guildName=guildName)
            self.data.set_current_song(guildID, None)
            self.music_player(guildName, guildID, voice_client, recall=True)
            return True
    #CHECKS IF MUSIC_PLAYER LOOP SHOULD START
    async def music_player_start(self, user, guildName, guildID, voice_client, channel, edit = False):
        voice_client = await voice_connect(user, guildName, guildID, voice_client)
        self.data.set_channel(guildID, channel)
        play_error = False
        if voice_client.is_playing() == voice_client.is_paused() == False and self.data.get_current_song(guildID) is None:
            log(guildName, 'MUSIC PLAYER', 'starting')
            play_error = self.music_player(guildName, guildID, voice_client)

        await GUI_HANDLER(self, guildID, edit= edit, error= play_error)
    
#######PLAY FUNCTIONS######################################################
    @app_commands.check(valid_play_command)
    @app_commands.command(name= "play", description="Play Song or Playlist with the Title or Link (Spotify, YouTube, YTMusic)")
    async def play(self, interaction:discord.Interaction, title_or_link:str):
        user = interaction.user
        guildName = interaction.user.guild.name
        guildID = interaction.user.guild.id
        voice_client = interaction.client.get_guild(guildID).voice_client
        channel = interaction.channel
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
                        await interaction.delete_original_response()
                        await interaction.followup.send(embed= msg, ephemeral=True)
                        return
                    playlistType = 'YTMusic'
                    playlist_emb = queuePlaylist(guildName,guildID,song_data, playlistType,self.data)
                    msg = embed.queued_playlist_prompt(self.bot, playlist_emb, len(song_data), title_or_link, 'YTMusic')
                    await interaction.delete_original_response()
                    await interaction.channel.send(embed=msg)
                    await self.music_player_start(user, guildName, guildID, voice_client, channel)
                    return
                if type(song_data) == dict:
                    if song_data is None:
                        msg = embed.invalid_link(self.bot, title_or_link, 'YTMusic Song')
                        await interaction.followup.send(embed= msg, ephemeral=True)
                        return
                    self.data.queue_song(guildID, song_data)
                    prompt = song_data['title'] + ' by ' + song_data['author']
                    log(guildName, "queued", f"{prompt} (ytmusic)" )
                    msg = embed.queue_prompt(self.bot, prompt)
                    await interaction.delete_original_response()
                    await interaction.followup.send(embed= msg)
                    await self.music_player_start(user, guildName, guildID, voice_client, channel)
                    return
                msg = embed.invalid_link(self.bot, title_or_link, 'YTMusic Song')
                await interaction.delete_original_response()
                await interaction.followup.send(embed= msg, ephemeral=True)
                error_log('play', 'invalid ytmusic link', title_or_link, guildName=guildName)
                return
            
            if 'youtube.com' in title_or_link:
                song_data = GetYT(title_or_link)
                if type(song_data) == dict:
                    if song_data is None:
                        msg = embed.invalid_link(self.bot, title_or_link, 'Youtube Song')
                        await interaction.followup.send(embed= msg, ephemeral=True)
                        return
                    self.data.queue_song(guildID, song_data)
                    log(guildName, "QUEUED", f"{song_data['title']} (youtube)" )
                    msg = embed.queue_prompt(self.bot, song_data['title'])
                    await interaction.delete_original_response()
                    await interaction.followup.send(embed= msg)
                    await self.music_player_start(user, guildName, guildID, voice_client, channel)
                    return
                if type(song_data) == list:
                    if song_data is None:
                        msg = embed.invalid_link(self.bot, title_or_link, 'YT Playlist')
                        await interaction.followup.send(embed= msg, ephemeral=True)
                        return
                    playlistType = 'Youtube'
                    playlist_emb = queuePlaylist(guildName, guildID, song_data, playlistType, self.data)      
                    msg = embed.queued_playlist_prompt(self.bot, playlist_emb, len(song_data), title_or_link, 'Youtube')
                    await interaction.delete_original_response()
                    await interaction.followup.send(embed = msg)              
                    await self.music_player_start(user, guildName, guildID, voice_client, channel)
                    return
                msg = embed.invalid_link(self.bot, title_or_link, 'Youtube')
                await interaction.delete_original_response()
                await interaction.followup.send(embed= msg, ephemeral=True)
                error_log('play', 'invalid youtube link', title_or_link, guildName=guildName)
                return
            
            if 'open.spotify.com' in title_or_link:
                song_data = GetSpotify(title_or_link, self.client_id, self.client_secret)
                if song_data is None:
                    msg = embed.invalid_link(self.bot, title_or_link, 'Spotify')
                    await interaction.delete_original_response()
                    await interaction.followup.send(embed= msg, ephemeral=True)
                    return
                if type(song_data) is dict:
                    self.data.queue_song(guildID, song_data)
                    full_title = song_data['title'] + ' by ' + song_data['author']
                    log(guildName, "QUEUED", f"{full_title} (spotify)" )
                    msg = embed.queue_prompt(self.bot, full_title)
                    await interaction.delete_original_response()
                    await interaction.followup.send(embed= msg)
                    await self.music_player_start(user, guildName, guildID, voice_client, channel)
                    return
                if type(song_data) is list:
                    playlistType = 'Spotify'
                    playlist = song_data
                    playlist_emb = queuePlaylist(guildName,guildID,playlist,playlistType,self.data)
                    msg = embed.queued_playlist_prompt(self.bot, playlist_emb, len(playlist), title_or_link, 'Spotify')
                    await interaction.delete_original_response()
                    await interaction.followup.send(embed= msg)
                    await self.music_player_start(user, guildName, guildID, voice_client, channel)
                    return
                
                msg = embed.invalid_link(self.bot, title_or_link, 'Spotify')
                await interaction.delete_original_response()
                await interaction.followup.send(embed= msg, ephemeral=True)
                error_log('play', 'invalid spotify link', title_or_link, guildName=guildName)
                return

            if 'https://' in title_or_link:
                msg = embed.invalid_link(self.bot, title_or_link)
                await interaction.delete_original_response()
                await interaction.followup.send(embed= msg, ephemeral=True)
                error_log('play', 'invalid link', title_or_link, guildName=guildName)
                return
            
            #title_or_link is not a link
            song = {
                'title' : title_or_link, 
                'author': None,
                'query' : title_or_link,
                'source': 'query'} 
            self.data.queue_song(guildID, song)
            log(guildName, "QUEUED", f'{title_or_link} (query)')
            msg = embed.queue_prompt(self.bot, title_or_link)
            await interaction.delete_original_response()
            await interaction.followup.send(embed = msg)
            await self.music_player_start(user, guildName, guildID, voice_client, channel)
        except Exception as e:
            error_log('play', e, guildName=guildName)
            await interaction.delete_original_response()

    @app_commands.check(valid_play_command)
    @app_commands.command(name= "play_random", description="Play random songs from pocket bot library forever")
    async def play_random(self, interaction:discord.Interaction): 
        user = interaction.user
        guildName = interaction.user.guild.name
        guildID = interaction.user.guild.id
        voice_client = interaction.client.get_guild(guildID).voice_client
        channel = interaction.channel
        log(guildName, 'command', 'play_random_sc')
        await interaction.response.defer()
        self.data.initialize(guildID)
        if self.data.flip_random(guildID) is True:
            log(guildName, 'RANDOM', 'On')
        else: 
            log(guildName, 'RANDOM', 'Off')
        await self.music_player_start(user, guildName, guildID, voice_client, channel)
        await interaction.delete_original_response()

    @app_commands.check(valid_user_REGULAR_FUNC)
    @app_commands.command(name= "skip", description="Skips song")
    async def skip(self, interaction:discord.Interaction):
        guildName = interaction.user.guild.name
        log(guildName, 'command', 'skip')
        guildName = interaction.user.guild.name
        guildID = interaction.user.guild.id
        voice_client = interaction.client.get_guild(guildID).voice_client
        await interaction.response.defer(ephemeral=True)
        self.data.initialize(guildID)
        if (voice_client.is_playing() or voice_client.is_paused()):
            self.data.set_loop(guildID, False)
            #current_song = self.data.get_current_song(guildID)
            voice_client.stop()
            await interaction.delete_original_response()
            await GUI_HANDLER(self, guildID)
            return
        msg = embed.skip_error_prompt(self.bot)
        await interaction.followup.send(embed= msg, ephemeral=True)

    @app_commands.check(valid_user_REGULAR_FUNC)
    @app_commands.command(name= "previous", description="Previous song")
    async def previous(self, interaction:discord.Interaction):
        try:
            user = interaction.user
            guildName = interaction.user.guild.name
            guildID = interaction.user.guild.id
            voice_client = interaction.client.get_guild(guildID).voice_client
            channel = interaction.channel
            log(guildName, 'COMMAND', 'previous')
            await interaction.response.defer(thinking=True)
            #IF VOICE RUNNING
            if voice_client is None:
                self.data.set_loop(guildID, False)
                self.data.history_to_queue(guildID)
                await self.music_player_start(user, guildName, guildID, voice_client, channel, edit = True)
                await interaction.delete_original_response()
                return
            if voice_client.is_playing() or voice_client.is_paused():
                self.data.set_loop(guildID, False)
                self.data.flip_back(guildID)
                voice_client.stop()
                await self.music_player_start(user, guildName, guildID, voice_client, channel, edit = True)
                await interaction.delete_original_response()
                return
            self.data.set_loop(guildID, False)
            self.data.history_to_queue(guildID)
            await self.music_player_start(user, guildName, guildID, voice_client, channel, edit = True)
            await interaction.delete_original_response()
            return
        except Exception as e:
            error_log('previous', e, guildName= guildName)

    @app_commands.check(valid_user_REGULAR_FUNC)
    @app_commands.command(name= "pause", description="Pause song")
    async def pause(self, interaction:discord.Interaction):
        await interaction.response.defer(thinking=True)
        try:
            guildName = interaction.user.guild.name
            guildID = interaction.user.guild.id
            voice_client = interaction.client.get_guild(guildID).voice_client
            log(guildName, 'COMMAND', 'previous')
            if voice_client.is_playing() and not voice_client.is_paused():
                song = self.data.get_current_song(guildID)
                log(guildName, 'PAUSED',song['title'])
                voice_client.pause()
                await GUI_HANDLER(self, guildID)
        except Exception as e:
            error_log('pause', e)
        await interaction.delete_original_response()

    @app_commands.check(valid_user_REGULAR_FUNC)
    @app_commands.command(name= "resume", description="Resume song")
    async def resume(self, interaction:discord.Interaction):
        await interaction.response.defer(thinking=True)
        try:
            guildName = interaction.user.guild.name
            guildID = interaction.user.guild.id
            voice_client = interaction.client.get_guild(guildID).voice_client
            log(guildName, 'COMMAND', 'previous')
            if not voice_client.is_playing() and voice_client.is_paused():
                song = self.data.get_current_song(guildID)
                log(guildName, 'PAUSED',song['title'])
                voice_client.resume()
                await GUI_HANDLER(self, guildID)
        except Exception as e:
            error_log('pause', e)
        await interaction.delete_original_response()

    @app_commands.check(valid_user_REGULAR_FUNC)
    @app_commands.command(name= "shuffle", description="Shuffle song")
    async def shuffle(self, interaction:discord.Interaction):
        await interaction.response.defer(thinking=True)
        try:
            user = interaction.user
            guildName = interaction.user.guild.name
            guildID = interaction.user.guild.id
            voice_client = interaction.client.get_guild(guildID).voice_client
            channel = interaction.channel
            log(guildName, 'command', 'play')
            queue = self.data.get_queue(guildID)
            history = self.data.get_history(guildID)
            combined = queue+history
            if combined == []:
                return
            random.shuffle(combined)
            self.data.set_history(guildID, [])
            self.data.set_queue(guildID, combined)
            await interaction.delete_original_response()
            await self.music_player_start(user, guildName, guildID, voice_client, channel, edit = True)
        except Exception as e:
            error_log('shuffle_tc', e)
            await interaction.delete_original_response()

    @app_commands.check(valid_user_REGULAR_FUNC)
    @app_commands.command(name= "reset", description="Full reset bot")
    async def reset(self, interaction:discord.Interaction):
        await interaction.response.defer()
        try:
            guildName = interaction.user.guild.name
            guildID = interaction.user.guild.id
            voice_client = interaction.client.get_guild(guildID).voice_client
            log(guildName, 'button', 'disconnect')
            self.data.full_reset(guildID)
            if voice_client is not None:
                channel_name = voice_client.channel.name
                if voice_client.is_playing() or voice_client.is_paused():
                    voice_client.stop()
                await voice_client.disconnect()
                log(guildName, 'DISCONNECTED (force)', channel_name)
            await interaction.delete_original_response()
            await GUI_HANDLER(self, guildID)
        except Exception as e:
            await interaction.delete_original_response()
            error_log('DisconnectButton', e, guildName= guildName)

    @app_commands.check(valid_user_REGULAR_FUNC)
    @app_commands.command(name= "flush", description="Empty current data and stop music player")
    async def flush(self, interaction:discord.Interaction):
        await interaction.response.defer()
        try:
            guildName = interaction.user.guild.name
            guildID = interaction.user.guild.id
            voice_client = interaction.client.get_guild(guildID).voice_client
            log(guildName, 'button', 'flush')
            self.data.reset(guildID)
            if voice_client is not None:
                if voice_client.is_playing() or voice_client.is_paused():
                    voice_client.stop()
            self.data.full_reset(guildID)
            await interaction.delete_original_response()
            await GUI_HANDLER(self, guildID, edit=False)
        except Exception as e:
            await interaction.delete_original_response()
            error_log('flush', e, guildName= guildName)

    @app_commands.command(name= "help", description="Shows bot use information")
    async def help(self, interaction:discord.Interaction):
        guildName = interaction.user.guild.name
        guildID = interaction.user.guild.id
        log(guildName, 'command', 'help')
        msg = embed.HelpPrompt(self.bot)
        await interaction.response.send_message(embed= msg)
        if self.data.get_message(guildID) is not None:
            await GUI_HANDLER(self, guildID, edit=False)

  #@commands.check(valid_play_command2)
    @commands.command(aliases = ['p','P', 'play','PLAY'])
    async def play_tc(self, ctx:commands.context.Context):
        title_or_link = ctx.message.content.strip()[3:]
        user = ctx.author
        guildName = str(ctx.guild)
        guildID = ctx.guild.id
        voice_client = self.bot.get_guild(guildID).voice_client
        channel = ctx.message.channel
        log(guildName, 'command', 'play')
        if await valid_play_command2(self.bot, ctx) is False:
            msg = embed.unauthorized_prompt(self.bot)
            await ctx.send(embed = msg, ephemeral = True)
            time.sleep(3)
            await GUI_HANDLER(self, guildID, edit=False)
            return
        if title_or_link == '' or title_or_link.count(' ') == len(title_or_link):
            msg = embed.no_query_prompt(self.bot)
            await ctx.send(embed = msg, ephemeral = True)
            time.sleep(3)
            await GUI_HANDLER(self, guildID, edit=False)
            return
        self.data.initialize(guildID)
        try:
            song_data = GetYTMusic(title_or_link)
            if 'music.youtube.com' in title_or_link:
                if type(song_data) == list:
                    if song_data is None:
                        msg = embed.invalid_link(self.bot, title_or_link, 'YTMusic Playlist')
                        await ctx.send(embed= msg, ephemeral=True)
                        return
                    playlistType = 'YTMusic'
                    playlist_emb = queuePlaylist(guildName,guildID,song_data,playlistType,self.data)
                    msg = embed.queued_playlist_prompt(self.bot, playlist_emb, len(song_data), title_or_link, 'YTMusic')
                    await ctx.send(embed=msg)
                    await self.music_player_start(user, guildName, guildID, voice_client, channel)
                    return
                if '/watch?v=' in title_or_link:
                    song_data = GetYTMSong(title_or_link)
                    if song_data is None:
                        msg = embed.invalid_link(self.bot, title_or_link, 'YTMusic Song')
                        await ctx.send(embed= msg, ephemeral=True)
                        return
                    self.data.queue_song(guildID, song_data)
                    prompt = song_data['title'] + ' by ' + song_data['author']
                    log(guildName, "queued", f"{prompt} (ytmusic)" )
                    msg = embed.queue_prompt(self.bot, prompt)
                    await ctx.send(embed= msg)
                    await self.music_player_start(user, guildName, guildID, voice_client, channel)
                    return
                msg = embed.invalid_link(self.bot, title_or_link, 'YTMusic Song')
                await ctx.send(embed= msg, ephemeral=True)
                error_log('play_tc', 'invalid ytmusic link', title_or_link, guildName=guildName)
                return
            
            if 'youtube.com/' in title_or_link:
                song_data = GetYT(title_or_link)
                if type(song_data) == dict:
                    if song_data is None:
                        msg = embed.invalid_link(self.bot, title_or_link, 'Youtube Song')
                        await ctx.send(embed= msg, ephemeral=True)
                        return
                    self.data.queue_song(guildID, song_data)
                    log(guildName, "QUEUED", f"{song_data['title']} (youtube)" )
                    msg = embed.queue_prompt(self.bot, song_data['title'])
                    await ctx.send(embed= msg)
                    await self.music_player_start(user, guildName, guildID, voice_client, channel)
                    return
                if type(song_data) == list:
                    if song_data is None:
                        msg = embed.invalid_link(self.bot, title_or_link, 'YT Playlist')
                        await ctx.send(embed= msg, ephemeral=True)
                        return
                    playlistType = 'Youtube'
                    playlist_emb = queuePlaylist(guildName,guildID, song_data, playlistType, self.data)                    
                    msg = embed.queued_playlist_prompt(self.bot, playlist_emb, len(song_data), title_or_link, 'Youtube')
                    await ctx.send(embed = msg)
                    await self.music_player_start(user, guildName, guildID, voice_client, channel)
                    return
                msg = embed.invalid_link(self.bot, title_or_link, 'Youtube')
                await ctx.send(embed= msg, ephemeral=True)
                error_log('play_tc', 'invalid youtube link', title_or_link, guildName=guildName)
                return
            
            if 'open.spotify.com' in title_or_link:
                song_data = GetSpotify(title_or_link, self.client_id, self.client_secret)
                if song_data is None:
                    msg = embed.invalid_link(self.bot, title_or_link, 'Spotify')
                    await ctx.send(embed= msg, ephemeral=True)
                    return
                if type(song_data) is dict:
                    self.data.queue_song(guildID, song_data)
                    full_title = song_data['title'] + ' by ' + song_data['author']
                    log(guildName, "QUEUED", f"{full_title} (spotify)" )
                    msg = embed.queue_prompt(self.bot, full_title)
                    await ctx.send(embed= msg)
                    await self.music_player_start(user, guildName, guildID, voice_client, channel)
                    return
                if type(song_data) is list:
                    playlistType = 'Spotify'
                    playlist = song_data
                    playlist_emb = queuePlaylist(guildName,guildID,playlist,playlistType,self.data)
                    msg = embed.queued_playlist_prompt(self.bot, playlist_emb, len(playlist), title_or_link, 'Spotify')
                    await ctx.send(embed= msg)
                    await self.music_player_start(user, guildName, guildID, voice_client, channel)
                    return
                
                msg = embed.invalid_link(self.bot, title_or_link, 'Spotify')
                await ctx.send(embed= msg, ephemeral=True)
                error_log('play_tc', 'invalid spotify link', title_or_link, guildName=guildName)
                return

            if 'https://' in title_or_link:
                msg = embed.invalid_link(self.bot, title_or_link)
                await ctx.send(embed= msg, ephemeral=True)
                error_log('play_tc', 'invalid link', title_or_link, guildName=guildName)
                return
            
            #title_or_link is not a link
            song = {
                'title' : title_or_link, 
                'author': None,
                'query' : title_or_link,
                'source': 'query'} 
            self.data.queue_song(guildID, song)
            log(guildName, "QUEUED", f'{title_or_link} (query)')
            msg = embed.queue_prompt(self.bot, title_or_link)
            await ctx.send(embed = msg)
            await self.music_player_start(user, guildName, guildID, voice_client, channel)

        except Exception as e:
            error_log('play_tc', e, guildName=guildName)

    @commands.command(aliases = ['s','S', 'skip', 'SKIP'])
    async def skip_tc(self, ctx:commands.context.Context):
        guildName = str(ctx.guild)
        guildID = ctx.guild.id
        voice_client = self.bot.get_guild(guildID).voice_client
        log(guildName, 'command', 'skip')
        if await valid_user_REGULAR_FUNC_tc(self.bot, ctx) is False:
            msg = embed.unauthorized_prompt(self.bot)
            await ctx.send(embed = msg)
            return
        self.data.initialize(guildID)
        if (voice_client.is_playing() or voice_client.is_paused()):
            self.data.set_loop(guildID, False)
            #current_song = self.data.get_current_song(guildID)
            voice_client.stop()
            time.sleep(.3)
            await GUI_HANDLER(self, guildID, edit=False)
            return
        error_log('skip_tc', 'None')
        msg = embed.skip_error_prompt(self.bot)
        await ctx.send(embed= msg, ephemeral=True)
    
    @commands.command(aliases = ['pre', 'PRE', 'previous', 'PREVIOUS'])
    async def previous_tc(self, ctx:commands.context.Context):
        try:
            user = ctx.author
            guildName = str(ctx.guild)
            guildID = ctx.guild.id
            voice_client = self.bot.get_guild(guildID).voice_client
            channel = ctx.message.channel
            log(guildName, 'COMMAND', 'previous')
            if await valid_user_REGULAR_FUNC_tc(self.bot, ctx) is False:
                msg = embed.unauthorized_prompt(self.bot)
                await ctx.send(embed = msg)
                return
            #IF VOICE RUNNING/p
            if voice_client is None and self.data.get_history(guildID) != []:
                self.data.set_loop(guildID, False)
                self.data.history_to_queue(guildID)
                await self.music_player_start(user, guildName, guildID, voice_client, channel)
                return
            if voice_client.is_playing() or voice_client.is_paused():
                self.data.set_loop(guildID, False)
                self.data.flip_back(guildID)
                voice_client.stop()
                await self.music_player_start(user, guildName, guildID, voice_client, channel)
                return
            self.data.set_loop(guildID, False)
            self.data.history_to_queue(guildID)
            await self.music_player_start(user, guildName, guildID, voice_client, channel )
            return
        except Exception as e:
            error_log('previous', e, guildName= guildName)
    
    @commands.command(aliases = ['pause', 'PAUSE'])
    async def pause_tc(self, ctx:commands.context.Context):
        try:
            guildName = str(ctx.guild)
            guildID = ctx.guild.id
            voice_client = self.bot.get_guild(guildID).voice_client
            log(guildName, 'COMMAND', 'pause_tc')
            if await valid_user_REGULAR_FUNC_tc(self.bot, ctx) is False:
                msg = embed.unauthorized_prompt(self.bot)
                await ctx.send(embed = msg)
                return
            if voice_client.is_playing() and not voice_client.is_paused():
                song = self.data.get_current_song(guildID)
                log(guildName, 'PAUSED',song['title'])
                voice_client.pause()
                await GUI_HANDLER(self, guildID, edit=False)
        except Exception as e:
            error_log('pause_tc', e, guildName=guildName)
            
    @commands.command(aliases = ['resume', 'RESUME'])
    async def resume_tc(self, ctx:commands.context.Context):
        try:
            guildName = str(ctx.guild)
            guildID = ctx.guild.id
            voice_client = self.bot.get_guild(guildID).voice_client
            log(guildName, 'COMMAND', 'pause')
            if await valid_user_REGULAR_FUNC_tc(self.bot, ctx) is False:
                msg = embed.unauthorized_prompt(self.bot)
                await ctx.send(embed = msg)
                return
            if not voice_client.is_playing() and voice_client.is_paused():
                song = self.data.get_current_song(guildID)
                log(guildName, 'resume_tc',song['title'])
                voice_client.resume()
                await GUI_HANDLER(self, guildID, edit=False)
        except Exception as e:
            error_log('resume', e, guildName= guildName)

    @commands.command(aliases = ['shuffle', 'SHUFFLE'])
    async def shuffle_tc(self, ctx:commands.context.Context):
        try:
            user = ctx.author
            guildName = str(ctx.guild)
            guildID = ctx.guild.id
            voice_client = self.bot.get_guild(guildID).voice_client
            channel = ctx.message.channel
            log(guildName, 'command', 'play')
            if await valid_user_REGULAR_FUNC_tc(self.bot, ctx) is False:
                msg = embed.unauthorized_prompt(self.bot)
                await ctx.send(embed = msg)
                return
            queue = self.data.get_queue(guildID)
            history = self.data.get_history(guildID)
            combined = queue+history
            if combined == []:
                return
            random.shuffle(combined)
            self.data.set_history(guildID, [])
            self.data.set_queue(guildID, combined)
            await self.music_player_start(user, guildName, guildID, voice_client, channel, edit = False)
        except Exception as e:
            error_log('shuffle_tc', e)

    @commands.command(aliases = ['pr','PR', 'play_random', 'PLAY_RANDOM'])
    async def play_random_tc(self, ctx:commands.context.Context):
        try:
            user = ctx.author
            guildName = str(ctx.guild)
            guildID = ctx.guild.id
            voice_client = self.bot.get_guild(guildID).voice_client
            channel = ctx.message.channel
            log(guildName, 'command', 'play_random_tc')
            if await valid_play_command2(self.bot, ctx) is False:
                msg = embed.unauthorized_prompt(self.bot)
                await ctx.send(msg)
                return
            self.data.initialize(guildID)
            if self.data.flip_random(guildID) is True:
                log(guildName, 'RANDOM', 'On')
            else: 
                log(guildName, 'RANDOM', 'Off')
            await self.music_player_start(user, guildName, guildID, voice_client, channel)
        except Exception as e:
            error_log('play_random_tc', e, guildName=guildName)

    @commands.command(aliases = ['r', 'R', 'reset','RESET'])
    async def reset_tc(self, ctx:commands.context.Context):
        try:
            guildName = str(ctx.guild)
            guildID = ctx.guild.id
            voice_client = self.bot.get_guild(guildID).voice_client
            log(guildName, 'button', 'disconnect')
            self.data.full_reset(guildID)
            if voice_client is not None:
                channel_name = voice_client.channel.name
                if voice_client.is_playing() or voice_client.is_paused():
                    voice_client.stop()
                await voice_client.disconnect()
                log(guildName, 'DISCONNECTED (force)', channel_name)
            await GUI_HANDLER(self, guildID, edit= False)
        except Exception as e:
            error_log('DisconnectButton', e, guildName= guildName)

    @commands.command(aliases = ['f','F'])
    async def flush_tc(self, ctx:commands.context.Context):
        try:
            guildName = str(ctx.guild)
            guildID = ctx.guild.id
            voice_client = self.bot.get_guild(guildID).voice_client
            log(guildName, 'button', 'flush')
            self.data.reset(guildID)
            if voice_client is not None:
                if voice_client.is_playing() or voice_client.is_paused():
                    voice_client.stop()
            self.data.full_reset(guildID)
            msg = embed.flush_prompt(self.bot)
            await ctx.send(embed=msg)
            time.sleep(3)
            await GUI_HANDLER(self, guildID, edit=False)
        except Exception as e:
            error_log('ResetButton', e, guildName= guildName)

    @commands.command(aliases = ['h','H'])
    async def help_tc(self, ctx:commands.context.Context):
        guildName = str(ctx.guild)
        guildID = ctx.guild.id
        log(guildName, 'command', 'help')
        msg = embed.HelpPrompt(self.bot)
        await ctx.send(embed= msg)
        if self.data.get_message(guildID) is not None:
            await GUI_HANDLER(self, guildID, edit=False)


    @commands.command(name= "sync")
    async def sync(self,ctx):
        guildName = ctx.guild.name
        try:
            sync_num = await ctx.bot.tree.sync()
            log(guildName, 'synced commands', sync_num)
        except Exception as e:
            print(e)

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
        try:
            while self.gui_print:
                guildID = self.gui_print.pop()
                await GUI_HANDLER(self, guildID)
        except Exception as e:
            error_log('gui_loop', e, self.gui_print)

####### Auto Disconnect Bot After X Seconds idle
    @tasks.loop(minutes=3)
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
                    await GUI_HANDLER(self, guildID)
                    log(voice.guild.name, 'disconnected (timeout)', channelName)
        except Exception as e:
            error_log('disconnect_check', e)