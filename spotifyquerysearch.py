import asyncio, os, time
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

SPOTIFY_CLIENT_ID = '824363ac6a4a4217b3fa9b25f85cb8ef'
SPOTIFY_CLIENT_SECRET = 'e1045eaaf3444f7cac187af6df0c8a3c'
client_credentials_manager = SpotifyClientCredentials(client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET)
spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

def search_spotify(query):
    result = spotify.search(q=query, type='track', limit=1)
    tracks = result['tracks']['items'][0]
    title = tracks['name']
    author = ''
    for artist in tracks['artists']:
        author += artist['name'] +', '
    author = author[:-2]
    return {
        'title' : title, 
        'author': author,
        'query' : f'{title} by {author}',
        'source':'query'}

while True:
    query = input('Enter Song: ')
    result = search_spotify(query)
    print(result)
