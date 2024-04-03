import discord, os, random
import cog.helper.setting  as Setting
from discord               import app_commands, FFmpegPCMAudio
from discord.ext           import commands, tasks
from discord.ui            import View, Select, Button
from datetime              import datetime
from cog.helper            import embed
from cog.helper.guild_data import Guild_Music_Properties
from cog.helper.functions  import *



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


    async def GUI_HANDLER(self, guild_id, reprint = False, connect = False):
        try:
            player_embed = embed.MainGuiPrompt(self.bot, self.data, guild_id, connect = connect)
            view = MusicFunctions(self, self.data, guild_id)
            last_message = self.data.get_message(guild_id)
            #First message
            if last_message is None:
                message = await self.data.get_channel(guild_id).send(embed = player_embed, view = view)
                self.data.set_message(guild_id, message)
                return
            #New message when last message not at bottom
            if reprint is True:
                message = await self.data.get_channel(guild_id).send(embed = player_embed, view = view)
                if last_message is not None:
                    await last_message.delete()
                self.data.set_message(guild_id, message)
                return
            #Edit message when its at bottom and same channel
            if self.data.get_channel(guild_id).id == last_message.channel.id:
                msg = self.data.get_message(guild_id)
                await msg.edit(embed = player_embed, view = view)
                return
            else:#new message when its new channel
                message = await self.data.get_channel(guild_id).send(embed = player_embed, view = view)
                await last_message.delete()
                self.data.set_message(guild_id, message)
                return
        except Exception as e: 
            print(e)

    #MUSIC PLAYER LOOP (not recursive)
    def music_player(self, interaction:discord.Interaction, recall = False):
        guild_name = interaction.user.guild.name
        guild_id = interaction.user.guild.id
        if recall is True:
            self.data.current_to_history(guild_id)

        check_features(self.data, guild_id)

        if self.data.empty_queue(guild_id):
            self.data.set_idle_timestamp(guild_id)
            self.gui_print.add(guild_id)
            log(guild_name, 'PLAYER', 'end')
            return

        self.data.queue_to_current(guild_id)
        song = self.data.get_current_song(guild_id)
        if song['source']=='youtube' or song['source']=='spotify':
            song = YoutubeGet(song['title'])

        if recall is True:
            self.gui_print.add(guild_id)
        
        if LOCAL_MUSIC_PATH in song['source']:
            player = FFmpegPCMAudio(
                song['source'],
                executable=FFMPEG_LOC)
        else:
            player = FFmpegPCMAudio(
                song['source'],
                **FFMPEG_OPTIONS,
                executable= FFMPEG_LOC)
        player = discord.PCMVolumeTransformer(player, volume=0.16)
        voice_client = interaction.client.get_guild(guild_id).voice_client
        log(guild_name, "NOW PLAYING", f'\"{song["title"]}\"')
        self.data.set_idle_timestamp(guild_id)
        voice_client.play(player, after= lambda x=None: self.music_player(interaction, recall=True))
        return True
    
    #CHECKS IF MUSIC_PLAYER LOOP SHOULD START
    async def music_player_start(self, interaction:discord.Interaction, reprint=False):

        guild_name = interaction.user.guild.name
        guild_id = interaction.user.guild.id
        await voice_connect(interaction)
        voice_client = interaction.client.get_guild(guild_id).voice_client
        self.data.set_channel(guild_id, interaction.channel)
        connect_only = False
        if voice_client.is_playing() == voice_client.is_paused() == False and self.data.get_current_song(guild_id) is None:
            log(guild_name, 'MUSIC PLAYER', 'Start')
            try:
                self.music_player(interaction)
            except Exception as e:
                print(e)
                connect_only = True
        
        await self.GUI_HANDLER(guild_id, connect = connect_only,reprint=reprint)
        
