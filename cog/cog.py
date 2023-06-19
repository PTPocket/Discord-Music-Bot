import discord, os, random

from discord import app_commands, FFmpegPCMAudio
from discord.ext import commands, tasks
from tinytag import TinyTag
from cog import embed
from cog.help_functions import *


YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist':'True'}
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
FFMPEG_LOC = "C:\\Users\\SERVER\\Documents\\ffmpeg\\bin\\ffmpeg.exe"
LOCAL_MUSIC_PATH = "C:\\Users\\SERVER\\Music"

class Music_Cog(commands.Cog):
    def __init__(self, bot:commands.Bot):
        self.bot = bot
        self.data = Guild_Music_Properties()
        self.song_print_loop.start()
        
    #prints current song
    @tasks.loop(seconds=5)
    async def song_print_loop(self):
        for guild_id in self.data.get_guild_ids():
            if self.data.get_channel(guild_id) is None:
                continue

            #If its history is empty
            song = self.data.get_current_song(guild_id) 
            if self.data.empty_history(guild_id) or self.data.get_history(guild_id)[0] != song:
                await print_music_player(self, guild_id, self.data)
                self.data.current_to_history(guild_id)


            


    #MUSIC PLAYER LOOP (not recursive)
    def music_player(self, interaction:discord.Interaction):
        guild_name = interaction.user.guild.name
        guild_id = interaction.user.guild.id
        bot_voice = interaction.client.get_guild(guild_id).voice_client
        
        if self.data.get_loop(guild_id) is True:
            self.data.current_to_queue(guild_id)
        elif self.data.empty_queue(guild_id):
            if self.data.get_random(guild_id) is True:
                flac_song_list = os.listdir(LOCAL_MUSIC_PATH)
                song = random.choice(flac_song_list)
                path = LOCAL_MUSIC_PATH + '\\'+ song
                song_metadata = TinyTag.get(path)
                title = f"{song_metadata.title} - {song_metadata.artist}"
                song = {'title': title, 'source': f'{LOCAL_MUSIC_PATH}\{song}'}
                self.data.queue_song(guild_id, song)
            else:
                self.data.soft_reset(guild_id)
                send_log(guild_name, 'QUEUE', 'Empty')
                return
        song = self.data.queue_to_current(guild_id)
        if '.mp3' in song['source']\
            or '.flac' in song['source']:
            player = FFmpegPCMAudio(
                song['source'],
                executable=FFMPEG_LOC)
        else:
            player = FFmpegPCMAudio(
                song['source'],
                **FFMPEG_OPTIONS,
                executable= FFMPEG_LOC)

        send_log(guild_name, "Now Playing", f'\"{song["title"]}\"')
        bot_voice.play(player, after= lambda x=None: self.music_player(interaction))

    #CHECKS IF MUSIC_PLAYER LOOP SHOULD START
    def music_player_start(self, interaction:discord.Interaction):
        guild_name = interaction.user.guild.name
        guild_id = interaction.user.guild.id
        bot_voice = interaction.client.get_guild(guild_id).voice_client
        if bot_voice.is_playing() == bot_voice.is_paused() == False:
            send_log(guild_name, 'MUSIC PLAYER', 'Start')
            self.music_player(interaction)
            return True
        return False
    
