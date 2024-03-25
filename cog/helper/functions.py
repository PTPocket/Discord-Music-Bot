import discord, os, random, time, yt_dlp, spotipy
from ytmusicapi import YTMusic
from tinytag import TinyTag
from discord.ui import View, Select, Button
from datetime import datetime
from spotipy.oauth2 import SpotifyClientCredentials
from cog.helper import embed
from cog.helper.guild_data import Guild_Music_Properties

BLANK = '\u200b'
LOCAL_MUSIC_PATH = "C:\\Users\\p\\Documents\\SERVER\\music\\Formatted"

def send_log(log_name, description, result = ''):
    time= str(datetime.now())
    print(f"{time} | Guild : {log_name} | {description} -> {result}")


async def valid_play_command(interaction:discord.Interaction):
    #for log print
    user = interaction.user
    guild_name = interaction.user.guild.name
    guild_id = interaction.user.guild.id

    voice_client = interaction.client.get_guild(guild_id).voice_client
    authorized = None
    if user.voice is None:
        authorized = False
    elif voice_client is None or not voice_client.is_connected():
        authorized = True
    elif user.voice.channel.id == voice_client.channel.id:
        authorized = True
    else:
        authorized = False

    if not authorized:
        send_log(guild_name, 'ACCESS DENIED', user)
        msg = embed.unauthorized(interaction.client)
        await interaction.response.send_message(embed= msg, ephemeral=True)
    else:
        send_log(guild_name, 'ACCESS GRANTED', user)
    return authorized

async def valid_user_REGULAR_FUNC(interaction:discord.Interaction):
    user = interaction.user
    guild_name = interaction.user.guild.name
    guild_id = interaction.user.guild.id
    authorized = None
    voice_client = interaction.client.get_guild(guild_id).voice_client

    if user.voice is None or \
    voice_client is None or \
    not voice_client.is_connected():
        authorized = False
    elif voice_client.channel.id == user.voice.channel.id:
        authorized =  True
    else: 
        authorized =  False

    if authorized is False:
        send_log(guild_name, 'ACCESS DENIED', user)
        msg = embed.unauthorized(interaction.client)
        await interaction.response.send_message(embed= msg, ephemeral=True)
    else: send_log(guild_name, 'ACCESS GRANTED', user) 
    return authorized

async def voice_connect(interaction:discord.Interaction):
    user = interaction.user
    guild_name = interaction.user.guild.name
    guild_id = interaction.user.guild.id
    voice_client = interaction.client.get_guild(guild_id).voice_client

    if voice_client is None:
        voice_client = await user.voice.channel.connect(reconnect=True)
        send_log(guild_name, 'Voice Connected', voice_client.channel.name)
    else:
        if voice_client.is_connected() is False:
            await voice_client.move_to(user.voice.channel)
            voice_client = interaction.client.get_guild(guild_id).voice_client
            voice_client = interaction.client.get_guild(guild_id).voice_client
            send_log(guild_name, 'Voice Reconnected', voice_client.channel.name)

    return voice_client