#######PLAY FUNCTIONS######################################################
    @app_commands.check(valid_play_command)
    @app_commands.command(name= "play", description="Play Song or Playlist with the Title or Link (Spotify, YouTube, YTMusic)")
    async def play(self, interaction:discord.Interaction, title_or_link:str):
        try:
            guild_name = interaction.user.guild.name
            guild_id = interaction.user.guild.id
            self.data.initialize(interaction)
            await interaction.response.defer(ephemeral=True)
            
            if 'music.youtube.com' in title_or_link:
                title_or_link = title_or_link.replace(' ','')
                if '/playlist' in title_or_link:
                    playlist = YTMusicGet(title_or_link)
                    if playlist is None:
                        log(guild_name, 'ERROR', 'YTMusic Playlist')
                        msg = embed.invalid_link(self.bot, title_or_link, 'YTMusic Playlist')
                        await interaction.followup.send(embed= msg, ephemeral=True)
                        return
                    song_names_list = []
                    name_list = ''
                    last_ind = None
                    for ind, title in enumerate(playlist):
                        self.data.queue_song(guild_id,{'source': 'youtube', 'title': title})
                        last_ind = ind+1
                        title = embed.title(f"{last_ind}. {title}")
                        if len(name_list) + len(title) < 1000:
                            name_list += title+'\n'
                        else:
                            song_names_list.append(name_list)
                            name_list = title+'\n'
                    song_names_list.append(name_list)
                    log(guild_name, "QUEUED", f"YTMusic ({len(playlist)} songs)")
                    done = embed.finished_prompt(self.bot)
                    await interaction.followup.send(embed = done)
                    msg = embed.queued_playlist_prompt(self.bot, song_names_list, len(playlist), title_or_link, 'Youtube')
                    await interaction.channel.send(embed=msg)
                    await self.music_player_start(interaction,reprint=True)
                elif '/watch' in title_or_link:
                    song = YTMusicGet(title_or_link)
                    if song is None:
                        log(guild_name, 'ERROR', 'YTMusic Song')
                        msg = embed.invalid_link(self.bot, title_or_link, 'YTMusic Song')
                        await interaction.followup.send(embed= msg, ephemeral=True)
                        await self.GUI_HANDLER(guild_id)
                        return
                    self.data.queue_song(guild_id, song)
                    msg = embed.queue_prompt(self.bot, song['title'])
                    await interaction.followup.send(embed= msg)
                    log(guild_name, "QUEUED", f"YTMusic link ({song['title']})" )
                    await self.music_player_start(interaction,reprint=True)
                else:
                    log(guild_name, 'ERROR', 'YTMusic')
                    msg = embed.invalid_link(self.bot, title_or_link, 'YTMusic')
                    await interaction.followup.send(embed= msg, ephemeral=True)
                return
            
            if 'youtube.com/' in title_or_link:
                title_or_link = title_or_link.replace(' ','')
                if '/watch' in title_or_link:
                    try:
                        song = YoutubeGet(title_or_link)
                        if song is None:
                            log(guild_name, 'ERROR', 'Youtube Watch')
                            msg = embed.invalid_link(self.bot, title_or_link, 'Youtube Song')
                            await interaction.followup.send(embed= msg, ephemeral=True)
                            await self.GUI_HANDLER(guild_id)
                            return##################################################
                        self.data.queue_song(guild_id, song)
                        log(guild_name, "QUEUED", f"youtube link ({song['title']})" )
                        msg = embed.queue_prompt(self.bot, song['title'])
                        await interaction.followup.send(embed= msg)
                        await self.music_player_start(interaction,reprint=True)
                    except Exception as e:
                        print(e)
                elif '/playlist' in title_or_link:
                    playlist = YoutubeGet(title_or_link)
                    if playlist is None:
                        log(guild_name, 'ERROR', 'Youtube Playlist')
                        msg = embed.invalid_link(self.bot, title_or_link, 'YT Playlist')
                        await interaction.followup.send(embed= msg, ephemeral=True)
                        await self.GUI_HANDLER(guild_id)
                        return####################################################
                    song_names_list = []
                    name_list = ''
                    last_ind = None
                    for ind, title in enumerate(playlist):
                        self.data.queue_song(guild_id,{'source': 'youtube', 'title': title})
                        last_ind = ind+1
                        title = embed.title(f"{last_ind}. {title}")
                        if len(name_list) + len(title) < 1000:
                            name_list += title+'\n'
                        else:
                            song_names_list.append(name_list)
                            name_list = title+'\n'
                    song_names_list.append(name_list)
                    log(guild_name, "QUEUED", f"youtube playlist ({len(playlist)} songs)")
                    done = embed.finished_prompt(self.bot)
                    await interaction.followup.send(embed = done)
                    msg = embed.queued_playlist_prompt(self.bot, song_names_list, len(playlist), title_or_link, 'Youtube')
                    await interaction.channel.send(embed=msg)
                    await self.music_player_start(interaction,reprint=True)
                else:
                    log(guild_name, 'ERROR', 'Youtube')
                    msg = embed.invalid_link(self.bot, title_or_link, 'Youtube')
                    await interaction.followup.send(embed= msg, ephemeral=True)
                return
            
            if 'open.spotify.com' in title_or_link:
                title_or_link = title_or_link.replace(' ','')
                if 'track' in title_or_link:
                    song = SpotifyGet(title_or_link, self.client_id, self.client_secret)
                    if song is None:
                        log(guild_name, 'ERROR', 'Spotify Song')
                        msg = embed.invalid_link(self.bot, title_or_link, 'Spotify Track')
                        await interaction.followup.send(embed= msg, ephemeral=True)
                        return
                    self.data.queue_song(guild_id, song)
                    log(guild_name, "QUEUED", f"Spotify Track ({song['title']})" )
                    msg = embed.queue_prompt(self.bot, song['title'])
                    await interaction.followup.send(embed= msg)
                    await self.music_player_start(interaction,reprint=True)
                elif 'playlist' in title_or_link:
                    playlist = SpotifyGet(title_or_link, self.client_id, self.client_secret)
                    if playlist is None:
                        log(guild_name, 'ERROR', 'Spotify Playlist')
                        msg = embed.invalid_link(self.bot, title_or_link, 'Spotify Playlist')
                        await interaction.followup.send(embed= msg, ephemeral=True)
                        return 
                    song_names_list = []
                    name_list = ''
                    last_ind = None
                    for ind, title in enumerate(playlist):
                        self.data.queue_song(guild_id,{'source': 'spotify', 'title': title})
                        last_ind = ind+1
                        title = embed.title(f"{last_ind}. {title}")
                        if len(name_list) + len(title) < 1000:
                            name_list += title+'\n'
                        else:
                            song_names_list.append(name_list)
                            name_list = title+'\n'
                    song_names_list.append(name_list)
                    log(guild_name, "QUEUED", f'Spotify Playlist ({len(playlist)} songs)' )
                    done = embed.finished_prompt(self.bot)
                    await interaction.followup.send(embed = done)
                    msg = embed.queued_playlist_prompt(self.bot, song_names_list, len(playlist), title_or_link, 'Spotify')
                    await interaction.channel.send(embed= msg)
                    await self.music_player_start(interaction,reprint=True)
                    pass
                else:
                    log(guild_name, 'ERROR', 'Spotify')
                    msg = embed.invalid_link(self.bot, title_or_link, 'Spotify')
                    await interaction.followup.send(embed= msg, ephemeral=True)
                return
            
            if 'https://' in title_or_link:
                log(guild_name, 'ERROR', 'playlist link')
                msg = embed.invalid_link(self.bot, title_or_link)
                await interaction.followup.send(embed= msg, ephemeral=True)
                return
            #title_or_link is not a link
            song = {'source': 'youtube', 'title': title_or_link}
            self.data.queue_song(guild_id, song)
            log(guild_name, "QUEUED", title_or_link)
            msg = embed.queue_prompt(self.bot, title_or_link)
            await interaction.followup.send(embed = msg)
            await self.music_player_start(interaction,reprint=True)
        except Exception as e:
            print(e)

    @app_commands.check(valid_play_command)
    @app_commands.command(name= "play_random", description="Play random songs from pocket bot library forever")
    async def play_random(self, interaction:discord.Interaction):
        guild_name = interaction.user.guild.name
        guild_id = interaction.user.guild.id
        self.data.initialize(interaction)
        
        await interaction.response.defer()
        if self.data.flip_random(guild_id) is True:
            log(guild_name, 'RANDOM SONG', 'On')
        else: 
            log(guild_name, 'RANDOM SONG', 'Off')
        await self.music_player_start(interaction)
        await interaction.delete_original_response()

    @app_commands.check(valid_play_command)
    @app_commands.command(name= "skip", description="Skips song")
    async def skip(self, interaction:discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guild_name = interaction.user.guild.name
        guild_id = interaction.user.guild.id
        log(guild_name, 'SKIP COMMAND')
        self.data.initialize(interaction)
        voice_client = interaction.client.get_guild(guild_id).voice_client
        if voice_client is None:
            msg = embed.skip_error_prompt(self.bot)
            await interaction.followup.send(embed= msg, ephemeral=True)
            return
        if (voice_client.is_playing() or voice_client.is_paused()):
            self.data.set_loop(guild_id, False)
            #current_song = self.data.get_current_song(guild_id)
            voice_client.stop()
            interaction.delete_original_response()
            await self.GUI_HANDLER(guild_id)
            return
        msg = embed.skip_error_prompt(self.bot)
        await interaction.followup.send(embed= msg, ephemeral=True)

    
    # @app_commands.check(valid_play_command)
    # @app_commands.command(name= "local_library", description="Search and play downloaded songs on bot server")
    # async def local_library(self, interaction:discord.Interaction, title_or_link:str):
    #     return
    #     guild_name = interaction.user.guild.name
    #     guild_id = interaction.user.guild.id
    #     self.data.initialize(interaction)
    #     local_song_list = os.listdir(LOCAL_MUSIC_PATH)
    #     title_or_link = title_or_link.lower()
    #     title_or_link_matches = [song for song in local_song_list if title_or_link in song.lower()]
    #     if not title_or_link_matches: #If there are no matches for title_or_link from list of songs
    #         emb_msg = embed.no_match(self.bot, title_or_link)
    #         await interaction.response.send_message(embed= emb_msg, ephemeral=True)
    #         await self.GUI_HANDLER(guild_id, reprint = True)
    #         return
    #     if len(title_or_link_matches) > 25:
    #         title_or_link_matches = title_or_link_matches[0:25]
    #     sview = SearchView(title_or_link_matches)
    #     emb_msg = embed.search_list_prompt(self.bot)
    #     await interaction.response.send_message(embed =emb_msg, view=sview, ephemeral=True)
    #     timeout = await sview.wait()
        
    #     if timeout is True:
    #         return
    #     song = sview.song_choice
    #     self.data.queue_song(guild_id, song)
    #     log(guild_name, "QUEUED", song['title'])
    #     await self.music_player_start(interaction)
    #     await interaction.delete_original_response()


######## LOOP TO AUTO CHANGE GUI ##############################################################
    @tasks.loop(seconds = 5)
    async def gui_loop(self):
        while self.gui_print:
            guild_id = self.gui_print.pop()
            await self.GUI_HANDLER(guild_id)
        
####### Auto Disconnect Bot After X Seconds idle
    @tasks.loop(minutes=3)
    async def disconnect_check(self):
        all_voice_connections = self.bot.voice_clients
        for voice in all_voice_connections:    
            guild_id = voice.guild.id
            last_idle = self.data.get_time(guild_id)
            if last_idle is None or voice.is_playing():
                self.data.set_idle_timestamp(guild_id)
                continue
            time_passed = (datetime.today()-last_idle).seconds
            timeout = Setting.get_timeout()
            if  time_passed > timeout:
                self.data.full_reset(guild_id)
                await voice.disconnect()
                await self.GUI_HANDLER(guild_id)
                log(voice.guild.name, 'VOICE DISCONNECTED (auto)', )


############# LISTENERS ########################################################################
    # Keep music player at bottom of channel
    @commands.Cog.listener() 
    async def on_message(self, message):
        guild_name = message.guild.name
        guild_id = message.guild.id
        if message.author.id != self.bot.user.id and message.channel.id == self.data.get_message(guild_id).channel.id:
            await self.GUI_HANDLER(guild_id, reprint = True)

    # RESET BOT FOR GUILD IF DISCONNECTED FROM VOICE CHANNEL
    @commands.Cog.listener()
    async def on_voice_state_update(self, member:discord.member.Member, before, after):
        if after.channel is not None:return
        users = self.bot.get_channel(before.channel.id).members
        if users == []: return
        guild_name = member.guild.name
        guild_id= member.guild.id
        connected_user_ids = [user.id for user in users]

        #Disconnects if bot is only one is channel
        if (len(connected_user_ids) == 1 and self.bot.user.id in connected_user_ids) or \
           (len(connected_user_ids) == 2 and self.bot.user.id in connected_user_ids and 990490227401453618 in connected_user_ids):
            voice_client = self.bot.get_guild(guild_id).voice_client
            self.data.reset(guild_id)
            if voice_client is not None:
                if voice_client.is_playing() or voice_client.is_paused():
                    self.gui_print.add(guild_id)
                    voice_client.stop()
                await voice_client.disconnect()
            log(guild_name, 'VOICE DISCONNECTED (no active users)', before.channel.name)
            await self.GUI_HANDLER(guild_id)

            return
        


#####################################################################################
    @commands.command(name= "sync", description= "Sync app commands with discord server")
    async def sync(self,ctx):
        guild_name = ctx.guild.name
        try:
            sync_num = await ctx.bot.tree.sync()
            log(guild_name, 'COMMANDS SYNCED', sync_num)
        except Exception as e:
            print(e)

#####################################################################################
class AddPlaylistModal(discord.ui.Modal, title='Save Playlist with Link'):
    name = discord.ui.TextInput(label='Name', required=True, placeholder='Name for your playlist')
    link = discord.ui.TextInput(label='Link', required=True, placeholder='Playlist Link (Spotify, Youtube, YTMusic))')
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(f'Thanks for your response, {self.name}{self.link}!', ephemeral=True)

class MusicFunctions(View):
    def __init__(self, music_cog, data:Guild_Music_Properties, guild_id):
        super().__init__(timeout=None)
        #self.add_item(self.SongSelectMenu(music_cog,data,guild_id))
        self.add_item(self.PreviousButton  (music_cog, data, guild_id))
        self.add_item(self.PlayPause       (music_cog, data, guild_id))
        self.add_item(self.NextButton      (music_cog, data, guild_id))
        self.add_item(self.ShuffleButton      (music_cog, data, guild_id))
        self.add_item(self.LoopButton      (music_cog, data, guild_id))
        #self.add_item(self.RandomButton    (music_cog, data, guild_id))
        #self.add_item(self.EmptyQueueButton    (music_cog, data, guild_id))
        #self.add_item(self.RandomSongButton(music_cog, data, guild_id))
        #self.add_item(self.AddPlaylistButton(music_cog, data, guild_id))
        self.add_item(self.ResetButton(music_cog, data, guild_id))
        self.add_item(self.DisconnectButton(music_cog, data, guild_id))
        
    async def interaction_check(self, interaction: discord.Interaction):
        user = interaction.user
        guild_name = interaction.user.guild.name
        guild_id = interaction.user.guild.id
        voice_client = interaction.client.get_guild(guild_id).voice_client
        access = False
        if user.voice is None:
            access = False
        elif voice_client is None:
            access = True
        elif voice_client.channel.id == user.voice.channel.id:
            access = True
        
        if access is True:
            log(guild_name, 'ACCESS GRANTED', user) 
            return True
        else:
            log(guild_name, 'ACCESS DENIED', user)
            await interaction.response.defer()
            return False

    class SongSelectMenu(Select):
        def __init__(self, music_cog, data:Guild_Music_Properties, guild_id):
            self.data      = data
            self.music_cog = music_cog
            self.guild_id  = guild_id
            options = []

            song_list = self.data.get_all_songs(guild_id)
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
            guild_name = interaction.user.guild.name
            log(guild_name, 'MENU OPTION', 'Clicked')
            guild_id = interaction.user.guild.id
            voice_client = interaction.client.get_guild(guild_id).voice_client
            song_title = self.values[0]
            if voice_client is None:
                await interaction.response.defer()
                return
            if (voice_client.is_playing() or voice_client.is_paused()):
                print('d')
                queue = self.data.get_queue()
                self.data.empty_queue()
                voice_client.stop()
                await interaction.response.defer()
                past_songs = self.data.get_history()[::-1]
                all_songs = past_songs+queue
                for i in range(len(all_songs)):
                    if song_title == all_songs['title']:
                        index = i
                self.data.set_queue(guild_id, all_songs[index:len(all_songs)])
                self.data.set_history(guild_id, all_songs[0:index])
                await self.music_cog.music_player_start(interaction) 
                return
            await interaction.response.defer()
            
    class PlayPause(Button):
        def __init__(self,music_cog, data:Guild_Music_Properties,guild_id):
            super().__init__(emoji = '⏯', style= discord.ButtonStyle.blurple)
            self.data = data
            self.music_cog = music_cog
            self.guild_id = guild_id
        async def callback(self, interaction: discord.Interaction):
            guild_name = interaction.user.guild.name
            voice_client = interaction.client.get_guild(self.guild_id).voice_client
            song = self.data.get_current_song(self.guild_id)
            if voice_client is None:
                self.style = discord.ButtonStyle.grey
                await interaction.response.edit_message(view=self.view)
                return
            if voice_client.is_playing() and not voice_client.is_paused():
                log(guild_name, 'PAUSED',song['title'])
                voice_client.pause()
                self.style = discord.ButtonStyle.grey
                await interaction.response.edit_message(view=self.view)
                return
            if not voice_client.is_playing() and voice_client.is_paused():
                log(guild_name, 'RESUMED',song['title'])
                self.style = discord.ButtonStyle.blurple
                await interaction.response.edit_message(view=self.view)
                voice_client.resume()
                return
            await interaction.response.defer()
            
    class RandomButton(Button):
        def __init__(self, music_cog, data:Guild_Music_Properties, guild_id):
            if data.get_random(guild_id) == True:
                style= discord.ButtonStyle.blurple
            else:
                style= discord.ButtonStyle.grey
            super().__init__(emoji='♾', label='Forever', style= style)
            self.data = data
            self.music_cog = music_cog
            self.guild_id = guild_id
        async def callback(self, interaction: discord.Interaction):
            guild_name = interaction.user.guild.name
            if self.data.flip_random(self.guild_id) is True:
                log(guild_name, 'RANDOM SONG', 'On')
                self.data.set_loop(self.guild_id, False)
                await self.music_cog.music_player_start(interaction) 
            else: 
                log(guild_name, 'RANDOM SONG', 'Off')
                await self.music_cog.GUI_HANDLER(self.guild_id)
            await interaction.response.defer()
    
    class PreviousButton(Button):
        def __init__(self,music_cog, data:Guild_Music_Properties, guild_id):
            super().__init__(emoji = "⏮", style= discord.ButtonStyle.blurple)
            self.data = data
            self.music_cog = music_cog
            self.guild_id = guild_id
        async def callback(self, interaction: discord.Interaction):
            guild_name = interaction.user.guild.name
            log(guild_name, 'PREVIOUS BUTTON', 'Clicked')
            voice_client = interaction.client.get_guild(self.guild_id).voice_client
            #IF VOICE RUNNING
            if voice_client is None:
                print('No voice_client')
                self.data.set_loop(self.guild_id, False)
                self.data.history_to_queue(self.guild_id)
                await interaction.response.defer()
                await self.music_cog.music_player_start(interaction) 
            elif voice_client.is_playing() or voice_client.is_paused():
                print('PLAYING OR PAUSED')
                self.data.flip_back(self.guild_id)
                self.data.set_loop(self.guild_id, False)
                voice_client.stop()
                await interaction.response.defer()
                await self.music_cog.music_player_start(interaction)
            else:
                print('Nothing Playing')
                self.data.set_loop(self.guild_id, False)
                self.data.flip_back(self.guild_id)
                self.data.history_to_queue(self.guild_id)
                voice_client.stop()
                await interaction.response.defer()
                await self.music_cog.music_player_start(interaction) 
     
    class NextButton(Button):
        def __init__(self,music_cog, data:Guild_Music_Properties, guild_id):
            super().__init__(emoji = "⏭", style= discord.ButtonStyle.blurple)
            self.data = data
            self.music_cog = music_cog
            self.guild_id = guild_id
        async def callback(self, interaction: discord.Interaction):
            guild_name = interaction.user.guild.name
            log(guild_name, 'NEXT BUTTON', 'Clicked')
            voice_client = interaction.client.get_guild(self.guild_id).voice_client
            if voice_client is None:
                await interaction.response.defer()
                return
            if (voice_client.is_playing() or voice_client.is_paused()):
                self.data.set_loop(self.guild_id, False)
                voice_client.stop()
                await interaction.response.defer()
                await self.music_cog.GUI_HANDLER(self.guild_id)
                return
            await interaction.response.defer()

    class ShuffleButton(Button):
        def __init__(self,music_cog, data:Guild_Music_Properties,guild_id):
            if data.get_shuffle(guild_id) is True:
                style= discord.ButtonStyle.blurple
            else:
                style= discord.ButtonStyle.grey
            super().__init__(emoji = "🔀", style= style)
            self.data = data
            self.music_cog = music_cog
            self.guild_id = guild_id
        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer()
            guild_name = interaction.user.guild.name
            log(guild_name, 'SHUFFLE BUTTON', 'Clicked')
            voice_client = interaction.client.get_guild(self.guild_id).voice_client
            if voice_client is None:
                return
            queue = self.data.get_queue(self.guild_id)
            history = self.data.get_history(self.guild_id)
            num_songs = len(queue)+len(history)
            if num_songs > 0 or voice_client.is_playing() or voice_client.is_paused():
                self.data.set_random(self.guild_id, False)
                self.data.set_loop(self.guild_id, False)
                self.data.flip_shuffle(self.guild_id)
                if self.data.get_shuffle(self.guild_id) is True:
                    await self.music_cog.music_player_start(interaction)
                await self.music_cog.GUI_HANDLER(self.guild_id)

    class LoopButton(Button):
        def __init__(self,music_cog, data:Guild_Music_Properties, guild_id):
            if data.get_loop(guild_id) is True:
                style= discord.ButtonStyle.blurple
            else:
                style= discord.ButtonStyle.grey
            super().__init__(emoji = "🔁", style=style)
            self.music_cog = music_cog
            self.data = data
        async def callback(self, interaction: discord.Interaction):
            guild_name = interaction.user.guild.name
            guild_id = interaction.user.guild.id
            voice_client = interaction.client.get_guild(guild_id).voice_client
            await interaction.response.defer()
            if voice_client is None:
                return
            if voice_client.is_playing() or voice_client.is_paused():
                song = self.data.get_current_song(guild_id)
                self.data.flip_loop(guild_id)
                self.data.set_random(guild_id, False)
                log(guild_name, 'LOOP', f"{song['title']}")
                await self.music_cog.GUI_HANDLER(guild_id)
                return
            
    
    class RandomSongButton(Button):
        def __init__(self,music_cog, data:Guild_Music_Properties, guild_id):
            super().__init__(label = 'Random Song', style= discord.ButtonStyle.blurple)
            self.data = data
            self.music_cog = music_cog
            self.guild_id = guild_id
        async def callback(self, interaction: discord.Interaction):
            guild_name = interaction.user.guild.name
            log(guild_name, 'MYSTERY BUTTON', 'Clicked')
            voice_client = interaction.client.get_guild(self.guild_id).voice_client
            add_random_song(self.data, self.guild_id)
            if voice_client is not None and (voice_client.is_playing() or voice_client.is_paused()):
                voice_client.stop()
            self.data.set_loop(self.guild_id, False)
            await interaction.response.defer()
            await self.music_cog.music_player_start(interaction) 

    class EmptyQueueButton(Button):
        def __init__(self,music_cog, data:Guild_Music_Properties, guild_id):
            super().__init__(emoji='🗑', label = 'Empty Queue', style=discord.ButtonStyle.grey)
            self.music_cog = music_cog
            self.data = data
            self.guild_id = guild_id
        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer()
            guild_name = interaction.user.guild.name
            log(guild_name, 'EMPTY QUEUE BUTTON', 'Clicked')
            guild_name = interaction.user.guild.name
            self.data.delete_queue(self.guild_id)
            # voice_client = interaction.client.get_guild(self.guild_id).voice_client
            # if voice_client is not None and (voice_client.is_playing() or voice_client.is_paused()):
            #     voice_client.stop()
            log(guild_name, 'QUEUE', 'empty')
            await self.music_cog.GUI_HANDLER(self.guild_id)

    class DisconnectButton(Button):
        def __init__(self,music_cog, data:Guild_Music_Properties, guild_id):
            super().__init__(label = 'Disconnect', style=discord.ButtonStyle.grey)
            self.music_cog = music_cog
            self.data = data
            self.guild_id = guild_id
        async def callback(self, interaction: discord.Interaction):
            guild_name = interaction.user.guild.name
            log(guild_name, 'DISCONNECT BUTTON', 'Clicked')
            voice_client = interaction.client.get_guild(self.guild_id).voice_client
            self.data.full_reset(self.guild_id)
            if voice_client is not None:
                if voice_client.is_playing() or voice_client.is_paused():
                    voice_client.stop()
                await voice_client.disconnect()
                log(guild_name, 'VOICE DISCONNECTED (force)')
            await interaction.response.defer()
            await self.music_cog.GUI_HANDLER(self.guild_id)

    class ResetButton(Button):
        def __init__(self,music_cog, data:Guild_Music_Properties, guild_id):
            super().__init__(emoji='🚽',label = 'Flush', style=discord.ButtonStyle.grey)
            self.music_cog = music_cog
            self.data = data
            self.guild_id = guild_id
        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            guild_name = interaction.user.guild.name
            log(guild_name, 'FLUSH BUTTON', 'Clicked')
            voice_client = interaction.client.get_guild(self.guild_id).voice_client
            self.data.reset(self.guild_id)
            if voice_client is not None:
                if voice_client.is_playing() or voice_client.is_paused():
                    voice_client.stop()
            self.data.full_reset(self.guild_id)
            #await interaction.response.send_message(embed=embed.flush_prompt(self.music_cog.bot),ephemeral=True)
            await self.music_cog.GUI_HANDLER(self.guild_id)

    class AddPlaylistButton(Button):
        def __init__(self,music_cog, data:Guild_Music_Properties, guild_id):
            super().__init__(emoji='➕',label = 'Playlist', style=discord.ButtonStyle.blurple)
            self.music_cog = music_cog
            self.data = data
            self.guild_id = guild_id
        async def callback(self, interaction: discord.Interaction):
            guild_name = interaction.user.guild.name
            log(guild_name, 'ADD PLAYLIST BUTTON', 'Clicked')
            await interaction.response.send_modal(AddPlaylistModal())
            #await self.music_cog.GUI_HANDLER(self.guild_id, reprint=True)
