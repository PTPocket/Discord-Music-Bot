import discord, os, random
from datetime import datetime
from discord               import app_commands, FFmpegPCMAudio
from discord.ext           import commands, tasks
from discord.ui            import View, Select, Button
from datetime              import datetime
from cog.helper            import embed
from cog.helper.guild_data import Guild_Music_Properties
from cog.helper.functions  import *
import cog.helper.setting  as Setting


FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
FFMPEG_LOC = "C:\\Users\\p\\Downloads\\ffmpeg\\bin\\ffmpeg.exe"
LOCAL_MUSIC_PATH = "C:\\Users\\p\\Documents\\SERVER\\music\\Formatted"



class Music_Cog(commands.Cog):
    def __init__(self, bot:commands.Bot, client_id, client_secret):
        Setting.initialize_settings()
        self.bot = bot
        self.client_id = client_id
        self.client_secret = client_secret
        self.data = Guild_Music_Properties()
        self.gui_print = set()
        self.gui_loop.start()
        self.disconnect_check.start()


    async def GUI_HANDLER(self, guildID, edit = True, error = False):
        try:
            player_embed = embed.MainGuiPrompt(self.bot, self.data, guildID, connect = error)
            view = MusicFunctions(self, self.data, guildID)
            channel = self.data.get_channel(guildID)
            last_message = self.data.get_message(guildID)

            if last_message is None:
                message = await channel.send(embed = player_embed, view = view)
                self.data.set_message(guildID, message)
                return

            if edit is True:
                message = await last_message.edit(embed = player_embed, view = view)
                self.data.set_message(guildID, message)
                return
            message = await channel.send(embed = player_embed, view = view)
            await last_message.delete()
            self.data.set_message(guildID, message)
        except Exception as e:
            error_log('Gui_handler', e)




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
                log(guildName, 'error', 'music_player_start', e)
        await self.GUI_HANDLER(guildID, edit= edit, error= play_error)
        
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
        try:
            self.data.initialize(guildID)
            await interaction.response.defer()
            if 'music.youtube.com' in title_or_link:
                if '/playlist' in title_or_link:
                    playlist = GetYTMPlaylist(title_or_link)
                    if playlist is None:
                        msg = embed.invalid_link(self.bot, title_or_link, 'YTMusic Playlist')
                        await interaction.followup.send(embed= msg, ephemeral=True)
                        return
                    playlistType = 'YTMusic'
                    playlist_emb = queuePlaylist(guildName,guildID,playlist,playlistType,self.data)
                    msg = embed.queued_playlist_prompt(self.bot, playlist_emb, len(playlist), title_or_link, 'YTMusic')
                    await interaction.channel.send(embed=msg)
                    await self.music_player_start(user, guildName, guildID, voice_client, channel)
                    return
                if '/watch?v=' in title_or_link:
                    song = GetYTMSong(title_or_link)
                    if song is None:
                        msg = embed.invalid_link(self.bot, title_or_link, 'YTMusic Song')
                        await interaction.followup.send(embed= msg, ephemeral=True)
                        return
                    self.data.queue_song(guildID, song)
                    prompt = song['title'] + ' by ' + song['author']
                    log(guildName, "queued", f"{prompt} (ytmusic)" )
                    msg = embed.queue_prompt(self.bot, prompt)
                    await interaction.followup.send(embed= msg)
                    await self.music_player_start(user, guildName, guildID, voice_client, channel)
                    return
                msg = embed.invalid_link(self.bot, title_or_link, 'YTMusic Song')
                await interaction.followup.send(embed= msg, ephemeral=True)
                error_log('play', 'invalid ytmusic link', title_or_link)
                return
            
            if 'youtube.com/' in title_or_link:
                if 'watch?v=' in title_or_link:
                    song = GetYTSong(title_or_link)
                    if song is None:
                        msg = embed.invalid_link(self.bot, title_or_link, 'Youtube Song')
                        await interaction.followup.send(embed= msg, ephemeral=True)
                        return
                    self.data.queue_song(guildID, song)
                    log(guildName, "QUEUED", f"{song['title']} (youtube)" )
                    msg = embed.queue_prompt(self.bot, song['title'])
                    await interaction.followup.send(embed= msg)
                    await self.music_player_start(user, guildName, guildID, voice_client, channel)
                    return
                if '/playlist' in title_or_link:
                    playlist = GetYTPlaylist(title_or_link)
                    if playlist is None:
                        msg = embed.invalid_link(self.bot, title_or_link, 'YT Playlist')
                        await interaction.followup.send(embed= msg, ephemeral=True)
                        return
                    playlistType = 'Youtube'
                    playlist_emb = queuePlaylist(guildName,guildID,playlist,playlistType,self.data)      
                    msg = embed.queued_playlist_prompt(self.bot, playlist_emb, len(playlist), title_or_link, 'Youtube')
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
    @app_commands.command(name= "playlist", description="Queue a Playlist with a Link (Spotify, YouTube, YTMusic)")
    async def playlist(self, interaction:discord.Interaction, link:str):
        user = interaction.user
        guildName = interaction.user.guild.name
        guildID = interaction.user.guild.id
        voice_client = interaction.client.get_guild(guildID).voice_client
        channel = interaction.channel
        log(guildName, 'command', 'playlist')
        try:
            self.data.initialize(guildID)
            await interaction.response.defer(ephemeral=True)
            if 'music.youtube.com' in link and 'list=' in link:
                playlistType = 'YTMusic'
                playlist = GetYTMPlaylist(link)
            elif 'youtube.com' in link and 'list=' in link:
                playlistType = 'Youtube'
                playlist = GetYTPlaylist(link)
            elif 'open.spotify.com/playlist' in link:
                playlistType = 'Spotify'
                playlist = GetSpotify(link, self.client_id, self.client_secret)
            else:
                msg = embed.invalid_link(self.bot, link)
                await interaction.followup.send(embed= msg, ephemeral=True)
                error_log('playlist', 'Invalid Playlist Link')
                return
            if playlist is None:
                msg = embed.invalid_link(self.bot, link, f'{playlistType} Playlist')
                await interaction.followup.send(embed= msg, ephemeral=True)
                return 
            playlist_emb = queuePlaylist(guildName,guildID,playlist,playlistType,self.data)
            msg = embed.queued_playlist_prompt(self.bot, playlist_emb, len(playlist), link, playlistType)
            await interaction.channel.send(embed=msg)
            await self.music_player_start(user, guildName, guildID, voice_client, channel)
        except Exception as e:
            error_log('playlist', e)
            return

    @app_commands.check(valid_play_command)
    @app_commands.command(name= "play_random", description="Play random songs from pocket bot library forever")
    async def play_random(self, interaction:discord.Interaction): 
        user = interaction.user
        guildName = interaction.user.guild.name
        guildID = interaction.user.guild.id
        voice_client = interaction.client.get_guild(guildID).voice_client
        channel = interaction.channel
        log(guildName, 'command', 'play_random')
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
    async def skip(self, interaction:discord.Interaction):
        guildName = interaction.user.guild.name
        guildID = interaction.user.guild.id
        voice_client = interaction.client.get_guild(guildID).voice_client
        log(guildName, 'command', 'skip')
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
            await self.GUI_HANDLER(guildID)
            return
        msg = embed.skip_error_prompt(self.bot)
        await interaction.followup.send(embed= msg, ephemeral=True)

    #@commands.check(valid_play_command2)
    @commands.command(name = 'p', aliases = ['P'])
    async def play2(self, ctx:commands.context.Context):
        title_or_link = ctx.message.content.strip()[3:]
        user = ctx.author
        guildName = str(ctx.guild)
        guildID = ctx.guild.id
        voice_client = self.bot.get_guild(guildID).voice_client
        channel = ctx.message.channel
        log(guildName, 'command', 'play')
        if await valid_play_command2(self.bot, ctx) is False:
            return
        try:
            self.data.initialize(guildID)
            if 'music.youtube.com' in title_or_link:
                if '/playlist' in title_or_link:
                    playlist = GetYTMPlaylist(title_or_link)
                    if playlist is None:
                        msg = embed.invalid_link(self.bot, title_or_link, 'YTMusic Playlist')
                        await ctx.send(embed= msg, ephemeral=True)
                        return
                    playlistType = 'YTMusic'
                    playlist_emb = queuePlaylist(guildName,guildID,playlist,playlistType,self.data)
                    msg = embed.queued_playlist_prompt(self.bot, playlist_emb, len(playlist), title_or_link, 'YTMusic')
                    await ctx.send(embed=msg)
                    await self.music_player_start(user, guildName, guildID, voice_client, channel)
                    return
                if '/watch?v=' in title_or_link:
                    song = GetYTMSong(title_or_link)
                    if song is None:
                        msg = embed.invalid_link(self.bot, title_or_link, 'YTMusic Song')
                        await ctx.send(embed= msg, ephemeral=True)
                        return
                    self.data.queue_song(guildID, song)
                    prompt = song['title'] + ' by ' + song['author']
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
                if 'watch?v=' in title_or_link:
                    song = GetYTSong(title_or_link)
                    if song is None:
                        msg = embed.invalid_link(self.bot, title_or_link, 'Youtube Song')
                        await ctx.send(embed= msg, ephemeral=True)
                        return
                    self.data.queue_song(guildID, song)
                    log(guildName, "QUEUED", f"{song['title']} (youtube)" )
                    msg = embed.queue_prompt(self.bot, song['title'])
                    await ctx.send(embed= msg)
                    await self.music_player_start(user, guildName, guildID, voice_client, channel)
                    return
                if '/playlist' in title_or_link:
                    playlist = GetYTPlaylist(title_or_link)
                    if playlist is None:
                        msg = embed.invalid_link(self.bot, title_or_link, 'YT Playlist')
                        await ctx.send(embed= msg, ephemeral=True)
                        return
                    playlistType = 'Youtube'
                    playlist_emb = queuePlaylist(guildName,guildID,playlist, playlistType, self.data)                    
                    msg = embed.queued_playlist_prompt(self.bot, playlist_emb, len(playlist), title_or_link, 'Youtube')
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
        

