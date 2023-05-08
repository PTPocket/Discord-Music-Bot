import discord, asyncio, json, os
from discord import app_commands, FFmpegPCMAudio
from discord.ext import commands, tasks
from yt_dlp import YoutubeDL
from datetime import datetime, timedelta
from discord.ui import Button, View
from cog import embed


YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist':'True'}
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
PLAYLIST_FILENAME = "cog/playlists.json"
def print_log(text, guild_id):
    time= str(datetime.now())
    msg = f"{time} | Guild ID: {guild_id} | Master Pocket Bot - {text}"
    print(msg)
    


class music_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.song_queues = {}
        self.current_song = {}
        self.loop_song = {}


#####STATIC FUNCTIONS########################################################
    #Searches Youtube
    #   Input  : song name(string)
    #   Returns: song url and title(Dictionary)
    def search_yt(self, query):
        with YoutubeDL(YDL_OPTIONS) as ydl:
            try: 
                info = ydl.extract_info("ytsearch:%s" % query, download=False)['entries'][0]
            except Exception: 
                return None
        return {'source': info['url'], 'title': info['title']}

    async def valid_play_command(interaction:discord.Interaction):
        user = interaction.user
        authorized = None
        bot_voice = interaction.client.get_guild(user.guild.id).voice_client

        if user.voice is None:
            authorized = False
        elif bot_voice is None or not bot_voice.is_connected():
            authorized = True
        elif user.voice.channel.id == bot_voice.channel.id:
            authorized = True
        else:
            authorized = False

        if not authorized:
            msg = embed.unauthorized(interaction.client)
            await interaction.response.send_message(embed= msg)
            print_log(f"ACCESS DENIED -> {user}",user.guild.id)
        else:
            print_log(f"ACCESS GRANTED -> {user}",user.guild.id)
        return authorized
    
    async def valid_user_REGULAR_FUNC(interaction:discord.Interaction):
        user = interaction.user
        authorized = None
        bot_voice = interaction.client.get_guild(user.guild.id).voice_client
        if user.voice is None or \
                bot_voice is None or \
                not bot_voice.is_connected():
            authorized = False
        elif bot_voice.channel.id == user.voice.channel.id:
            authorized =  True
        else: 
            authorized =  False

        if authorized is False:
            msg = embed.unauthorized(interaction.client)
            await interaction.response.send_message(embed= msg)  
        return authorized
    
    def start_queue(self, bot_voice, guild_id):
        if self.loop_song[guild_id] is True:
            self.song_queues[guild_id].insert(0,self.current_song[guild_id])
        if not self.song_queues[guild_id]:
            self.current_song[guild_id] = None
            print_log(f"QUEUE EMPTY",guild_id)
            return

        self.current_song[guild_id]= self.song_queues[guild_id].pop(0)
        try:
            player = FFmpegPCMAudio(
                self.current_song[guild_id]['source'],
                **FFMPEG_OPTIONS)
        except Exception as e:
            print_log(e,guild_id)
        print_log(f"PLAYING -> '{self.current_song[guild_id]['title']}'",guild_id)
        bot_voice.play(player, after= lambda x=None: self.start_queue(bot_voice, guild_id))
        
