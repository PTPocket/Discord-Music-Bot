import discord, os, random
from discord import app_commands, FFmpegPCMAudio
from discord.ext import commands, tasks
from tinytag import TinyTag
from cog.helper import embed
from cog.helper.guild_data import Guild_Music_Properties
from cog.helper.functions import *
from datetime import datetime


YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist':'True'}
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
FFMPEG_LOC = "C:\\Users\\p\\Downloads\\ffmpeg\\bin\\ffmpeg.exe"
LOCAL_MUSIC_PATH = "C:\\Users\\p\\Music"



class Music_Cog(commands.Cog):
    def __init__(self, bot:commands.Bot):
        self.bot = bot
        self.data = Guild_Music_Properties()
        self.gui_print = set()
        self.gui_loop.start()
        self.disconnect_check.start()
        self.timeout_min = 18



    async def GUI_HANDLER(self, guild_id, reprint = False, connect = False):
        try:
            player_embed = embed.gui_embed(self.bot, self.data, guild_id, connect = connect)
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
        except Exception as e: print(e)


    #MUSIC PLAYER LOOP (not recursive)
    def music_player(self, interaction:discord.Interaction, recall = False):
        
        guild_name = interaction.user.guild.name
        guild_id = interaction.user.guild.id
        
        if recall is True:
            self.data.current_to_history(guild_id)

        check_features(self.data, guild_id)
        if self.data.empty_queue(guild_id):
            send_log(guild_name, 'QUEUE', 'Empty')
            self.data.soft_reset(guild_id)
            self.gui_print.add(guild_id)
            return

        
        self.data.queue_to_current(guild_id)
        song = self.data.get_current_song(guild_id)
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
        player = discord.PCMVolumeTransformer(player, volume=0.15)
        send_log(guild_name, "NOW PLAYING", f'\"{song["title"]}\"')
        voice_client = interaction.client.get_guild(guild_id).voice_client
        self.data.set_voice(guild_id, voice_client)
        voice_client.play(player, after= lambda x=None: self.music_player(interaction, recall=True))
        return True
    
    #CHECKS IF MUSIC_PLAYER LOOP SHOULD START
    async def music_player_start(self, interaction:discord.Interaction):

        guild_name = interaction.user.guild.name
        guild_id = interaction.user.guild.id
        await voice_connect(interaction)
        voice_client = interaction.client.get_guild(guild_id).voice_client
        self.data.set_channel(guild_id, interaction.channel)
        connect_only = False
        if voice_client.is_playing() == voice_client.is_paused() == False and self.data.get_current_song(guild_id) is None:
            send_log(guild_name, 'MUSIC PLAYER', 'Start')
            try:
                self.music_player(interaction)
            except Exception as e:
                print(e)
                connect_only = True
        
        await self.GUI_HANDLER(guild_id, connect = connect_only)
        

