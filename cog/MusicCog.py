import discord, time
from discord                import app_commands, FFmpegPCMAudio
from discord.ext            import commands
from cog.helper             import embed
from cog.helper.Log         import *
from cog.helper.Functions   import *
from cog.helper.MusicSearch import *

FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
FFMPEG_LOC = "C:\\Users\\p\\Downloads\\ffmpeg\\bin\\ffmpeg.exe"
LOCAL_MUSIC_PATH = "C:\\Users\\p\\Documents\\SERVER\\music\\Formatted"


class MusicCog(commands.Cog):
    def __init__(self, bot:commands.Bot, client_id, client_secret, data, gui_print):
        self.bot = bot
        self.client_id = client_id
        self.client_secret = client_secret
        self.data = data
        self.gui_print = gui_print

    #MUSIC PLAYER LOOP (not recursive)
    def music_player(self, guildName, guildID, voice_client, recall = False):
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
        return True
    
    #CHECKS IF MUSIC_PLAYER LOOP SHOULD START
    async def music_player_start(self, user, guildName, guildID, voice_client, channel, edit = False):
        voice_client = await voice_connect(user, guildName, guildID, voice_client)
        self.data.set_channel(guildID, channel)
        play_error = False
        if voice_client.is_playing() == voice_client.is_paused() == False and self.data.get_current_song(guildID) is None:
            log(guildName, 'MUSIC PLAYER', 'starting')
            try:
                self.music_player(guildName, guildID, voice_client)
            except Exception as e:
                play_error = True
                error_log('music_player', e)
        await GUI_HANDLER(self, guildID, edit= edit, error= play_error)
    
