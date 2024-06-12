import youtube_dl, yt_dlp, spotipy, time
from ytmusicapi     import YTMusic
from spotipy.oauth2 import SpotifyClientCredentials
from cog.helper.Log import *
FFMPEG_LOC = "C:\\Users\\p\\Downloads\\ffmpeg\\bin\\ffmpeg.exe"

def SearchYoutube(query):
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
        return {'title' : '', 
                'author': '', 
                'url'   : '', 
                'query' : query,
                'source': 'query',
                'thumbnail': None}
    try:
        song = result['entries'][0]
        thumbnail = get_thumbnailYT(song['thumbnails'])
        return {
            'title' : song['title'], 
            'author': song['uploader'],
            'url'   : song['url'],
            'query' : query,
            'source': 'query',
            'thumbnail': thumbnail}
    except Exception as e:
        error_log('SearchYoutube', e, query)
        song = result['entries']
        thumbnail = get_thumbnailYT(song['thumbnails'])
        try:
            return {
            'title' : song['title'], 
            'author': song['uploader'],
            'url'   : song['url'],
            'query' : query,
            'source': 'query',
            'thumbnail': thumbnail}
        except Exception as e:
            error_log('SearchYoutube', e, query)
            return {'title' : '', 
                    'author': '', 
                    'url'   : '', 
                    'query' : query,
                    'source': 'query'}

def SearchSpotify(spotify:spotipy.Spotify, query):
    try:
        result = None
        try:
            result = spotify.search(q=query, type='track', limit=1)
        except Exception as e:
            error_log('SearchSpotify', e)
            time.sleep(.1)
            log('N/A', 'trying again')
        if result is None:
            result = spotify.track(query)
        
        track = result['tracks']['items'][0]
        title = track['name']
        url = track['external_urls']['spotify']
        thumbnail = get_thumbnailSpotify(track['album']['images'])
        duration = int(track['duration_ms'])/1000
        author = ''
        for artist in track['artists']:
            author += artist['name'] +', '
        author = author[:-2]
        return {
            'title' : title, 
            'author': author,
            'query' : f'{title} by {author}',
            'source':'query',
            'url':url,
            'thumbnail':thumbnail,
            'duration' :duration}
    except Exception as e:
        error_log('Searchspotify', e)
### CONTROLLER FUNCTIONS ###
def GetYT(link):
    if 'watch?v=' in link:
        return GetYTSong(link)
    if '/playlist' in link: 
        return GetYTPlaylist(link)
    return None

def GetYTMusic(link):
    if 'watch?v=' in link:
        return GetYTMSong(link)
    if '?list=' in link:
        return GetYTMPlaylist(link)
    return

def GetSpotify(spotify, link):
    if 'open.spotify.com/playlist' in link:
        return GetSpotifyPlaylist(spotify, link)
    if 'open.spotify.com/album' in link:
        return GetSpotifyAlbum(spotify, link)
    if 'open.spotify.com/artist' in link:
        return GetSpotifyArtist10(spotify, link)
    if 'open.spotify.com/track' in link:
        return GetSpotifyTrack(spotify, link)
    return None
############################

############################
def GetYTSong(link):
    ydl_opts = {
        'quiet': True,
        'format': 'bestaudio/best'
    }
    try:
        link = link.replace(' ','').replace('\n','')
        link = link.split('&')[0]
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Search for videos matching the query
            result = ydl.extract_info(f"ytsearch1:{link}", download=False)
    except Exception as e:
        error_log('SearchYoutube', e, link)
        return None
    try:
        song = result['entries'][0]
        thumbnail = get_thumbnailYT(song['thumbnails'])
        duration = song['duration']
        return {
            'title' : song['title'], 
            'author': song['uploader'],
            'url'   : song['url'],
            'query' : link,
            'source': 'YTsong',
            'thumbnail': thumbnail,
            'duration' : duration}
    except Exception as e:
        error_log('SearchYoutube', e, link)
        song = result['entries']
        thumbnail = get_thumbnailYT(song['thumbnails'])
        duration = song['duration']
        try:
            return {
            'title' : song['title'], 
            'author': song['uploader'],
            'url'   : song['url'],
            'query' : link,
            'source': 'YTsong',
            'thumbnail': thumbnail,
            'duration' : duration}
        except Exception as e:
            error_log('SearchYoutube', e, link)
            return None
        
def GetYTPlaylist(link):
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'skip_download': True
    }
    link = link.replace(' ','').replace('\n','')
    playlistID = link.split('list=')[1]
    link = 'https://www.youtube.com/playlist?list='+playlistID
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(link,download=False)
            playlist = []
            for item in result['entries']:
                if item['title']=='[Private video]' and item['title'] == '[Deleted video]':
                    continue
                title = item['title']
                author = item['uploader']
                url = item['url']
                duration = int(item['duration'])
                thumbnail = get_thumbnailYT(item['thumbnails'])
                playlist.append({
                    'title'     : title, 
                    'author'    : author, 
                    'query'     : url,
                    'source'    :'query',
                    'url'       : url,
                    'thumbnail' : thumbnail,
                    'duration'  : duration})
            return playlist
    except Exception as e:
        error_log('GetYTPlaylist', e, link)
        return None