#######PLAY FUNCTIONS######################################################
    @app_commands.check(valid_play_command)
    @app_commands.command(name= "play", description="Play song or add to song queue")
    async def play(self, interaction:discord.Interaction, song:str):
        guild_name = interaction.user.guild.name
        guild_id = interaction.user.guild.id
        self.data.initialize(interaction)

        await interaction.response.defer(ephemeral=True)
        query= song
        song = youtube_search(query)
        if song is None:
            send_log(guild_name, 'ERROR', 'Youtube Search')
            msg = embed.yt_search_error(self.bot, query)
            await interaction.followup.send(embed= msg, ephemeral=True)
            await self.GUI_HANDLER(guild_id)
        self.data.queue_song(guild_id, song)
        send_log(guild_name, "QUEUED", song['title'])
        await self.music_player_start(interaction)
        await interaction.delete_original_response()

    @app_commands.check(valid_play_command)
    @app_commands.command(name= "play_random", description="Play random songs from pocket bot library forever")
    async def play_random(self, interaction:discord.Interaction):
        guild_name = interaction.user.guild.name
        guild_id = interaction.user.guild.id
        self.data.initialize(interaction)
        

        await interaction.response.defer()
        if self.data.flip_random(guild_id) is True:
            send_log(guild_name, 'RANDOM SONG', 'On')
        else: 
            send_log(guild_name, 'RANDOM SONG', 'Off')
        await self.music_player_start(interaction)
        await interaction.delete_original_response()

        
    @app_commands.check(valid_play_command)
    @app_commands.command(name= "local_library", description="Search and play downloaded songs on bot server")
    async def local_library(self, interaction:discord.Interaction, query:str):
        guild_name = interaction.user.guild.name
        guild_id = interaction.user.guild.id
        self.data.initialize(interaction)
        local_song_list = os.listdir(LOCAL_MUSIC_PATH)
        query = query.lower()
        query_matches = [song for song in local_song_list if query in song.lower()]
        if not query_matches: #If there are no matches for query from list of songs
            emb_msg = embed.no_match(self.bot, query)
            await interaction.response.send_message(embed= emb_msg, ephemeral=True)
            await self.GUI_HANDLER(guild_id, reprint = True)
            return
        if len(query_matches) > 25:
            query_matches = query_matches[0:25]
        sview = SearchView(query_matches)
        emb_msg = embed.search_list_prompt(self.bot)
        await interaction.response.send_message(embed =emb_msg, view=sview, ephemeral=True)
        timeout = await sview.wait()
        
        if timeout is True:
            return
        song = sview.song_choice
        self.data.queue_song(guild_id, song)
        send_log(guild_name, "QUEUED", song['title'])
        await self.music_player_start(interaction)
        await interaction.delete_original_response()


######## LOOP TO AUTO CHANGE GUI ##############################################################
    @tasks.loop(seconds = 5)
    async def gui_loop(self):
        while self.gui_print:
            guild_id = self.gui_print.pop()
            await self.GUI_HANDLER(guild_id)
            print('Auto Print : GUI')
        
####### Auto Disconnect Bot After X Seconds idle
    @tasks.loop(minutes=1)
    async def disconnect_check(self):
        all_voice_connections = self.bot.voice_clients
        for voice in all_voice_connections:    
            guild_id = voice.guild.id
            last_idle = self.data.get_time(guild_id)
            if last_idle is None or voice.is_playing():
                self.data.set_idle_timestamp(guild_id)
                continue
            time_passed_sec = (datetime.today()-last_idle).seconds
            if  time_passed_sec > 60*self.timeout_min:
                await voice.disconnect()
                send_log(voice.guild.name, 'VOICE AUTO DISCONNECTED')



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
        guild_name = member.guild.name
        guild_id= member.guild.id

        users = self.bot.get_channel(before.channel.id).members
        if users == []: return
        usernames_only = [user.name for user in users]
        #Disconnects if bot is only one is channel
        if after.channel is None and self.bot.user.name in usernames_only and len(usernames_only) == 1:
            voice_client = self.bot.get_guild(guild_id).voice_client
            self.data.soft_reset(guild_id)
            if voice_client is not None:
                if voice_client.is_playing() or voice_client.is_paused():
                    self.gui_print.add(guild_id)
                    voice_client.stop()
                await voice_client.disconnect()
            send_log(guild_name, 'VOICE DISCONNECTED (empty)', before.channel.name)
            try:
                self.data.current_to_history(guild_id)
                await self.GUI_HANDLER(guild_id)
            except Exception as e: print(e)
            return

        if member.id == self.bot.user.id and after.channel is None:
            voice_client = self.bot.get_guild(guild_id).voice_client
            self.data.soft_reset(guild_id)
            if voice_client is not None:
                if voice_client.is_playing() or voice_client.is_paused():
                    self.gui_print.add(guild_id)
                    voice_client.stop()
            send_log(guild_name, 'VOICE DISCONNECTED (force)', before.channel.name)
            try:
                self.data.current_to_history(guild_id)
                await self.GUI_HANDLER(guild_id)
            except Exception as e: print(e)
            return



    
#####################################################################################
    @commands.command(name= "sync", description= "Sync app commands with discord server")
    async def sync(self,ctx):
        guild_name = ctx.guild.name
        try:
            sync_num = await ctx.bot.tree.sync()
            send_log(guild_name, 'COMMANDS SYNCED', sync_num)
        except Exception as e:
            print(e)



