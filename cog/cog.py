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
        self.to_print = []
        self.print_player.start()


    @tasks.loop(seconds = 5)
    async def print_player(self):
        while self.to_print:
            await print_music_player(self, self.to_print.pop(), self.data)
            print('printed')




    #MUSIC PLAYER LOOP (not recursive)
    def music_player(self, interaction:discord.Interaction, recall = False):
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
                if recall is True and guild_id not in self.to_print:
                    self.to_print.append(guild_id)
                elif guild_id in self.to_print:
                    self.to_print.pop(self.to_print.index(guild_id))
                send_log(guild_name, 'QUEUE', 'Empty')
                return
        
        song = self.data.queue_to_current(guild_id)

        if guild_id in self.to_print:
            self.to_print.pop(self.to_print.index(guild_id))
        elif recall is True:
            self.to_print.append(guild_id)
        #add to history
        if self.data.get_history(guild_id) == [] \
        or self.data.get_history(guild_id)[0]['title'] != song['title']:
            self.data.current_to_history(guild_id)


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
        bot_voice.play(player, after= lambda x=None: self.music_player(interaction, recall=True))

    #CHECKS IF MUSIC_PLAYER LOOP SHOULD START
    def music_player_start(self, interaction:discord.Interaction):
        guild_name = interaction.user.guild.name
        guild_id = interaction.user.guild.id
        bot_voice = interaction.client.get_guild(guild_id).voice_client
        self.data.set_channel(guild_id, interaction.channel)
        if bot_voice.is_playing() == bot_voice.is_paused() == False :
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
        await voice_connect(interaction)
        await interaction.response.defer(ephemeral=True)

        query= song
        song = youtube_search(query)
        if song is None:
            send_log(guild_name, 'ERROR', 'Youtube Search')
            msg = embed.yt_search_error(self.bot, query)
            await interaction.followup.send(embed= msg, ephemeral=True)
        self.data.queue_song(guild_id, song)
        self.music_player_start(interaction)
        await print_music_player(self, guild_id, self.data)
        await interaction.delete_original_response()
        


    @app_commands.check(valid_play_command)
    @app_commands.command(name= "play_random", description="Play random songs from pocket bot library forever")
    async def play_random(self, interaction:discord.Interaction):
        guild_name = interaction.user.guild.name
        guild_id = interaction.user.guild.id

        self.data.initialize(interaction)
        random_song = self.data.flip_random(guild_id)
        await interaction.response.defer()
        if random_song is True:
            await voice_connect(interaction)
            send_log(guild_name, 'RANDOM SONG', 'On')
            self.music_player_start(interaction)
        else: 
            send_log(guild_name, 'RANDOM SONG', 'Off')
        await interaction.delete_original_response()
        await print_music_player(self, guild_id, self.data)
        



    @app_commands.check(valid_play_command)
    @app_commands.command(name= "flac", description="Search and play downloaded songs on bot server")
    async def flac(self, interaction:discord.Interaction, query:str):
        guild_name = interaction.user.guild.name
        guild_id = interaction.user.guild.id
        self.data.initialize(interaction)
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
        
        if timeout is True:
            return
        song = sview.song_choice
        self.data.queue_song(guild_id, song)
        send_log(guild_name, "Queued", song['title'])
        await voice_connect(interaction)
        self.music_player_start(interaction)
        await print_music_player(self, guild_id, self.data)
        await interaction.delete_original_response()

        



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


        
    
    @commands.Cog.listener() #keep music player at bottom of channel
    async def on_message(self, message):
        guild_name = message.guild.name
        guild_id = message.guild.id

        if message.author.id == self.bot.user.id:
            return
        await print_music_player(self, guild_id, self.data)


        
        
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