def GetYTMSong(link:str):
    try:
        link = link.replace(' ','').replace('\n','')
        ytmusic = YTMusic()
        splitURL = link.split('&list=')[0]
        splitURL = link.split('watch?v=')[1]
        songID = splitURL.split('&')[0]
        song = ytmusic.get_song(songID)
        title = song['videoDetails']['title']
        author = song['videoDetails']['author']
        duration = int(song['videoDetails']['lengthSeconds'])
        url = f'https://music.youtube.com/watch?v={song['videoDetails']['videoId']}'
        thumbnail = get_thumbnailYT(song['videoDetails']['thumbnail']['thumbnails'])
        return {
            'title' :title, 
            'author':author, 
            'query' : f'{title} by {author}',
            'source': 'query',
            'url'   : url,
            'thumbnail': thumbnail,
            'duration' : duration}
    except Exception as e:
        error_log('GetYTMSong', e, link)
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
            url = f'https://music.youtube.com/watch?v={song['videoId']}'
            thumbnail = get_thumbnailYT(song['thumbnails'])
            author = get_author(song['artists'])
            duration = song['duration']
            formatted_playlist.append({
                'title'    : title, 
                'author'   : author,
                'query'    : f'{title} by {author}',
                'source'   : 'query',
                'url'      : url,
                'thumbnail': thumbnail,
                'duration' : duration})
        return formatted_playlist
    except Exception as e:
        error_log('GetYTMPlaylist', e, link)
        return None



def GetSpotifyTrack(spotify:spotipy.Spotify, link):
    try:
        link = link.replace(' ','').replace('\n','')
        # Retrieve track information
        track_info = None
        try:
            track_info = spotify.track(link)
        except Exception as e:
            error_log('GetSpotifyTrack', e)
            time.sleep(.1)
            log('N/A', 'trying again')
        if track_info is None:
            track_info = spotify.track(link)
        # Extract title and artist from track information
        title = track_info['name']
        url = track_info['external_urls']['spotify']
        thumbnail = get_thumbnailSpotify(track_info['album']['images'])
        duration = int(track_info['duration_ms'])/1000
        author = get_author(track_info['artists'])
        return {
            'title' : title, 
            'author': author,
            'query' : f'{title} by {author}',
            'source':'query',
            'url':url,
            'thumbnail':thumbnail,
            'duration' :duration}
    except Exception as e:
        error_log('GetSpotifyTrack', e, link)
        return None
    
def GetSpotifyPlaylist(spotify:spotipy.Spotify, link):
    try:
        link = link.replace(' ','').replace('\n','')
        # Initialize Spotipy with your credentials
        # Get playlist tracks
        results = None
        try:
            results = spotify.playlist_tracks(link)
        except Exception as e:
            error_log('GetSpotifyPlaylist', e)
            time.sleep(.1)
            log('N/A', 'trying again')
        if results is None:
            results = spotify.playlist_tracks(link)
        # Extract track names
        playlist = []
        for item in results['items']:
            track_info = item['track']
            title = track_info['name']
            url = track_info['external_urls']['spotify']
            thumbnail = get_thumbnailSpotify(track_info['album']['images'])
            author = get_author(track_info['artists'])
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
    except Exception as e:
        error_log('GetSpotifyPlaylist', e, link)
        return None
    
def GetSpotifyArtist10(spotify:spotipy.Spotify, link):
    try:
        link = link.replace(' ','').replace('\n','')
        results = None
        try:
            results = spotify.artist_top_tracks(link)
        except Exception as e:
            error_log('GetSpotifyArtist10', e)
            time.sleep(.1)
            log('N/A', 'trying again')
        if results is None:
            results = spotify.artist_top_tracks(link)
        playlist = []
        for track_info in results['tracks']:
            title = track_info['name']
            url = track_info['external_urls']['spotify']
            thumbnail = get_thumbnailSpotify(track_info['album']['images'])
            author = get_author(track_info['artists'])
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
    except Exception as e:
        error_log('GetSpotifyArtist10', e, link)
        return None

def GetSpotifyAlbum(spotify:spotipy.Spotify, link):
    try:
        link = link.replace(' ','').replace('\n','')
        results = None
        try:
            results = spotify.album_tracks(link)
        except Exception as e:
            error_log('GetSpotifyAlbum', e)
            time.sleep(.1)
            log('N/A', 'trying again')
        if results is None:
            results = spotify.album_tracks(link)
        playlist = []
        for track_info in results['items']:
            title = track_info['name']
            url = track_info['external_urls']['spotify']
            duration = int(track_info['duration_ms'])/1000
            author = get_author(track_info['artists'])
            playlist.append({
                'title':title, 
                'author':author,
                'query' : f'{title} by {author}',
                'source': 'spotify',
                'url':url,
                'thumbnail':None,
                'duration': duration})
        return playlist
    
    except Exception as e:
        error_log('GetSpotifyAlbum', e, link)
        return None


def get_thumbnailYT(thumbnails):
    if len(thumbnails) > 0:
        return thumbnails[-1]['url']
    else: return

def get_thumbnailSpotify(thumbnails):
    if len(thumbnails) > 0:
        return thumbnails[0]['url']
    else: return
def get_author(artists):
    author = ''
    for artist in artists:
        author += artist['name'] +', '
    author = author[:-2]
    return author