######## LOOP TO AUTO CHANGE GUI ##############################################################
    @tasks.loop(seconds = 5)
    async def gui_loop(self):
        while self.gui_print:
            guildID = self.gui_print.pop()
            await self.GUI_HANDLER(guildID)
        
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
                await self.GUI_HANDLER(guildID)
                log(voice.guild.name, 'disconnected (timeout)', channelName)


############# LISTENERS ########################################################################
    # Keep music player at bottom of channel
    @commands.Cog.listener() 
    async def on_message(self, message):
        guildName = message.guild.name
        guildID = message.guild.id
        command = message.content[:3].lower()
        if message.author.id != self.bot.user.id \
            and message.channel.id == self.data.get_message(guildID).channel.id\
            and command not in ['/p ']:
            await self.GUI_HANDLER(guildID, edit=False)

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
            await self.GUI_HANDLER(guildID)

            return
        


#####################################################################################
    @commands.command(name= "sync")
    async def sync(self,ctx):
        guildName = ctx.guild.name
        try:
            sync_num = await ctx.bot.tree.sync()
            log(guildName, 'synced commands', sync_num)
        except Exception as e:
            print(e)

#####################################################################################
class AddPlaylistModal(discord.ui.Modal, title='Save Playlist with Link'):
    name = discord.ui.TextInput(label='Name', required=True, placeholder='Name for your playlist')
    link = discord.ui.TextInput(label='Link', required=True, placeholder='Playlist Link (Spotify, Youtube, YTMusic))')
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(f'Thanks for your response, {self.name}{self.link}!', ephemeral=True)

