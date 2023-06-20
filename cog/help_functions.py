import discord, os, random, time
from tinytag import TinyTag
from discord import FFmpegPCMAudio
from discord.ui import View, Select, Button
from datetime import datetime
from yt_dlp import YoutubeDL
from cog import embed
BLANK = '\u200b'
YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist':'True'}
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
FFMPEG_LOC = "C:\\Users\\SERVER\\Documents\\ffmpeg\\bin\\ffmpeg.exe"
LOCAL_MUSIC_PATH = "C:\\Users\\SERVER\\Music"

def send_log(log_name, description, result = ''):
    time= str(datetime.now())
    print(f"{time} | Guild : {log_name} | {description} -> {result}")

####CHECK IF USER HAS ACCESS
async def valid_play_command(interaction:discord.Interaction):
    #for log print
    user = interaction.user
    guild_name = interaction.user.guild.name
    guild_id = interaction.user.guild.id

    bot_voice = interaction.client.get_guild(guild_id).voice_client
    authorized = None
    if user.voice is None:
        authorized = False
    elif bot_voice is None or not bot_voice.is_connected():
        authorized = True
    elif user.voice.channel.id == bot_voice.channel.id:
        authorized = True
    else:
        authorized = False

    if not authorized:
        send_log(guild_name, 'ACCESS DENIED', user)
        msg = embed.unauthorized(interaction.client)
        await interaction.response.send_message(embed= msg)
    else:
        send_log(guild_name, 'ACCESS GRANTED', user)
    
    
    return authorized
####CHECK IF USER HAS ACCESS
async def valid_user_REGULAR_FUNC(interaction:discord.Interaction):
    user = interaction.user
    guild_name = interaction.user.guild.name
    guild_id = interaction.user.guild.id
    authorized = None
    bot_voice = interaction.client.get_guild(guild_id).voice_client

    if user.voice is None or \
    bot_voice is None or \
    not bot_voice.is_connected():
        authorized = False
    elif bot_voice.channel.id == user.voice.channel.id:
        authorized =  True
    else: 
        authorized =  False

    if authorized is False:
        send_log(guild_name, 'ACCESS DENIED', user)
        msg = embed.unauthorized(interaction.client)
        await interaction.response.send_message(embed= msg)
    else: send_log(guild_name, 'ACCESS GRANTED', user) 
    return authorized

async def voice_connect(interaction:discord.Interaction):
    user = interaction.user
    guild_name = interaction.user.guild.name
    guild_id = interaction.user.guild.id
    bot_voice = interaction.client.get_guild(guild_id).voice_client

    if bot_voice is None:
        try:
            await user.voice.channel.connect()
            bot_voice = interaction.client.get_guild(guild_id).voice_client
            send_log(guild_name, 'Voice Connected', bot_voice.channel.name)
        except Exception as e:
            print(e)
    else:
        # Already exists
        if not bot_voice.is_connected():
            await bot_voice.move_to(user.voice.channel)
            send_log(guild_name, 'Voice Reconnected', bot_voice.channel.name)

def youtube_search(query):
    with YoutubeDL(YDL_OPTIONS) as ydl:
        try: 
            info = ydl.extract_info("ytsearch:%s" % query, download=False)['entries'][0]
        except Exception as e: 
            print(e)
            return None
    return {'source': info['url'], 'title': info['title']}


class SearchView(View):
    def __init__(self, song_list):
        super().__init__(timeout=30)
        self.add_item(self.SongSelectMenu(song_list))
        self.song_choice = None
    class SongSelectMenu(Select):
        def __init__(self, song_list):
            options = []
            for i, song in enumerate(song_list):
                path = LOCAL_MUSIC_PATH + '\\'+ song
                file = TinyTag.get(path)
                options.append(discord.SelectOption(
                    label = f"{file.title} - {file.artist}",
                    value = i
                ))
            super().__init__(placeholder='Search Results', options = options)
            self.song_list = song_list
        async def callback(self, interaction:discord.Interaction):
            song = self.song_list[int(self.values[0])]
            path = LOCAL_MUSIC_PATH + '\\'+ song
            song_metadata = TinyTag.get(path)
            title = f"{song_metadata.title} - {song_metadata.artist}"
            song = {'title': title, 'source': f'{path}'}
            self.view.song_choice = song
            self.view.stop()
            await interaction.response.send_message()

