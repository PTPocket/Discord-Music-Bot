import yt_dlp, spotipy
from ytmusicapi     import YTMusic
from spotipy.oauth2 import SpotifyClientCredentials
from cog.helper.Log import *


def SearchYoutube(query):
    ydl_opts = {
        'quiet': True,
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        # Search for videos matching the query
        result = ydl.extract_info(f"ytsearch1:{query}", download=False)
    
    try:
        song = result['entries'][0]
        return {
            'title' : song['title'], 
            'author': song['uploader'],
            'url'   : song['url'],
            'query' : query,
            'source': 'query',}
    except Exception as e:
        error_log('SearchYoutube', e, query)
        try:
            song = result
            return {
                'title' : song['title'], 
                'author': song['uploader'],
                'url'   : song['url'],
                'query' : query,
                'source': 'query',}
        except Exception as e:
            error_log('SearchYoutube', e, query)
            return {'title' : '', 
                    'author': '', 
                    'url'   : '', 
                    'query' : query,
                    'source': 'query'}

def GetYT(link):
    if 'watch?v=' in link:
        return GetYTSong(link)
    if '/playlist' in link: 
        return GetYTPlaylist(link)
    return None
def GetYTMusic(link):
    if '/watch?v=' in link:
        return GetYTMSong(link)
    if '/playlist?list=' in link:
        return GetYTMPlaylist(link)
    return
def GetSpotify(link, client_id, client_secret):
    if 'open.spotify.com/playlist' in link:
        return GetSpotifyPlaylist(link, client_id, client_secret)
    if 'open.spotify.com/album' in link:
        return GetSpotifyAlbum(link, client_id, client_secret)
    if 'open.spotify.com/artist' in link:
        return GetSpotifyArtist10(link, client_id, client_secret)
    if 'open.spotify.com/track' in link:
        return GetSpotifyTrack(link, client_id, client_secret)
    return None


def GetYTSong(link):
    try:
        link = link.replace(' ','').replace('\n','')
        link = link.split('&')[0]
        song = {
            'title' : link, 
            'author':None, 
            'query':link,
            'source':'query'}
        return song
    except Exception as e:
        error_log('GetYTSong', e, link)
    return None
def GetYTPlaylist(link):
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'force_generic_extractor': True,
    }
    try:
        link = link.replace(' ','').replace('\n','')
        playlistID = link.split('list=')[1]
        link = 'https://www.youtube.com/playlist?list='+playlistID

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(link,download=False)
            playlist = []
            for item in result['entries']:
                if item['title']=='[Private video]' and item['title'] == '[Deleted video]':
                    continue
                title = item['title']
                author = item['uploader']
                url = item['url']
                playlist.append({
                    'title':title, 
                    'author':author, 
                    'query' : url,
                    'source':'query'})
            return playlist
    except Exception as e:
        error_log('GetYTPlaylist', e, link)
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
        return {
            'title' :title, 
            'author':author, 
            'query' : f'{title} by {author}',
            'source': 'query'}
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
            author = ''
            for artist in song['artists']:
                author += artist['name'] +', '
            author = author[:-2]
            formatted_playlist.append({
                'title':title, 
                'author':author,
                'query' : f'{title} by {author}',
                'source': 'query'})
        return formatted_playlist
    except Exception as e:
        error_log('GetYTMPlaylist', e, link)
    return None

def GetSpotifyTrack(link, client_id, client_secret):
    try:
        client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
        spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
        link = link.replace(' ','').replace('\n','')
        # Retrieve track information
        track_info = spotify.track(link)
        # Extract title and artist from track information
        title = track_info['name']
        author = ''
        for artist in track_info['artists']:
            author += artist['name'] +', '
        author = author[:-2]
        return {
            'title' : title, 
            'author': author,
            'query' : f'{title} by {author}',
            'source':'query'}
    except Exception as e:
        error_log('GetSpotifyTrack', e, link)
    return None
def GetSpotifyPlaylist(link, client_id, client_secret):
    try:
        client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
        spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
        link = link.replace(' ','').replace('\n','')
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
            playlist.append({
                'title':title, 
                'author':author,
                'query' : f'{title} by {author}',
                'source': 'query'})
        return playlist
    except Exception as e:
        error_log('GetSpotifyPlaylist', e, link)
    return None
def GetSpotifyAlbum(link, client_id, client_secret):
    try:
        client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
        spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
        link = link.replace(' ','').replace('\n','')
        results = spotify.album_tracks(link)
        playlist = []
        for item in results['items']:
            title = item['name']
            author = ''
            for artist in item['artists']:
                author+=artist['name']+', '
            author = author[:-2]
            playlist.append({
                'title':title, 
                'author':author,
                'query' : f'{title} by {author}',
                'source': 'query'})
        return playlist
    except Exception as e:
        error_log('GetSpotifyAlbum', e, link)
    return None
def GetSpotifyArtist10(link, client_id, client_secret):
    try:
        client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
        spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
        link = link.replace(' ','').replace('\n','')
        results = spotify.artist_top_tracks(link)
        playlist = []
        for item in results['tracks']:
            title = item['name']
            author = ''
            for artist in item['artists']:
                author+=artist['name']+', '
            author = author[:-2]
            playlist.append({
                'title':title, 
                'author':author,
                'query' : f'{title} by {author}',
                'source': 'query'})
        return playlist
    except Exception as e:
        error_log('GetSpotifyArtist10', e, link)
    return None

