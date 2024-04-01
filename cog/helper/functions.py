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
def log(guild_name, description, result = ''):
    time= str(datetime.now())
    print(f"{time} | Guild : {guild_name} | {description} -> {result}")


async def valid_play_command(interaction:discord.Interaction):
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
        log(guild_name, 'ACCESS DENIED', user)
        msg = embed.unauthorized_prompt(interaction.client)
        await interaction.response.send_message(embed= msg, ephemeral=True)
    else:
        log(guild_name, 'ACCESS GRANTED', user)
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
        log(guild_name, 'ACCESS DENIED', user)
        msg = embed.unauthorized_prompt(interaction.client)
        await interaction.response.send_message(embed= msg, ephemeral=True)
    else: log(guild_name, 'ACCESS GRANTED', user) 
    return authorized

async def voice_connect(interaction:discord.Interaction):
    user = interaction.user
    guild_name = interaction.user.guild.name
    guild_id = interaction.user.guild.id
    voice_client = interaction.client.get_guild(guild_id).voice_client

    if voice_client is None:
        voice_client = await user.voice.channel.connect(reconnect=True)
        log(guild_name, 'Voice Connected', voice_client.channel.name)
    else:
        if voice_client.is_connected() is False:
            await voice_client.move_to(user.voice.channel)
            voice_client = interaction.client.get_guild(guild_id).voice_client
            voice_client = interaction.client.get_guild(guild_id).voice_client
            log(guild_name, 'Voice Reconnected', voice_client.channel.name)

    return voice_client


def YoutubeGet(query):
    if '/watch' in query:
        if '&list=' in query:
            split_url = query.split('&list=')
            query = split_url[0]
        # Configure yt-dlp options
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        # Create yt-dlp instance
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                # Search for videos matching the query
                search_results = ydl.extract_info(f"ytsearch1:{query}", download=False)['entries'][0]
                success = True
            except Exception as e:
                print("YT_DLP Error:", e)
                success = False
        if success is True:
            return {'source': search_results['url'], 'title': search_results['title']}
        else:
            return None
    elif '/playlist' in query:
        # Create a yt_dlp object
        ydl_opts = {
            'quiet': True,
            'extract_flat': True,
            'force_generic_extractor': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                result = ydl.extract_info(query,download=False)
                video_titles = [video['title'] for video in result['entries'] if video['title']!='[Private video]' and video['title'] != '[Deleted video]']
                success = True
            except Exception as e:
                print('YoutubeGet: error -> ', e)
                success = False
        if success is True:
            return video_titles
        else:
            return None
    else:
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        # Create yt-dlp instance
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                # Search for videos matching the query
                search_results = ydl.extract_info(f"ytsearch1:{query}", download=False)['entries'][0]
                success = True
            except Exception as e:
                print("YT_DLP Error:", e)
                success = False
        if success is True:
            return {'source': search_results['url'], 'title': search_results['title']}
        else:
            return None

def YTMusicGet(url):
    if 'watch' in url and 'list=' in url:
        url = url.split('music.')
        url = url[0]+url[1]
        url = url.split('&list=')[0]
        return YoutubeGet(url)
    elif 'watch' in url:
        split_url = url.split('music.')
        url = split_url[0]+split_url[1]
        # Configure yt-dlp options
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        # Create yt-dlp instance
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                # Search for videos matching the query
                search_results = ydl.extract_info(url, download=False)#['entries'][0]
                success = True
            except Exception as e:
                print("YT_DLP Error:", e)
                success = False
        if success is True:
            return {'source': search_results['url'], 'title': search_results['title']}
        else:
            return None
    elif 'playlist' in url:
        try:
            ytmusic = YTMusic()
            # Extract playlistId from the URL
            playlist_id = url.split('list=')[1]
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
            print('YTMusic: error -> ', e)
            return None


def spotify_get(url, client_id, client_secret):
    client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
    spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
    if 'open.spotify.com/playlist' in url:
        try:
            # Initialize Spotipy with your credentials
            # Get playlist tracks
            results = spotify.playlist_tracks(url)
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
    elif 'open.spotify.com/track' in url:
        try:
            # Extract track ID from the Spotify link
            track_id = url.split('/')[-1]

            # Retrieve track information
            track_info = spotify.track(url)

            # Extract title and artist from track information
            song_name = track_info['name']
            all_artists = ''
            for artist in track_info['artists']:
                all_artists += artist['name'] +','
            title = song_name + ' by ' +all_artists[:-1]
            return {'source':'spotify', 'title': title}
        except Exception as e:
            print(e)
            return None
    else:
        print('Invalid Spotify Link')
        return None


def yt_playlist(link):
    try:
        # Create a yt_dlp object
        ydl_opts = {
            'quiet': True,
            'extract_flat': True,
            'force_generic_extractor': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(
                link,
                download=False
            )
        video_titles = [video['title'] for video in result['entries'] if video['title']!='[Private video]' and video['title'] != '[Deleted video]']
        return video_titles
    except Exception as e:
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
        song = {'title': title, 'source': f'{LOCAL_MUSIC_PATH}\\{song}'}
        data.queue_song(guild_id, song)
        return

def add_random_song(data, guild_id):
    flac_song_list = os.listdir(LOCAL_MUSIC_PATH)
    song = random.choice(flac_song_list)
    path = LOCAL_MUSIC_PATH + '\\'+ song
    song_metadata = TinyTag.get(path)
    title = f"{song_metadata.title} - {song_metadata.artist}"
    song = {'title': title, 'source': f'{LOCAL_MUSIC_PATH}\\{song}'}
    data.prepend_to_queue(guild_id, song)

def get_random_song(data,guild_id):
    pass


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