class MusicFunctions(View):
    def __init__(self, music_cog:Music_Cog, data:Guild_Music_Properties, guildID):
        super().__init__(timeout=None)
        self.add_item(self.PreviousButton  (music_cog, data))
        self.add_item(self.PlayPause       (data))
        self.add_item(self.NextButton      (music_cog, data))
        self.add_item(self.ShuffleButton   (music_cog, data, guildID))
        self.add_item(self.LoopButton      (music_cog, data, guildID))
        self.add_item(self.RandomButton    (music_cog, data, guildID))
        self.add_item(self.ResetButton(music_cog, data))
        self.add_item(self.DisconnectButton(music_cog, data))
        
    async def interaction_check(self, interaction: discord.Interaction):
        user = interaction.user
        guildName = interaction.user.guild.name
        guildID = interaction.user.guild.id
        voice_client = interaction.client.get_guild(guildID).voice_client
        access = False
        if user.voice is None:
            access = False
        elif voice_client is None:
            access = True
        elif voice_client.channel.id == user.voice.channel.id:
            access = True
        
        if access is True:
            log(guildName, 'ACCESS GRANTED', user) 
            return True
        else:
            log(guildName, 'ACCESS DENIED', user)
            await interaction.response.defer()
            return False

    class PlayPause(Button):
        def __init__(self, data:Guild_Music_Properties):
            super().__init__(emoji = '⏯', style= discord.ButtonStyle.blurple)
            self.data = data
        async def callback(self, interaction: discord.Interaction):
            guildName = interaction.user.guild.name
            guildID = interaction.user.guild.id
            voice_client = interaction.client.get_guild(guildID).voice_client
            log(guildName, 'BUTTON', 'play/pause')
            song = self.data.get_current_song()
            if voice_client is None:
                self.style = discord.ButtonStyle.grey
                await interaction.response.edit_message(view=self.view)
                return
            if voice_client.is_playing() and not voice_client.is_paused():
                log(guildName, 'PAUSED',song['title'])
                voice_client.pause()
                self.style = discord.ButtonStyle.grey
                await interaction.response.edit_message(view=self.view)
                return
            if not voice_client.is_playing() and voice_client.is_paused():
                log(guildName, 'RESUMED',song['title'])
                self.style = discord.ButtonStyle.blurple
                await interaction.response.edit_message(view=self.view)
                voice_client.resume()
                return
            await interaction.response.defer()
            
    class RandomButton(Button):
        def __init__(self, music_cog:Music_Cog, data:Guild_Music_Properties, guildID):
            if data.get_random(guildID) == True:
                style= discord.ButtonStyle.blurple
            else:
                style= discord.ButtonStyle.grey
            super().__init__(emoji='♾', label='Random', style= style)
            self.data = data
            self.music_cog = music_cog

        async def callback(self, interaction: discord.Interaction):
            user = interaction.user
            guildName = interaction.user.guild.name
            guildID = interaction.user.guild.id
            voice_client = interaction.client.get_guild(guildID).voice_client
            channel = interaction.channel
            log(guildName, 'BUTTON', 'random')
            if self.data.flip_random(guildID) is True:
                log(guildName, 'RANDOM', 'On')
                self.data.set_loop(guildID, False)
                await self.music_cog.music_player_start(user, guildName, guildID, voice_client, channel, edit = True)
            else: 
                log(guildName, 'RANDOM', 'Off')
                await self.music_cog.GUI_HANDLER(guildID)
            await interaction.response.defer()
    
    class PreviousButton(Button):
        def __init__(self,music_cog:Music_Cog, data:Guild_Music_Properties):
            super().__init__(emoji = "⏮", style= discord.ButtonStyle.blurple)
            self.data = data
            self.music_cog = music_cog

        async def callback(self, interaction: discord.Interaction):
            user = interaction.user
            guildName = interaction.user.guild.name
            guildID = interaction.user.guild.id
            voice_client = interaction.client.get_guild(guildID).voice_client
            channel = interaction.channel
            log(guildName, 'BUTTON', 'previous')

            #IF VOICE RUNNING
            if voice_client is None:
                self.data.set_loop(guildID, False)
                self.data.history_to_queue(guildID)
                await interaction.response.defer(thinking=True)
                await self.music_cog.music_player_start(user, guildName, guildID, voice_client, channel, edit = True)
                await interaction.delete_original_response()
                return
            if voice_client.is_playing() or voice_client.is_paused():
                self.data.set_loop(guildID, False)
                self.data.flip_back(guildID)
                voice_client.stop()
                await interaction.response.defer(thinking=True)
                await self.music_cog.music_player_start(user, guildName, guildID, voice_client, channel, edit = True)
                await interaction.delete_original_response()
                return
            self.data.set_loop(guildID, False)
            self.data.history_to_queue(guildID)
            await interaction.response.defer(thinking=True)
            await self.music_cog.music_player_start(user, guildName, guildID, voice_client, channel, edit = True)
            await interaction.delete_original_response()
            return
     
    class NextButton(Button):
        def __init__(self,music_cog:Music_Cog, data:Guild_Music_Properties):
            super().__init__(emoji = "⏭", style= discord.ButtonStyle.blurple)
            self.data = data
            self.music_cog = music_cog

        async def callback(self, interaction: discord.Interaction):
            guildName = interaction.user.guild.name
            guildID = interaction.user.guild.id
            voice_client = interaction.client.get_guild(guildID).voice_client
            log(guildName, 'BUTTON', 'next')
            if voice_client is None:
                await interaction.response.defer()
                return
            if (voice_client.is_playing() or voice_client.is_paused()):
                self.data.set_loop(guildID, False)
                voice_client.stop()
                await interaction.response.defer(thinking=True)
                await self.music_cog.GUI_HANDLER(guildID)
                await interaction.delete_original_response()
                return
            
    class ShuffleButton(Button):
        def __init__(self,music_cog:Music_Cog, data:Guild_Music_Properties, guildID):
            if data.get_shuffle(guildID) is True:
                style= discord.ButtonStyle.blurple
            else:
                style= discord.ButtonStyle.grey
            super().__init__(emoji = "🔀", style= style)
            self.data = data
            self.music_cog = music_cog

        async def callback(self, interaction: discord.Interaction):
            user = interaction.user
            guildName = interaction.user.guild.name
            guildID = interaction.user.guild.id
            voice_client = interaction.client.get_guild(guildID).voice_client
            channel = interaction.channel
            log(guildName, 'BUTTON', 'shuffle')
            await interaction.response.defer()
            if voice_client is None:
                return
            queue = self.data.get_queue(guildID)
            history = self.data.get_history(guildID)
            num_songs = len(queue)+len(history)
            if num_songs > 0 or voice_client.is_playing() or voice_client.is_paused():
                self.data.set_random(guildID, False)
                self.data.flip_shuffle(guildID)
                if self.data.get_shuffle(guildID) is True:
                    log(guildName, 'Shuffle', 'on')
                    await self.music_cog.music_player_start(user, guildName, guildID, voice_client, channel, edit = True)
                else:
                    log(guildName, 'Shuffle', 'off')
                await self.music_cog.GUI_HANDLER(guildID)

    class LoopButton(Button):
        def __init__(self,music_cog:Music_Cog, data:Guild_Music_Properties, guildID):
            if data.get_loop(guildID) is True:
                style= discord.ButtonStyle.blurple
            else:
                style= discord.ButtonStyle.grey
            super().__init__(emoji = "🔁", style=style)
            self.music_cog = music_cog
            self.data = data
        async def callback(self, interaction: discord.Interaction):
            guildName = interaction.user.guild.name
            guildID = interaction.user.guild.id
            log(guildName, 'BUTTON', 'loop')
            voice_client = interaction.client.get_guild(guildID).voice_client
            await interaction.response.defer()
            if voice_client is None:
                return
            if voice_client.is_playing() or voice_client.is_paused():
                song = self.data.get_current_song(guildID)
                self.data.flip_loop(guildID)
                self.data.set_random(guildID, False)
                if self.data.get_loop(guildID) is True:
                    log(guildName, 'looping', "on")
                else:
                    log(guildName, 'looping', "off")
                await self.music_cog.GUI_HANDLER(guildID)
                return
            
    class DisconnectButton(Button):
        def __init__(self,music_cog:Music_Cog, data:Guild_Music_Properties):
            super().__init__(label = 'Disconnect', style=discord.ButtonStyle.grey)
            self.music_cog = music_cog
            self.data = data
        async def callback(self, interaction: discord.Interaction):
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
            await interaction.response.defer()
            await self.music_cog.GUI_HANDLER(guildID)

    class ResetButton(Button):
        def __init__(self,music_cog, data:Guild_Music_Properties):
            super().__init__(emoji='🚽',label = 'Flush', style=discord.ButtonStyle.grey)
            self.music_cog = music_cog
            self.data = data
        async def callback(self, interaction: discord.Interaction):
            guildName = interaction.user.guild.name
            guildID = interaction.user.guild.id
            voice_client = interaction.client.get_guild(guildID).voice_client
            log(guildName, 'button', 'flush')
            await interaction.response.defer(ephemeral=True)
            
            self.data.reset(guildID)
            if voice_client is not None:
                if voice_client.is_playing() or voice_client.is_paused():
                    voice_client.stop()
            self.data.full_reset(guildID)
            #await interaction.response.send_message(embed=embed.flush_prompt(self.music_cog.bot),ephemeral=True)
            await self.music_cog.GUI_HANDLER(guildID)