############COMMANDS#################################################################
    @app_commands.check(valid_play_command)
    @app_commands.command(name= "play", description="Play song or add to song queue")
    async def play(self, interaction:discord.Interaction, song:str):

        user = interaction.user
        guild_id = user.guild.id
        bot_voice = interaction.client.get_guild(guild_id).voice_client
        if bot_voice is None:
            self.song_queues[guild_id]   = []
            self.current_song[guild_id]  = None
            self.loop_song[guild_id]     = False
            try:
                await user.voice.channel.connect()
            except Exception as e:
                print_log(e,guild_id)
            print_log(f"CONNECTED -> '{user.voice.channel}' voice channel",guild_id)
            bot_voice = interaction.client.get_guild(guild_id).voice_client
        else:
            # Already exists
            if not bot_voice.is_connected():
                await bot_voice.move_to(user.voice.channel)
                print_log(f"RECONNECTED -> '{user.voice.channel}' voice channel",guild_id)

        await interaction.response.defer()
        query= song
        print_log(f"SEARCHING YOUTUBE -> '{query}'",guild_id)
        song = self.search_yt(song)
        if song is None:
            msg = embed.yt_search_error(self.bot, query)
            await interaction.followup.send(embed= msg)
            print_log(f"YOUTUBE SEARCH ERROR -> '{query}'",guild_id)
            return
        song['query'] = query
        self.song_queues[guild_id].append(song)
        print_log(f"QUEUED -> '{song['title']}'",guild_id)

        if self.current_song[guild_id] is None:
            self.current_song[guild_id]= self.song_queues[guild_id].pop(0)
            play_emb= embed.play(self.bot, song['title'])
            await interaction.followup.send(embed = play_emb)
            try:
                player = FFmpegPCMAudio(
                    self.current_song[guild_id]['source'],
                    **FFMPEG_OPTIONS)
            except Exception as e:
                print_log(e,guild_id)
            print_log(f"PLAYING -> '{self.current_song[guild_id]['title']}'",guild_id)
            bot_voice.play(player, after= lambda x=None: self.start_queue(bot_voice, guild_id))
        else:
            queue_sum_emb = embed.queue_summary(self.bot, self.song_queues[guild_id])
            await interaction.followup.send(embed= queue_sum_emb)

    @app_commands.check(valid_user_REGULAR_FUNC)
    @app_commands.command(name="pause", description= "Pause Song")
    async def pause(self, interaction:discord.Interaction):
        user = interaction.user
        guild_id = user.guild.id
        current_song = self.current_song[guild_id]
        bot_voice = interaction.client.get_guild(guild_id).voice_client
        if bot_voice.is_playing() and not bot_voice.is_paused():
            print_log(f"PAUSED -> '{current_song['title']}'",guild_id)
            bot_voice.pause()
            await interaction.response.send_message(embed = embed.pause(self.bot, current_song['title']))
        else:
            await interaction.response.send_message(embed = embed.pause_err(self.bot, current_song))
    
    @app_commands.check(valid_user_REGULAR_FUNC)
    @app_commands.command(name="resume", description= "Resume Song")
    async def resume(self, interaction:discord.Interaction):
        user = interaction.user
        guild_id = user.guild.id
        current_song = self.current_song[guild_id]
        bot_voice = interaction.client.get_guild(guild_id).voice_client
        if not bot_voice.is_playing() and bot_voice.is_paused():
            print_log(f"RESUMED -> '{current_song['title']}'",guild_id)
            bot_voice.resume()
            await interaction.response.send_message(embed = embed.resume(self.bot, current_song['title']))
        else:
            await interaction.response.send_message(embed = embed.resume_err(self.bot, current_song))

    @app_commands.check(valid_user_REGULAR_FUNC)
    @app_commands.command(name="loop", description= "Loop currently playing song")
    async def loop(self, interaction:discord.Interaction):
        user = interaction.user
        msg= None
        guild_id = user.guild.id
        current_song = self.current_song[guild_id]
        if current_song is not None:
            if self.loop_song[guild_id] is False:
                self.loop_song[guild_id] = True
                print_log(f"LOOP START-> {current_song['title']}",guild_id)
                msg = embed.loop(self.bot, current_song['title'], True)
            else:
                self.loop_song[guild_id] = False
                print_log(f"LOOP STOP-> {current_song['title']}",guild_id)
                msg = embed.loop(self.bot, current_song['title'], False)
        else:
            msg = embed.loop(self.bot, None, None)
        await interaction.response.send_message(embed = msg)
    
    @app_commands.check(valid_user_REGULAR_FUNC)
    @app_commands.command(name="skip", description= "Skip song")
    async def skip(self, interaction:discord.Interaction):
        user = interaction.user
        msg= None
        guild_id = user.guild.id
        current_song = self.current_song[guild_id]
        bot_voice = interaction.client.get_guild(guild_id).voice_client
        if current_song is not None:
            self.loop = False
            print_log(f"SKIP -> {current_song['title']}",guild_id)
            bot_voice.stop()
            msg = embed.skip(self.bot, current_song['title'])
        else:
            msg = embed.skip(self.bot , None)
        await interaction.response.send_message(embed= msg)

    @app_commands.check(valid_user_REGULAR_FUNC)
    @app_commands.command(name="delete", description= "Deletes a song from queue. Position starts from 0.")
    async def delete(self, interaction:discord.Interaction, pos: int):
        user = interaction.user
        guild_id = user.guild.id
        if pos < len(self.song_queues[guild_id]) and pos >= 0:
            del self.song_queues[guild_id][pos]
            queue_sum_emb = embed.queue_summary(self.bot, self.song_queues[guild_id])
            await interaction.response.send_message(embed= queue_sum_emb)
        else:
            queue_sum_emb = embed.queue_summary(self.bot, self.song_queues[guild_id])
            await interaction.response.send_message(embed= queue_sum_emb)

    @app_commands.check(valid_user_REGULAR_FUNC)
    @app_commands.command(name="queue", description= "Shows queue list")
    async def queue(self, interaction:discord.Interaction):
        user = interaction.user
        guild_id = user.guild.id
        if guild_id not in self.song_queues:
            queue_sum_emb = embed.queue_summary(self.bot, [])
        else:
            queue_sum_emb = embed.queue_summary(self.bot, self.song_queues[guild_id])
        await interaction.response.send_message(embed= queue_sum_emb)

    @app_commands.command(name="create_playlist", description= "Create a playlist with a name")
    async def create_playlist(self, interaction: discord.Interaction, name: str):
        user = interaction.user
        user_id = str(user.id)
        name = name.upper()
        if not os.path.exists(PLAYLIST_FILENAME):
            with open(PLAYLIST_FILENAME, 'w') as playlist_file:
                json.dump({}, playlist_file)

        playlists_by_id = None
        with open(PLAYLIST_FILENAME, 'r') as playlist_file:
            playlists_by_id = json.load(playlist_file)
            if playlists_by_id == {}:
                playlists_by_id[user_id] = {}
            elif user_id in playlists_by_id and name in playlists_by_id[user_id]:
                emb_msg = embed.playlist_exists(self.bot)
                await interaction.response.send_message(embed=emb_msg, ephemeral=True)
            playlists_by_id[user_id][name] = []
        with open(PLAYLIST_FILENAME, 'w') as playlist_file:
            json.dump(playlists_by_id, playlist_file)

        emb_msg = embed.created_playlist(self.bot, name)
        await interaction.response.send_message(embed=emb_msg, ephemeral=True)
    
    class playlist_View(View):
        def __init__(self, playlists, song, playlists_by_id):
            super().__init__()
            for playlist in playlists:
                button = self.playlist_Button(playlist, song, playlists_by_id)
                self.add_item(button)

        class playlist_Button(Button):
            def __init__(self, label, song, playlists_by_id):
                super().__init__(label=label)
                self.name = label
                self.song = song
                self.playlists_by_id = playlists_by_id

            async def callback(self, interaction: discord.Interaction):
                self.playlists_by_id[str(interaction.user.id)][self.name].append(self.song)
                with open(PLAYLIST_FILENAME, 'w') as p_file:
                    json.dump(self.playlists_by_id, p_file)
                emb_msg = embed.add_success(self.name, self.song)
                await interaction.response.edit_message(embed = emb_msg,view=None)

                self.stop()
        



    @app_commands.command(name="add_to_playlist", description= "Add a song to your playlist")
    async def add_to_playlist(self, interaction: discord.Interaction, song: str):
        user = interaction.user
        user_id = str(user.id)
        guild_name = user.guild.name
        if not os.path.exists(PLAYLIST_FILENAME):
            msg = embed.add_to_playlist_error(self.bot)
            await interaction.response.send_message(embed = msg, ephemeral=True)
            return

        print_log(f"SEARCHING YOUTUBE -> '{song}'",guild_name)
        song = self.search_yt(song)
        if song is None:
            msg = embed.yt_search_error(self.bot, song)
            await interaction.response.send_message(embed= msg, ephemeral=True)
            print_log(f"YOUTUBE SEARCH ERROR -> '{song}'",guild_name)
            return
        
        playlists_by_id = None
        with open(PLAYLIST_FILENAME, 'r+') as playlist_file:
            playlists_by_id = json.load(playlist_file)

        pl_view = self.playlist_View(playlists_by_id[user_id], song, playlists_by_id)
        print('here')
        try:
            emb_msg = embed.adding_to_playlist(self.bot, song['title'])
            await interaction.response.send_message(embed=emb_msg,view= pl_view, ephemeral=True)
            timeout = await pl_view.wait()
        except Exception as e:
            print(e)
        print("hi")
        print("test")

        

        
##########LISTENERS#################################################################
    @commands.Cog.listener() #RESET BOT FOR GUILD IF DISCONNECTED FROM VOICE CHANNEL
    async def on_voice_state_update(self, member, before, after):
        guild_id= member.guild.id
        if member.id == self.bot.user.id:
            bot_voice = self.bot.get_guild(guild_id).voice_client
            if after.channel is None:
                self.song_queues[guild_id]= []
                self.loop_song[guild_id] = False
                self.current_song[guild_id] = None
                if bot_voice is not None and (bot_voice.is_playing() or bot_voice.is_paused()):
                    bot_voice.stop()
                print_log("RESET", guild_id)
                return




#####################################################################################
    @commands.command(name= "sync", description= "Sync app commands with discord server")
    async def sync(self,ctx):
        print_log("SYNCING COMMANDS", None)
        try:
            synced = await ctx.bot.tree.sync()
            print_log(f"SYNCED {len(synced)} COMMAND(S)",None)
        except Exception as e:
            print_log(e, None)