class MusicFunctions(View):
    def __init__(self,music_cog,guild_id, data):
        super().__init__(timeout=None)
        self.bot = music_cog.bot
        self.add_item(self.PreviousButton(music_cog, data,guild_id))
        self.add_item(self.PlayPause(music_cog, data,guild_id))
        self.add_item(self.NextButton(music_cog, data,guild_id))
        #self.add_item(self.LoopButton(data,guild_id))
        self.add_item(self.RandomButton(music_cog, data,guild_id))
        
    class PreviousButton(Button):
        def __init__(self,music_cog, data, guild_id):
            super().__init__(emoji = "⏮", style= discord.ButtonStyle.blurple)
            self.data = data
            self.music_cog = music_cog
        async def callback(self, interaction: discord.Interaction):
            guild_name = interaction.user.guild.name
            guild_id = interaction.user.guild.id
            bot_voice = interaction.client.get_guild(guild_id).voice_client
            

            if self.data.get_history(guild_id) == []:
                return


            if bot_voice.is_playing() or bot_voice.is_paused():
                if len(self.data.get_history(guild_id)) == 1:
                    recent = self.data.data[guild_id]['history'].pop(0)
                    self.data.prepend_to_queue(guild_id, recent)
                else:
                    recent = self.data.data[guild_id]['history'].pop(0)
                    self.data.prepend_to_queue(guild_id, recent)
                    recent = self.data.data[guild_id]['history'].pop(0)
                    self.data.prepend_to_queue(guild_id, recent)
                send_log(guild_name, 'LAST TRACK')
                self.data.set_loop(guild_id, False)
                self.music_cog.to_print.append(guild_id)
                bot_voice.stop()
                await interaction.response.defer()
                await print_music_player(self.music_cog, guild_id, self.data)
            else:
                recent = self.data.data[guild_id]['history'].pop(0)
                self.data.prepend_to_queue(guild_id, recent)
                await voice_connect(interaction)
                self.music_cog.to_print.append(guild_id)
                self.music_cog.music_player_start(interaction)
                await interaction.response.defer()
                await print_music_player(self.music_cog, guild_id, self.data)

                    

    class PlayPause(Button):
        def __init__(self,music_cog, data,guild_id):
            super().__init__(emoji = '⏯', style= discord.ButtonStyle.blurple )
            self.data = data
            self.music_cog = music_cog

        async def callback(self, interaction: discord.Interaction):
            guild_name = interaction.user.guild.name
            guild_id = interaction.user.guild.id
            bot_voice = interaction.client.get_guild(guild_id).voice_client
            song = self.data.get_current_song(guild_id)
            if bot_voice.is_playing() and not bot_voice.is_paused():
                send_log(guild_name, 'PAUSED',song['title'])
                bot_voice.pause()
                self.style = discord.ButtonStyle.grey
                await interaction.response.edit_message(view=self.view)
            elif not bot_voice.is_playing() and bot_voice.is_paused():
                send_log(guild_name, 'RESUMED',song['title'])
                bot_voice.resume()
                self.style = discord.ButtonStyle.blurple
                await interaction.response.edit_message(view=self.view)
            await interaction.response.defer()

    class RandomButton(Button):
        def __init__(self, music_cog, data, guild_id):
            if data.get_random(guild_id) == True:
                style= discord.ButtonStyle.blurple
            else:
                style= discord.ButtonStyle.grey
            super().__init__(label = 'Random Song', style= style)
            self.data = data
            self.music_cog = music_cog
        async def callback(self, interaction: discord.Interaction):
            guild_name = interaction.user.guild.name
            guild_id = interaction.user.guild.id
            random_song = self.data.flip_random(guild_id)
            if random_song:
                send_log(guild_name, 'RANDOM SONG', 'On')
                await voice_connect(interaction)
                self.music_cog.music_player_start(interaction)
                await print_music_player(self.music_cog, guild_id, self.data)
            else: 
                send_log(guild_name, 'RANDOM SONG', 'Off')
                await print_music_player(self.music_cog, guild_id, self.data)
            await interaction.response.send_message()

    class NextButton(Button):
        def __init__(self,music_cog, data, guild_id):
            super().__init__(emoji = "⏭", style= discord.ButtonStyle.blurple)
            self.data = data
            self.music_cog = music_cog
        async def callback(self, interaction: discord.Interaction):
            guild_name = interaction.user.guild.name
            guild_id = interaction.user.guild.id
            bot_voice = interaction.client.get_guild(guild_id).voice_client
            
            if bot_voice.is_playing() or bot_voice.is_paused():
                song = self.data.get_current_song(guild_id)
                send_log(guild_name, 'SKIP', f"{song['title']}")
                self.data.set_loop(guild_id, False)
                self.music_cog.to_print.append(guild_id)
                bot_voice.stop()
                await interaction.response.defer()
                await print_music_player(self.music_cog, guild_id, self.data)
            else:
                await interaction.response.defer()

    class LoopButton(Button):
        def __init__(self, data, guild_id):
            super().__init__(emoji = "🔁", style=discord.ButtonStyle.blurple)
            self.data = data
        async def callback(self, interaction: discord.Interaction):
            guild_name = interaction.user.guild.name
            guild_id = interaction.user.guild.id
            bot_voice = interaction.client.get_guild(guild_id).voice_client
            if bot_voice.is_playing() or bot_voice.is_paused():
                song = self.data.get_current_song(guild_id)
                self.data.flip_loop(guild_id)
                send_log(guild_name, 'LOOP', f"{song['title']}")
                await print_music_player(self.music_cog, guild_id, self.data)
            await interaction.response.send_message()

