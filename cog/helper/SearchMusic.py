import os
import base64
import requests
import asyncio
import yt_dlp
import random
import cog.helper.Setting as Setting
from discord.ext        import commands
from tinytag          import TinyTag
from time             import perf_counter
from cog.helper.Log   import *
from GlobVar          import LOCAL_MUSIC_PATH
from cog.helper.Embed import Embeds
from cog.helper.GuildData import GuildData


def funcTime(func):
    def wrapper(*args, **kwargs):
        start = perf_counter()
        result = func(*args, **kwargs)
        end = perf_counter()
        log(None, f'Finished {func.__name__}', f'{round(end-start,10)} sec')
        return result
    return wrapper

class MusicOrb():
    def __init__(self,bot:commands.Bot, dataObj:GuildData, embObj:Embeds ):
        #For Spotify API Call
        self.client_id    = os.getenv('SPOTIFY_CLIENT_ID')
        self.client_secret= os.getenv('SPOTIFY_CLIENT_SECRET')
        client_credentials = f"{self.client_id}:{self.client_secret}"
        base64_client_credentials = base64.b64encode(client_credentials.encode()).decode()
        self.token_url = 'https://accounts.spotify.com/api/token'
        self.token_headers = {
            'Authorization': f'Basic {base64_client_credentials}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        self.dataObj = dataObj
        self.embObj = embObj
        self.bot = bot
        self.access_token = None
        self.refresh_token = None
        self.headers = None
        self.baseUrl = 'https://api.spotify.com/v1'
        self.spotifyLock = asyncio.Lock()
        self.youtubeLock = asyncio.Lock()
        self.get_spotifyAccessToken()

#### LEVEL 1 #####################################

    async def Search(self, channel, query):
        if 'youtube.com/' in query or 'youtu.be/' in query:
            result = await self.GetYT(channel, query)
            return result
        if 'open.spotify.com' in query:
            result = await self.GetSpotify(channel, query)
            return result
        if 'https://' in query:
            await self.invalid_url_Print(channel, query)
            return False
        searchAlgorithm = Setting.get_searchAlgorithm(channel.guild.id)
        if searchAlgorithm == 'spotify':
            result = await self.GetSpotify(channel, query)
        else:
            result = await self.GetYT(channel, query)
        return result

#### LEVEL 2 #####################################

    async def GetYT(self, channel, query):
        log(channel.guild.name, 'youtube','searching')
        if 'watch?v=' in query or 'youtu.be/' in query:
            result = self.GetYTSong(query)
        elif 'list=' in query:
            result = self.GetYTPlaylist(query)
        else:
            result = self.SearchYoutube(query)

        if type(result) is dict:
            await self.queueSongnPrint(channel, result)
            return result
        elif type(result) is list:
            await self.queuePlaylistnPrint(channel, result, query, 'youtube')
            return result
        else:
            await self.invalid_url_Print(channel, query, 'youtube')
            return False
        
    async def GetSpotify(self, channel, query):
        async with self.spotifyLock:
            log(channel.guild.name, 'spotify','searching')
            if 'spotify.com/playlist' in query:
                result = self.GetSpotifyPlaylist(query)
            elif 'spotify.com/album' in query:
                result = self.GetSpotifyAlbum(query)
            elif 'spotify.com/artist' in query:
                result = self.GetSpotifyArtist10(query)
            elif 'spotify.com/track' in query:
                result = self.GetSpotifyTrack(query)
            else:
                result = self.SearchSpotify(query)

            if type(result) is dict:
                await self.queueSongnPrint(channel, result)
                return result
            elif type(result) is list:
                await self.queuePlaylistnPrint(channel, result, query, 'spotify')
                return result
            elif result == 429:
                await self.try_again_Print(channel)
                return False
            else:
                await self.invalid_url_Print(channel, query, 'spotify')
                return False


#### LEVEL 3 #####################################
    @funcTime
    def SearchYoutube(self, query):
        ydl_opts = {
            'quiet': True,
            'format': 'bestaudio/best'
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Search for videos matching the query
                result = ydl.extract_info(f"ytsearch1:{query}", download=False)
        except Exception as e:
            error_log('SearchYoutube', e, query)
            return None
        try:
            song = result['entries'][0]
        except Exception as e:
            error_log('SearchYoutube', e, query)
            try:
                song = result['entries']
            except Exception as e:
                error_log('SearchYoutube', e, query)
                return None
        
        url = f'https://youtube.com/watch?v={song['id']}'
        return {
            'title'    : song['title'], 
            'author'   : song['uploader'],
            'url'      : url,
            'query'    : song['url'],
            'source'   : 'searched',
            'thumbnail': song['thumbnail'],
            'duration' : song['duration']}

    @funcTime
    def GetYTSong(self, link):
        ydl_opts = {
            'quiet': True,
            'format': 'bestaudio/best'
        }
        link = link.replace(' ','').replace('\n','')
        if 'youtu.be/' in link:
            videoID = link.split('&index=')[0]
            videoID = videoID.split('&list=')[0]
            videoID = videoID.split('&si')[0]
            videoID = videoID.split('?si')[0]
            videoID = videoID.split('youtu.be/')[1]
        else:
            videoID = link.split('&si=')[0]
            videoID = videoID.split('&index=')[0]
            videoID = videoID.split('&list=')[0]
            videoID = videoID.split('&si')[0]
            videoID = videoID.split('?si')[0]
            videoID = videoID.split('watch?v=')[1]
        videoUrl = f'https://www.youtube.com/watch?v={videoID}'
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Search for videos matching the query
                result = ydl.extract_info(videoUrl, download=False)
            artists = result.get('artists')
            if artists is None:
                artists = result.get('uploader')
            else: artists = self.get_author(artists)
            return {
                'title'    : result['title'], 
                'author'   : artists,
                'url'      : videoUrl,
                'query'    : result['url'],
                'source'   : 'searched',
                'thumbnail': result['thumbnail'],
                'duration' : int(result['duration'])}
        except Exception as e:
            error_log('GetYTSong', e, link)
            return None
            
    def GetYTPlaylist(self, link):
        ydl_opts = {
            'quiet': True,
            'extract_flat': True,
            'skip_download': True
        }
        link = link.replace(' ','').replace('\n','')
        playlistID = link.split('list=')[1]
        playlistID = playlistID.split('&index=')[0]    
        playlistID = playlistID.split('&si=')[0]  
        playlistUrl = f'https://www.youtube.com/playlist?list={playlistID}'
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                result = ydl.extract_info(playlistUrl,download=False)
                playlist = []
                for song in result['entries']:
                    if song['title']=='[Private video]' and song['title'] == '[Deleted video]':
                        continue
                    playlist.append({
                        'title'     : song['title'], 
                        'author'    : song['uploader'], 
                        'query'     : song['url'],
                        'source'    :'query',
                        'url'       : song['url'],
                        'thumbnail' : self.get_thumbnailYT(song['thumbnails']),
                        'duration'  : int(song['duration'])})
                return playlist
        except Exception as e:
            error_log('GetYTPlaylist', e, link)
            return None

    def get_spotifyAccessToken(self):
        data = {'grant_type': 'client_credentials'}
        response = requests.post(
            self.token_url, 
            data=data, 
            headers=self.token_headers
        )
        if response.status_code == 200:
            response_data = response.json()
            self.access_token = response_data.get('access_token')
            self.refresh_token = response_data.get('refresh_token')
            self.headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/x-www-form-urlencoded'}
            log(None,'spotify access token', 'retrieved')
        else:
            # Print detailed error information
            print(f"Failed to refresh token: {response.status_code}")
            print(response.json())

    def refresh_spotifyAcessToken(self):
        data = {
            'grant_type': 'client_credentials',
            'refresh_token': self.refresh_token
        }
        response = requests.post(self.token_url, headers=self.token_headers, data=data)

        # Check if the request was successful
        if response.status_code == 200:
            response_data = response.json()
            self.access_token = response_data.get('access_token')
            self.refresh_token = response_data.get('refresh_token')
            self.headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/x-www-form-urlencoded'}
            log(None,'spotify access token', 'reset')
        else:
            # Print detailed error information
            print(f"Failed to refresh token: {response.status_code}")
            print(response.json())

    def get_spotifyRequest(self, url, params = None):
        result = requests.get(url, headers=self.headers, params=params)
        if result.status_code == 401:
            self.refresh_spotifyAcessToken()
            result = requests.get(url, headers=self.headers, params=params)
        return result
    
    def SearchSpotify(self, query):
        url = f'{self.baseUrl}/search'
        params = {
            'q'    : query,
            'type' : 'track',
            'limit': 10
        }
        result = self.get_spotifyRequest(url, params = params)
        if result.status_code != 200:
            return result.status_code
        result = result.json()
        track = result['tracks']['items'][0]
        title = track['name']
        url = track['external_urls']['spotify']
        thumbnail = self.get_thumbnail(track['album']['images'])
        duration = int(track['duration_ms'])/1000
        author = ''
        for artist in track['artists']:
            author += artist['name'] +', '
        author = author[:-2]
        return {
            'title' : title, 
            'author': author,
            'query' : f'{title} by {author}',
            'source': 'query',
            'url':url,
            'thumbnail':thumbnail,
            'duration' :duration}
    
    def GetSpotifyTrack(self, link):
        splitLink = link.split('track/')[1]
        id = splitLink.split('?si')[0]
        url = f'{self.baseUrl}/tracks/{id}'
        result = self.get_spotifyRequest(url)
        if result.status_code != 200:
            return result.status_code
        result = result.json()
        title = result['name']
        url = result['external_urls']['spotify']
        thumbnail = self.get_thumbnail(result['album']['images'])
        duration = int(result['duration_ms'])/1000
        author = self.get_author(result['artists'])
        return {
            'title' : title, 
            'author': author,
            'query' : f'{title} by {author}',
            'source':'query',
            'url':url,
            'thumbnail':thumbnail,
            'duration' :duration}

    def GetSpotifyPlaylist(self, link):
        splitLink = link.split('playlist/')[1]
        id = splitLink.split('?si')[0]
        url = f'{self.baseUrl}/playlists/{id}'
        result = self.get_spotifyRequest(url)
        if result.status_code != 200:
            return result.status_code
        result = result.json()
        playlist = []
        for track in result['tracks']['items']:
            track_info = track['track']
            title = track_info['name']
            url = track_info['external_urls']['spotify']
            thumbnail = self.get_thumbnail(track_info['album']['images'])
            author = self.get_author(track_info['artists'])
            duration = int(track_info['duration_ms'])/1000
            playlist.append({
                'title':title, 
                'author':author,
                'query' : f'{title} by {author}',
                'source': 'query',
                'url':url,
                'thumbnail':thumbnail,
                'duration' :duration})
        return playlist
    
    def GetSpotifyAlbum(self, link):
        splitLink = link.split('album/')[1]
        id = splitLink.split('?si')[0]
        url = f'{self.baseUrl}/albums/{id}/tracks'
        result = self.get_spotifyRequest(url)
        if result.status_code != 200:
            return result.status_code
        result = result.json()
        playlist = []
        for track_info in result['items']:
            title = track_info['name']
            url = track_info['external_urls']['spotify']
            duration = int(track_info['duration_ms'])/1000
            author = self.get_author(track_info['artists'])
            playlist.append({
                'title':title, 
                'author':author,
                'query' : f'{title} by {author}',
                'source': 'spotify',
                'url':url,
                'thumbnail':None,
                'duration': duration})
        return playlist

    def GetSpotifyArtist10(self, link):
        splitLink = link.split('artist/')[1]
        id = splitLink.split('?si')[0]
        url = f'{self.baseUrl}/artists/{id}/top-tracks'
        result = self.get_spotifyRequest(url)
        if result.status_code != 200:
            return result.status_code
        result = result.json()
        playlist = []
        for track_info in result['tracks']:
            title = track_info['name']
            url = track_info['external_urls']['spotify']
            thumbnail = self.get_thumbnail(track_info['album']['images'])
            author = self.get_author(track_info['artists'])
            duration = int(track_info['duration_ms'])/1000
            playlist.append({
                'title':title, 
                'author':author,
                'query' : f'{title} by {author}',
                'source': 'query',
                'url':url,
                'thumbnail':thumbnail,
            'duration' :duration})
        return playlist

    def GetRandom(self):
        flac_song_list = os.listdir(LOCAL_MUSIC_PATH)
        song = random.choice(flac_song_list)
        path = LOCAL_MUSIC_PATH + '\\'+ song
        song_metadata = TinyTag.get(path)
        title = song_metadata.title
        author = song_metadata.artist
        duration = song_metadata.duration
        return {
            'title' : title, 
            'author': author, 
            'url'   : None,
            'query' : f'{LOCAL_MUSIC_PATH}\\{song}',
            'source': 'Local',
            'thumbnail' :f'{self.bot.user.avatar}',
            'duration'  :duration}

#### Extra Functions ###########################################################

    def get_thumbnail(self, thumbnails):
        if len(thumbnails) > 0:
            return thumbnails[0]['url']
        else: return

    def get_author(self, artists):
        author = ''
        for artist in artists:
            if type(artist) is str:
                author += artist +', '
            else:
                author += artist['name'] +', '
        author = author[:-2]
        return author
    
    def get_thumbnailYT(self, thumbnails):
        if len(thumbnails) > 0:
            return thumbnails[-1]['url']
        else: return

    async def queuePlaylistnPrint(self, channel, playlist, query, platform = None):
        guildName = channel.guild.name
        guildID = channel.guild.id
        self.dataObj.add_playlist(guildID, playlist)
        playlistType = platform.lower()
        song_names_list = []
        name_list = ''
        last_ind = None
        for ind, song in enumerate(playlist):
            title = song['title']
            author = song['author']
            last_ind = ind+1
            row = self.embObj.title(f"{last_ind}. {title} - {author}")
            if len(name_list) + len(row) < 1000:
                name_list += row+'\n'
            else:
                song_names_list.append(name_list)
                name_list = row+'\n'
        song_names_list.append(name_list)
        log(guildName, "QUEUED", f"{len(playlist)} songs ({playlistType})")
        msg = self.embObj.queued_playlist_prompt(song_names_list, len(playlist), query, playlistType)
        await channel.send(embed = msg, delete_after=Setting.get_promptDelay()*30)
        
    async def queueSongnPrint(self, channel, song):
        guildName = channel.guild.name
        guildID = channel.guild.id
        self.dataObj.add_song(guildID, song)
        log(guildName, "QUEUED", song)
        msg = self.embObj.queue_prompt(song)
        await channel.send(embed= msg, delete_after=Setting.get_promptDelay())
    
    async def invalid_url_Print(self, channel, query, platform = ''):
        guildName = channel.guild.name
        msg = self.embObj.invalid_link(query, platform)
        await channel.send(embed= msg, delete_after=Setting.get_promptDelay())
        log(guildName,f'invalid {platform} url', query)

    async def try_again_Print(self, channel):
        guildName = channel.guild.name
        msg = self.embObj.try_again_prompt()
        await channel.send(embed= msg, delete_after=Setting.get_promptDelay())
        log(guildName,'too many requests')
    
    async def no_result_Print(self, channel, query):
        await channel.send(embed = self.embObj.no_search_result_prompt(query), delete_after=Setting.get_promptDelay())