############### NOT USED
    class AddPlaylistButton(Button):
        def __init__(self,music_cog, data:Guild_Music_Properties):
            super().__init__(emoji='➕',label = 'Playlist', style=discord.ButtonStyle.blurple)
            self.music_cog = music_cog
            self.data = data
        async def callback(self, interaction: discord.Interaction):
            guildName = interaction.user.guild.name
            guildID = interaction.user.guild.id
            log(guildName, 'BUTTON', 'add playlist')
            await interaction.response.send_modal(AddPlaylistModal())
            #await self.music_cog.GUI_HANDLER(self.guildID, reprint=True)

    class SongSelectMenu(Select):
        def __init__(self, music_cog:Music_Cog, data:Guild_Music_Properties, guildID):
            self.data      = data
            self.music_cog = music_cog
            self.guildID  = guildID
            options = []

            song_list = self.data.get_all_songs(guildID)
            incre = float(len(song_list))/25
            if incre < 1:
                incre = 1
            ind = float(0)
            while ind < len(song_list):
                song = song_list[int(ind)]['title']
                if len(song) > 99:
                    song = song[0:99]
                options.append(discord.SelectOption(
                    label = f"{song}"))
                ind+=incre
            super().__init__(placeholder='Select Song', options = options)
            self.song_list = song_list

        async def callback(self, interaction:discord.Interaction):
            user = interaction.user
            guildName = interaction.user.guild.name
            guildID = interaction.user.guild.id
            voice_client = interaction.client.get_guild(guildID).voice_client
            channel = interaction.channel
            log(guildName, 'MENU OPTION', 'Clicked')
            song_title = self.values[0]
            if voice_client is None:
                await interaction.response.defer()
                return
            if (voice_client.is_playing() or voice_client.is_paused()):
                queue = self.data.get_queue()
                self.data.empty_queue()
                voice_client.stop()
                await interaction.response.defer()
                past_songs = self.data.get_history()[::-1]
                all_songs = past_songs+queue
                for i in range(len(all_songs)):
                    if song_title == all_songs['title']:
                        index = i
                self.data.set_queue(guildID, all_songs[index:len(all_songs)])
                self.data.set_history(guildID, all_songs[0:index])
                await self.music_player_start(user, guildName, guildID, voice_client, channel)
                return
            await interaction.response.defer()

    class RandomSongButton(Button):
        def __init__(self,music_cog:Music_Cog, data:Guild_Music_Properties):
            super().__init__(label = 'Random Song', style= discord.ButtonStyle.blurple)
            self.data = data
            self.music_cog = music_cog
        async def callback(self, interaction: discord.Interaction):
            user = interaction.user
            guildName = interaction.user.guild.name
            guildID = interaction.user.guild.id
            voice_client = interaction.client.get_guild(guildID).voice_client
            channel = interaction.channel
            log(guildName, 'BUTTON', 'random song')
            add_random_song(self.data, guildID)
            if voice_client is not None and (voice_client.is_playing() or voice_client.is_paused()):
                voice_client.stop()
            self.data.set_loop(guildID, False)
            await interaction.response.defer()
            await self.music_cog.music_player_start(user, guildName, guildID, voice_client, channel, edit = True)