def youtube_search(query):
    ydl_opts = {'format': 'bestaudio', 'noplaylist':True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try: 
            info = ydl.extract_info("ytsearch:%s" % query, download=False)['entries'][0]
        except Exception as e: 
            print(e)
            return None
    return {'source': info['url'], 'title': info['title']}

def youtube_playlist(playlist_url):
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'force_generic_extractor': True,
        'force_playlist': True,
        'skip_download': True,
        'geo_bypass': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            playlist_info = ydl.extract_info(playlist_url, download=False)
            videos = playlist_info['entries']
            if videos:
                return videos
            else:
                print("No videos found in the playlist.")
                return None
        except Exception as e: 
            print(e)
            return None

def spotify_playlist(playlist_url, client_id, client_secret):
    try:
        # Initialize Spotipy with your credentials
        client_id = '9c3663afbe8f41589283a0055983da47'
        client_secret = '4d580e8f409b40e9b72e50b548d1dd28'
        client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
        sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
        # Get playlist tracks
        results = sp.playlist_tracks(playlist_url)
        # Extract track names
        song_titles = []
        for item in results['items']:
            track = item['track']
            artists = ''
            for i in range(len(track['artists'])):
                artists += track['artists'][i]['name'] + ','
            song_titles.append(f"{track['name']} by {artists[:-1]}")
        return song_titles
    except Exception as e:
        print(e)
        return None

def ytmusic_playlist(playlist_url):
    try:
        ytmusic = YTMusic()
        # Extract playlistId from the URL
        playlist_id = playlist_url.split('list=')[1]
        # Get playlist details
        playlist = ytmusic.get_playlist(playlist_id)
        # Extract playlist items
        playlist = playlist['tracks']
        formatted_playlist = []
        complete_title = None
        for song in playlist:
            complete_title = song['title'] + ' by '
            for artist in song['artists']:
                complete_title += artist['name']
            formatted_playlist.append(complete_title)
            complete_title=None
        return formatted_playlist
    except Exception as e:
        print(e)
        return None

def check_features(data:Guild_Music_Properties, guild_id):
    if data.get_back(guild_id) is True:
        data.history_to_queue(guild_id)
        data.history_to_queue(guild_id)
        data.flip_back(guild_id)
        return
    if data.get_loop(guild_id) is True:
        data.history_to_queue(guild_id)
        return
    if data.empty_queue(guild_id) is True and data.get_random(guild_id) is True:
        flac_song_list = os.listdir(LOCAL_MUSIC_PATH)
        song = random.choice(flac_song_list)
        path = LOCAL_MUSIC_PATH + '\\'+ song
        song_metadata = TinyTag.get(path)
        title = f"{song_metadata.title} - {song_metadata.artist}"
        song = {'title': title, 'source': f'{LOCAL_MUSIC_PATH}\{song}'}
        data.queue_song(guild_id, song)
        return

def add_random_song(data, guild_id):
        flac_song_list = os.listdir(LOCAL_MUSIC_PATH)
        song = random.choice(flac_song_list)
        path = LOCAL_MUSIC_PATH + '\\'+ song
        song_metadata = TinyTag.get(path)
        title = f"{song_metadata.title} - {song_metadata.artist}"
        song = {'title': title, 'source': f'{LOCAL_MUSIC_PATH}\{song}'}
        data.prepend_to_queue(guild_id, song)


# class SearchView(View):
#     def __init__(self, song_list):
#         super().__init__(timeout=30)
#         self.add_item(self.SongSelectMenu(song_list))
#         self.song_choice = None
#     class SongSelectMenu(Select):
#         def __init__(self, song_list):
#             options = []
#             for i, song in enumerate(song_list):
#                 path = LOCAL_MUSIC_PATH + '\\'+ song
#                 file = TinyTag.get(path)
#                 options.append(discord.SelectOption(
#                     label = f"{file.title} - {file.artist}",
#                     value = i,
#                 ))
#             super().__init__(placeholder='Search Results', options = options)
#             self.song_list = song_list
#         async def callback(self, interaction:discord.Interaction, select_item:discord.ui.Select):
#             print('awer')
#             print(select_item.values)
#             print('test')
#             await interaction.response.send_message()


class MusicFunctions(View):
    def __init__(self,music_cog,data,guild_id):
        super().__init__(timeout=None)
        #self.add_item(self.SongSelectMenu(music_cog,data,guild_id))
        self.add_item(self.PreviousButton  (music_cog, data, guild_id))
        self.add_item(self.PlayPause       (music_cog, data, guild_id))
        self.add_item(self.NextButton      (music_cog, data, guild_id))
        #self.add_item(self.LoopButton      (music_cog, data, guild_id))
        self.add_item(self.RandomButton    (music_cog, data, guild_id))
        self.add_item(self.RandomSongButton(music_cog, data, guild_id))
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
            send_log(guild_name, 'ACCESS GRANTED', user) 
            return True
        else:
            send_log(guild_name, 'ACCESS DENIED', user)
            await interaction.response.defer()
            return False

    class SongSelectMenu(Select):
        def __init__(self, music_cog, data, guild_id):
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
            send_log(guild_name, 'MENU OPTION', 'Clicked')
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
        def __init__(self,music_cog, data,guild_id):
            super().__init__(emoji = '⏯', style= discord.ButtonStyle.blurple)
            self.data = data
            self.music_cog = music_cog

        async def callback(self, interaction: discord.Interaction):
            guild_name = interaction.user.guild.name
            guild_id = interaction.user.guild.id
            voice_client = interaction.client.get_guild(guild_id).voice_client
            song = self.data.get_current_song(guild_id)
            if voice_client is None:
                self.style = discord.ButtonStyle.grey
                await interaction.response.edit_message(view=self.view)
                return
            if voice_client.is_playing() and not voice_client.is_paused():
                send_log(guild_name, 'PAUSED',song['title'])
                voice_client.pause()
                self.style = discord.ButtonStyle.grey
                await interaction.response.edit_message(view=self.view)
                return
            if not voice_client.is_playing() and voice_client.is_paused():
                send_log(guild_name, 'RESUMED',song['title'])
                self.style = discord.ButtonStyle.blurple
                await interaction.response.edit_message(view=self.view)
                voice_client.resume()
                return
            await interaction.response.defer()
            
    class RandomButton(Button):
        def __init__(self, music_cog, data, guild_id):
            if data.get_random(guild_id) == True:
                style= discord.ButtonStyle.blurple
            else:
                style= discord.ButtonStyle.grey
            super().__init__(emoji='♾', style= style)
            self.data = data
            self.music_cog = music_cog
        async def callback(self, interaction: discord.Interaction):
            guild_name = interaction.user.guild.name
            guild_id = interaction.user.guild.id
            if self.data.flip_random(guild_id) is True:
                send_log(guild_name, 'RANDOM SONG', 'On')
                self.data.set_loop(guild_id, False)
                await self.music_cog.music_player_start(interaction) 
            else: 
                send_log(guild_name, 'RANDOM SONG', 'Off')
                await self.music_cog.GUI_HANDLER(guild_id)
            await interaction.response.defer()
    
    class PreviousButton(Button):
        def __init__(self,music_cog, data, guild_id):
            super().__init__(emoji = "⏮", style= discord.ButtonStyle.blurple)
            self.data = data
            self.music_cog = music_cog
        
        async def callback(self, interaction: discord.Interaction):
            guild_name = interaction.user.guild.name
            send_log(guild_name, 'PREVIOUS BUTTON', 'Clicked')
            guild_id = interaction.user.guild.id
            voice_client = interaction.client.get_guild(guild_id).voice_client
            #IF VOICE RUNNING
            if voice_client is None:
                print('No voice_client')
                self.data.set_loop(guild_id, False)
                self.data.history_to_queue(guild_id)
                await interaction.response.defer()
                await self.music_cog.music_player_start(interaction) 
            elif voice_client.is_playing() or voice_client.is_paused():
                print('PLAYING OR PAUSED')
                self.data.flip_back(guild_id)
                self.data.set_loop(guild_id, False)
                voice_client.stop()
                await interaction.response.defer()
                await self.music_cog.music_player_start(interaction)
            else:
                print('Nothing Playing')
                self.data.set_loop(guild_id, False)
                self.data.flip_back(guild_id)
                self.data.history_to_queue(guild_id)
                voice_client.stop()
                await interaction.response.defer()
                await self.music_cog.music_player_start(interaction) 
     
    class NextButton(Button):
        def __init__(self,music_cog, data, guild_id):
            super().__init__(emoji = "⏭", style= discord.ButtonStyle.blurple)
            self.data = data
            self.music_cog = music_cog
        async def callback(self, interaction: discord.Interaction):
            guild_name = interaction.user.guild.name
            send_log(guild_name, 'NEXT BUTTON', 'Clicked')
            guild_id = interaction.user.guild.id
            voice_client = interaction.client.get_guild(guild_id).voice_client
            if voice_client is None:
                await interaction.response.defer()
                return
            if (voice_client.is_playing() or voice_client.is_paused()):
                self.data.set_loop(guild_id, False)
                voice_client.stop()
                await interaction.response.defer()
                await self.music_cog.GUI_HANDLER(guild_id)
                return
            await interaction.response.defer()

    class LoopButton(Button):
        def __init__(self,music_cog, data, guild_id):
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
            
            if voice_client is None:
                await interaction.response.defer()
                return
            if voice_client.is_playing() or voice_client.is_paused():
                song = self.data.get_current_song(guild_id)
                self.data.flip_loop(guild_id)
                self.data.set_random(guild_id, False)
                send_log(guild_name, 'LOOP', f"{song['title']}")
                await self.music_cog.GUI_HANDLER(guild_id)
                await interaction.response.defer()
                return
            await interaction.response.defer()
    
    class RandomSongButton(Button):
        def __init__(self,music_cog, data,guild_id):
            super().__init__(label = 'Random Song', style= discord.ButtonStyle.blurple)
            self.data = data
            self.music_cog = music_cog

        async def callback(self, interaction: discord.Interaction):
            guild_name = interaction.user.guild.name
            send_log(guild_name, 'MYSTERY BUTTON', 'Clicked')
            guild_id = interaction.user.guild.id
            voice_client = interaction.client.get_guild(guild_id).voice_client
            add_random_song(self.data, guild_id)
            if voice_client is not None and (voice_client.is_playing() or voice_client.is_paused()):
                voice_client.stop()
            self.data.set_loop(guild_id, False)
            await interaction.response.defer()
            await self.music_cog.music_player_start(interaction) 

    class DisconnectButton(Button):
        def __init__(self,music_cog, data, guild_id):
            super().__init__(label = 'Disconnect', style=discord.ButtonStyle.grey)
            self.music_cog = music_cog
            self.data = data
        async def callback(self, interaction: discord.Interaction):
            guild_name = interaction.user.guild.name
            send_log(guild_name, 'DISCONNECT BUTTON', 'Clicked')
            guild_id = interaction.user.guild.id
            voice_client = interaction.client.get_guild(guild_id).voice_client
            self.data.reset(guild_id)
            if voice_client is not None:
                if voice_client.is_playing() or voice_client.is_paused():
                    voice_client.stop()
                await voice_client.disconnect()
                send_log(guild_name, 'VOICE DISCONNECTED (force)')
            await interaction.response.defer()
            await self.music_cog.GUI_HANDLER(guild_id)