async def print_music_player(music_cog, guild_id, data):
    player_embed = embed.music_player(data, guild_id)
    view = MusicFunctions(music_cog, guild_id, data)
    msg_del = data.get_message(guild_id)
    message = await data.get_channel(guild_id).send(embed = player_embed, view = view)
    if msg_del is not None:
        await msg_del.delete()
    data.set_message(guild_id, message)



class Guild_Music_Properties():
    def __init__(self):
        self.data = {}
    
    def initialize(self, interaction:discord.Interaction):
        log_name = interaction.user.guild.name
        description = 'Initialized Variables for Guild'
        guild_id = interaction.user.guild.id
        if guild_id not in self.data:
            self.data[guild_id] = {
                #data field for music functions
                'queue'   : [],
                'history' : [],
                'current' : None,
                #For music player behaviour
                'loop'    : False,
                'random'  : False,
                #For message behaviour
                'channel' : None,
                #not used yet
                'message' : None
            }
            send_log(log_name, description )

    #RETRIEVE VALUES FUNCTIONS
    def get_queue(self, guild_id):
        return self.data[guild_id]['queue']
    def get_history(self, guild_id):
        return self.data[guild_id]['history']
    def get_current_song(self,guild_id):
        return self.data[guild_id]['current']
    def get_loop(self,guild_id):
        return self.data[guild_id]['loop']
    def get_random(self,guild_id):
        return self.data[guild_id]['random']
    def get_channel(self,guild_id):
        return self.data[guild_id]['channel']
    def get_message(self,guild_id):
        return self.data[guild_id]['message']
    def get_guild_ids(self):
        return self.data.keys()
    
    #SET VALUE FUNCTIONS
    def set_current_song(self,guild_id, song = None):
        self.data[guild_id]['current'] = song
    def set_loop(self,guild_id, value:bool):
        self.data[guild_id]['loop'] = value
    def set_random(self, guild_id, value:bool):
        self.data[guild_id]['random'] = value
    def set_channel(self, guild_id, channel):
        self.data[guild_id]['channel'] = channel
    def set_message(self,guild_id, message):
        self.data[guild_id]['message'] = message

    #SPECIFIC FUNCTIONS
    def queue_song(self, guild_id, song):
        self.data[guild_id]['queue'].append(song)
    def prepend_to_queue(self, guild_id, song):
        self.data[guild_id]['queue'].insert(0,song)
    def queue_to_current(self, guild_id):
        if self.data[guild_id]['queue'] != []:
            self.data[guild_id]['current'] = self.data[guild_id]['queue'].pop(0)
            return self.data[guild_id]['current']
        return None

    def current_to_queue(self, guild_id):
        if self.data[guild_id]['current'] is not None:
            self.data[guild_id]['queue'].insert(0,self.data[guild_id]['current'])
    def current_to_history(self, guild_id):
        if self.data[guild_id]['current'] is not None:
            self.data[guild_id]['history'].insert(0,self.data[guild_id]['current'])
            if len(self.data[guild_id]['history']) > 30:
                self.data[guild_id]['history'] = self.data[guild_id]['history'][0:30]
    def history_to_queue(self,guild_id):
        if self.data[guild_id]['history'] == []:
            return
        if len(self.data[guild_id]['history']) > 1:
            recent = self.data[guild_id]['history'].pop(0)
            self.prepend_to_queue(guild_id, recent)
            recent = self.data[guild_id]['history'].pop(0)
            self.prepend_to_queue(guild_id, recent)
        elif len(self.data[guild_id]['history']) == 1:
            recent = self.data[guild_id]['history'].pop(0)
            self.prepend_to_queue(guild_id, recent)


    
    def flip_loop(self,guild_id):  
        if self.data[guild_id]['loop'] is False:
            self.data[guild_id]['loop'] = True
        else:
            self.data[guild_id]['loop'] = False
    def flip_random(self,guild_id):
        if self.data[guild_id]['random'] is False:
            self.data[guild_id]['random'] = True
            return True
        else:
            self.data[guild_id]['random'] = False
            return False
    def empty_history(self, guild_id):
        if self.data[guild_id]['history']:
            return False
        else: return True
    def empty_queue(self, guild_id):
        if self.data[guild_id]['queue']:
            return False
        else: return True

    def reset_features(self, guild_id):
        self.data[guild_id]['loop']   = False
        self.data[guild_id]['random'] = False
    def soft_reset(self, guild_id):
        self.data[guild_id]['current']= None
        self.data[guild_id]['queue']  = []
        self.data[guild_id]['loop']   = False
        self.data[guild_id]['random'] = False

    def hard_reset(self, guild_id):
        self.data[guild_id]['queue']  = []
        self.data[guild_id]['history']  = []
        self.data[guild_id]['loop']   = False
        self.data[guild_id]['random'] = False
        self.data[guild_id]['channel'] = None
        self.data[guild_id]['message'] = None