#######PLAY FUNCTIONS######################################################
    @app_commands.check(valid_play_command)
    @app_commands.command(name= "play", description="Play song or add to song queue")
    async def play(self, interaction:discord.Interaction, song:str):
        guild_name = interaction.user.guild.name
        guild_id = interaction.user.guild.id
        self.data.initialize(interaction)

        self.data.set_channel(guild_id, interaction.channel)
        await voice_connect(interaction)
        await interaction.response.defer(ephemeral=True)
        query= song
        song = youtube_search(query)
        if song is None:
            send_log(guild_name, 'ERROR', 'Youtube Search')
            msg = embed.yt_search_error(self.bot, query)
            await interaction.followup.send(embed= msg, ephemeral=True)
        self.data.queue_song(guild_id, song)
        self.data.set_current_song(guild_id, song)
        send_log(guild_name, "Queued", song['title'])
        embed_msg = embed.queued(song)
        await interaction.followup.send(embed = embed_msg, ephemeral=True)
        if self.music_player_start(interaction) is False:
            await print_music_player(self, guild_id, self.data)


    @app_commands.check(valid_play_command)
    @app_commands.command(name= "play_random", description="Play random songs from pocket bot library forever")
    async def play_random(self, interaction:discord.Interaction):
        guild_name = interaction.user.guild.name
        guild_id = interaction.user.guild.id

        self.data.initialize(interaction)
        self.data.set_channel(guild_id, interaction.channel)
        random_song = self.data.flip_random(guild_id)
        await interaction.response.send_message('-_-', ephemeral=True)
        if random_song is True:
            await voice_connect(interaction)
            send_log(guild_name, 'RANDOM SONG', 'On')
            if self.music_player_start(interaction) is False:
                await print_music_player(self, guild_id, self.data)
        else: 
            send_log(guild_name, 'RANDOM SONG', 'Off')
            await print_music_player(self, guild_id, self.data)


    @app_commands.check(valid_play_command)
    @app_commands.command(name= "flac", description="Search and play downloaded songs on bot server")
    async def flac(self, interaction:discord.Interaction, query:str):
        guild_name = interaction.user.guild.name
        guild_id = interaction.user.guild.id
        self.data.initialize(interaction)
        self.data.set_channel(guild_id, interaction.channel)
        local_song_list = os.listdir(LOCAL_MUSIC_PATH)
        query = query.lower()
        query_matches = [song for song in local_song_list if query in song.lower()]
        if not query_matches: #If there are no matches for query from list of songs
            emb_msg = embed.no_match(self.bot, query)
            await interaction.response.send_message(embed= emb_msg, ephemeral=True)
            return
        if len(query_matches) > 25:
            query_matches = query_matches[0:25]
        sview = SearchView(query_matches)
        emb_msg = embed.search_list_prompt(self.bot)
        await interaction.response.send_message(embed =emb_msg, view=sview, ephemeral=True)
        timeout = await sview.wait()
        await interaction.delete_original_response()
        if timeout is True:
            return
        song = sview.song_choice
        self.data.queue_song(guild_id, song)
        send_log(guild_name, "Queued", song['title'])
        embed_msg = embed.queued(song)
        await interaction.followup.send(embed = embed_msg, ephemeral=True)
        await voice_connect(interaction)
        if self.music_player_start(interaction) is False:
            await print_music_player(self, guild_id, self.data)



#######MUSIC PLAYER GENERAL FUNCTIONS######################################################
    @app_commands.check(valid_user_REGULAR_FUNC)
    @app_commands.command(name="skip", description= "Skip song")
    async def skip(self, interaction:discord.Interaction):
        guild_name = interaction.user.guild.name
        guild_id = interaction.user.guild.id
        bot_voice = interaction.client.get_guild(guild_id).voice_client

        if bot_voice.is_playing() or bot_voice.is_paused():
            song = self.data.get_current_song(guild_id)
            self.data.set_loop(guild_id, False)
            send_log(guild_name, 'SKIP', f"{song['title']}")
            bot_voice.stop()
            msg = embed.skip(self.bot, song['title'])
            await interaction.response.send_message(embed= msg)
        else:
            msg = embed.skip(self.bot , None)
            await interaction.response.send_message(embed= msg)


        


        
        

#####################################################################################
    @commands.Cog.listener() #RESET BOT FOR GUILD IF DISCONNECTED FROM VOICE CHANNEL
    async def on_voice_state_update(self, member, before, after):
        guild_name = member.guild.name
        description = 'Voice Disconnected'
        guild_id= member.guild.id

        if member.id == self.bot.user.id and after.channel is None:
            self.data.soft_reset(guild_id)
            send_log(guild_name, description)



            
#####################################################################################
    @commands.command(name= "sync", description= "Sync app commands with discord server")
    async def sync(self,ctx):
        log_name = ctx.guild.name
        description = 'SYNCED COMMANDS'
        try:
            try:
                await ctx.bot.tree.sync()
            except Exception as e:
                pass
            send_log(log_name, description)
        except Exception as e:
            print(e)