#######PLAY FUNCTIONS######################################################
    @app_commands.check(valid_play_command)
    @app_commands.command(name= "play", description="Play Song or Playlist with the Title or Link (Spotify, YouTube, YTMusic)")
    async def play_sc(self, interaction:discord.Interaction, title_or_link:str):
        user = interaction.user
        guildName = interaction.user.guild.name
        guildID = interaction.user.guild.id
        voice_client = interaction.client.get_guild(guildID).voice_client
        channel = interaction.channel
        log(guildName, 'command', 'play')
        self.data.initialize(guildID)
        await interaction.response.defer()
        try:
            if 'music.youtube.com' in title_or_link:
                song_data = GetYTMusic(title_or_link)
                if type(song_data) == list:
                    song_data = GetYTMPlaylist(title_or_link)
                    if song_data is None:
                        msg = embed.invalid_link(self.bot, title_or_link, 'YTMusic Playlist')
                        await interaction.followup.send(embed= msg, ephemeral=True)
                        return
                    playlistType = 'YTMusic'
                    playlist_emb = queuePlaylist(guildName,guildID,song_data, playlistType,self.data)
                    msg = embed.queued_playlist_prompt(self.bot, playlist_emb, len(song_data), title_or_link, 'YTMusic')
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
                    await interaction.followup.send(embed= msg)
                    await self.music_player_start(user, guildName, guildID, voice_client, channel)
                    return
                msg = embed.invalid_link(self.bot, title_or_link, 'YTMusic Song')
                await interaction.followup.send(embed= msg, ephemeral=True)
                error_log('play', 'invalid ytmusic link', title_or_link)
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
                    await interaction.followup.send(embed = msg)              
                    await self.music_player_start(user, guildName, guildID, voice_client, channel)
                    return
                msg = embed.invalid_link(self.bot, title_or_link, 'Youtube')
                await interaction.followup.send(embed= msg, ephemeral=True)
                error_log('play', 'invalid youtube link', title_or_link)
                return
            
            if 'open.spotify.com' in title_or_link:
                song_data = GetSpotify(title_or_link, self.client_id, self.client_secret)
                if song_data is None:
                    msg = embed.invalid_link(self.bot, title_or_link, 'Spotify')
                    await interaction.followup.send(embed= msg, ephemeral=True)
                    return
                if type(song_data) is dict:
                    self.data.queue_song(guildID, song_data)
                    full_title = song_data['title'] + ' by ' + song_data['author']
                    log(guildName, "QUEUED", f"{full_title} (spotify)" )
                    msg = embed.queue_prompt(self.bot, full_title)
                    await interaction.followup.send(embed= msg)
                    await self.music_player_start(user, guildName, guildID, voice_client, channel)
                    return
                if type(song_data) is list:
                    playlistType = 'Spotify'
                    playlist = song_data
                    playlist_emb = queuePlaylist(guildName,guildID,playlist,playlistType,self.data)
                    msg = embed.queued_playlist_prompt(self.bot, playlist_emb, len(playlist), title_or_link, 'Spotify')
                    await interaction.followup.send(embed= msg)
                    await self.music_player_start(user, guildName, guildID, voice_client, channel)
                    return
                
                msg = embed.invalid_link(self.bot, title_or_link, 'Spotify')
                await interaction.followup.send(embed= msg, ephemeral=True)
                error_log('play', 'invalid spotify link', title_or_link)
                return

            if 'https://' in title_or_link:
                msg = embed.invalid_link(self.bot, title_or_link)
                await interaction.followup.send(embed= msg, ephemeral=True)
                error_log('play', 'invalid link', title_or_link)
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
            await interaction.followup.send(embed = msg)
            await self.music_player_start(user, guildName, guildID, voice_client, channel)
        except Exception as e:
            error_log('play', e)

    @app_commands.check(valid_play_command)
    @app_commands.command(name= "play_random", description="Play random songs from pocket bot library forever")
    async def play_random_sc(self, interaction:discord.Interaction): 
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

    @app_commands.check(valid_play_command)
    @app_commands.command(name= "skip", description="Skips song")
    async def skip_sc(self, interaction:discord.Interaction):
        guildName = interaction.user.guild.name
        log(guildName, 'command', 'skip')
        guildName = interaction.user.guild.name
        guildID = interaction.user.guild.id
        voice_client = interaction.client.get_guild(guildID).voice_client
        await interaction.response.defer(ephemeral=True)
        self.data.initialize(guildID)
        if voice_client is None:
            msg = embed.skip_error_prompt(self.bot)
            await interaction.followup.send(embed= msg, ephemeral=True)
            return
        if (voice_client.is_playing() or voice_client.is_paused()):
            self.data.set_loop(guildID, False)
            #current_song = self.data.get_current_song(guildID)
            voice_client.stop()
            await interaction.delete_original_response()
            await GUI_HANDLER(self, guildID)
            return
        msg = embed.skip_error_prompt(self.bot)
        await interaction.followup.send(embed= msg, ephemeral=True)

    @app_commands.command(name= "help", description="Shows bot use information")
    async def help_sc(self, interaction:discord.Interaction):
        guildName = interaction.user.guild.name
        guildID = interaction.user.guild.id
        log(guildName, 'command', 'help')
        msg = embed.HelpPrompt(self.bot)
        await interaction.response.send_message(embed= msg)
        await GUI_HANDLER(self, guildID, edit=False)

  #@commands.check(valid_play_command2)
    @commands.command(aliases = ['p','P'])
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
            await ctx.send(msg)
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
                error_log('play2', 'invalid ytmusic link', title_or_link)
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
                error_log('play2', 'invalid youtube link', title_or_link)
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
                error_log('play2', 'invalid spotify link', title_or_link)
                return

            if 'https://' in title_or_link:
                msg = embed.invalid_link(self.bot, title_or_link)
                await ctx.send(embed= msg, ephemeral=True)
                error_log('play2', 'invalid link', title_or_link)
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
            error_log('play2', e)


    @commands.command(aliases = ['s','S'])
    async def skip_tc(self, ctx:commands.context.Context):
        guildName = str(ctx.guild)
        guildID = ctx.guild.id
        voice_client = self.bot.get_guild(guildID).voice_client
        log(guildName, 'command', 'skip')
        if await valid_play_command2(self.bot, ctx) is False:
            msg = embed.unauthorized_prompt(self.bot)
            await ctx.send(msg)
            return
        self.data.initialize(guildID)
        if voice_client is None:
            msg = embed.skip_error_prompt(self.bot)
            await ctx.send(embed= msg, ephemeral=True)
            return
        if (voice_client.is_playing() or voice_client.is_paused()):
            self.data.set_loop(guildID, False)
            #current_song = self.data.get_current_song(guildID)
            voice_client.stop()
            time.sleep(.3)
            await GUI_HANDLER(self, guildID, edit=False)
            return
        msg = embed.skip_error_prompt(self.bot)
        await ctx.send(embed= msg, ephemeral=True)

    @commands.command(aliases = ['h','H'])
    async def help_tc(self, ctx:commands.context.Context):
        guildName = str(ctx.guild)
        guildID = ctx.guild.id
        log(guildName, 'command', 'help')
        msg = embed.HelpPrompt(self.bot)
        await ctx.send(embed= msg)
        await GUI_HANDLER(self, guildID, edit=False)

    @commands.command(aliases = ['r','R'])
    async def play_random_tc(self, ctx:commands.context.Context):
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

    @commands.command(name= "sync")
    async def sync(self,ctx):
        guildName = ctx.guild.name
        try:
            sync_num = await ctx.bot.tree.sync()
            log(guildName, 'synced commands', sync_num)
        except Exception as e:
            print(e)

