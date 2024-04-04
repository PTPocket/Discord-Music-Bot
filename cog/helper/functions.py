import discord, os, random, yt_dlp, spotipy
from ytmusicapi            import YTMusic
from tinytag               import TinyTag
from datetime              import datetime
from spotipy.oauth2        import SpotifyClientCredentials
from cog.helper            import embed
from cog.helper.guild_data import Guild_Music_Properties

BLANK = '\u200b'
LOCAL_MUSIC_PATH = "C:\\Users\\p\\Documents\\SERVER\\music\\Formatted"
def log(guild_name, action:str, description = '', error = ''):
    try:
        time= str(datetime.now())
        action = str(action).upper()
        description = str(description).lower()
        if description == '' and error == '':
            print(f"{time} | GUILD: {guild_name} | {action}")
        if description != '':
            print(f"{time} | GUILD: {guild_name} | {action} -> {description}")
        if error != '':
            print('Error Prompt: ', error)
    except Exception as e:
        print(e)


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

def check_features(data:Guild_Music_Properties, guild_id):
    if data.get_back(guild_id) is True:
        data.history_to_queue(guild_id)
        data.history_to_queue(guild_id)
        data.flip_back(guild_id)
        return
    if data.get_loop(guild_id) is True:
        data.history_to_queue(guild_id)
        return

    if data.get_shuffle(guild_id) is True:
        queue = data.get_queue(guild_id)
        history = data.get_history(guild_id)
        num_songs = len(queue)+len(history)
        rand_int = random.randint(0, num_songs-1)
        last_shuffle_int = data.get_last_shuffle(guild_id)
        while rand_int == last_shuffle_int and num_songs > 1:
            rand_int = random.randint(0, num_songs-1)
        data.set_last_shuffle(guild_id, rand_int)
        if rand_int < len(history):
            new_history = history[len(history)-rand_int::]
            to_queue = history[0:len(history)-rand_int]
            to_queue.reverse()
            new_queue = to_queue + queue
            data.set_queue(guild_id, new_queue)
            data.set_history(guild_id, new_history)
        else:
            rand_int = rand_int-len(history)
            new_queue = queue[rand_int::]
            to_history = queue[0:rand_int]
            to_history.reverse()
            new_history = to_history+history
            data.set_queue(guild_id, new_queue)
            data.set_history(guild_id, new_history)
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


def queuePlaylist(guildName, guildID, playlist, playlistType:str, data:Guild_Music_Properties):
        playlistType = playlistType.lower()
        song_names_list = []
        name_list = ''
        last_ind = None
        for ind, song in enumerate(playlist):
            data.queue_song(guildID,song)
            title = song['title']
            author = song['author']
            last_ind = ind+1
            row = embed.title(f"{last_ind}. {title} by {author}")
            if len(name_list) + len(row) < 1000:
                name_list += row+'\n'
            else:
                song_names_list.append(name_list)
                name_list = row+'\n'
        song_names_list.append(name_list)
        log(guildName, "QUEUED", f"{len(playlist)} songs ({playlistType})")
        return song_names_list


def SearchYoutube(query):
    try:
        ydl_opts = {
            'quiet': True,
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        # Create yt-dlp instance
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Search for videos matching the query
            result = ydl.extract_info(f"ytsearch1:{query}", download=False)['entries'][0]
            return {'source': result['url'], 'title': result['title'], 'author':result['uploader']}
    except Exception as e:
        print(e)
        return None

def GetYTSong(link):

    link = link.replace(' ','').replace('\n','')
    link = link.split('&list=')[0]
    song = {'title': link, 'author':None}
    return song

def GetYTPlaylist(link):
    try:
        link = link.replace(' ','').replace('\n','')
        playlistID = link.split('list=')[1]
        link = 'https://www.youtube.com/playlist?list='+playlistID
        # Create a yt_dlp object
        ydl_opts = {
            'quiet': True,
            'extract_flat': True,
            'force_generic_extractor': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(link,download=False)
            playlist = []
            for item in result['entries']:
                if item['title']=='[Private video]' and item['title'] == '[Deleted video]':
                    continue
                title = item['title']
                author = item['uploader']
                playlist.append({'title':title, 'author':author})
            return playlist
    except Exception as e:
        print(e)
        return None

def GetYTMSong(link:str):
    try:
        link = link.replace(' ','').replace('\n','')
        ytmusic = YTMusic()
        splitURL = link.split('/watch?v=')[1]
        songID = splitURL.split('&')[0]
        song = ytmusic.get_song(songID)
        title = song['videoDetails']['title']
        author = song['videoDetails']['author']
        return {'title':title, 'author':author}
    except Exception as e:
        print(e)
        return None

def GetYTMPlaylist(link:str):
    try:
        link = link.replace(' ','').replace('\n','')
        ytmusic = YTMusic()
        # Extract playlistId from the URL
        playlist_id = link.split('list=')[1]
        # Get playlist details
        playlist = ytmusic.get_playlist(playlist_id)
        # Extract playlist items
        playlist = playlist['tracks']
        formatted_playlist = []
        for song in playlist:
            title = song['title']
            author = ''
            for artist in song['artists']:
                author += artist['name'] +', '
            author = author[:-2]
            formatted_playlist.append({'title':title, 'author':author})
        return formatted_playlist
    except Exception as e:
        print(e)
        return None

def GetSpotify(link, client_id, client_secret):
    try:
        client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
        spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
        link = link.replace(' ','').replace('\n','')
        if 'open.spotify.com/playlist' in link:
                # Initialize Spotipy with your credentials
                # Get playlist tracks
                results = spotify.playlist_tracks(link)
                # Extract track names
                playlist = []
                for item in results['items']:
                    track = item['track']
                    title = track['name']
                    author = ''
                    for artist in track['artists']:
                        author+=artist['name']+', '
                    author = author[:-2]
                    playlist.append({'title':title, 'author':author})
                return playlist
        elif 'open.spotify.com/track' in link:
                # Retrieve track information
                track_info = spotify.track(link)
                # Extract title and artist from track information
                title = track_info['name']
                author = ''
                for artist in track_info['artists']:
                    author += artist['name'] +', '
                author = author[:-2]
                return {'title': title, 'author':author}
        else:
            return None
    except Exception as e:
        print(e)
        return None
    