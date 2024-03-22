import discord
from cog.helper.guild_data import Guild_Music_Properties

MUSIC_ICON = "https://cdn1.iconfinder.com/data/icons/music-audio-9/24/vinyl_player_retro_dj_disk_music_mix_2-512.png"
COG_NAME = "Pocket Muse"   

BLANK = '\u200b'

#####USING########
def title(song):
    if song is None:
        return '...'
    song = song['title']
    if len(song) > 25:
        song = song[0:25]+'...'
    return song

def gui_embed(bot, data:Guild_Music_Properties, guild_id, connect = False):
    bot_avatar = bot.user.display_avatar
    embed = discord.Embed(
        title=f":musical_note:   **MUSIC PLAYER**   :musical_note:",
        #description=f"***```{song}```***",
        color=discord.Color.blurple()) 
    embed.set_thumbnail(url=MUSIC_ICON)

    queue_msg = ''
    for ind, song in enumerate(data.get_queue(guild_id)):
        if ind == 0:
            queue_msg = f"Next : {title(song)}"
        else: queue_msg = f"{ind} : {title(song)}\n" + queue_msg
        if ind > 3:
            break
    
    if queue_msg == '': queue_msg = '...'
    if connect is True:
        queue_msg = 'Connected!'
    embed.add_field(
        name='**Queue**', 
        value = f"*```{queue_msg}```*")
    

    if connect is True:
        playing = 'Click or Enter Command' 
    else: playing = title(data.get_current_song(guild_id))
    embed.add_field(
        name='Now Playing', 
        value = f'*```{playing}```*',
        inline=False)


    features = 'Random: '
    if data.get_random(guild_id) is True:
        features +=   'On '
    else: features += 'Off'
    features += '          Loop: '
    if data.get_loop(guild_id) is True:
        features +=   'On '
    else: features += 'Off'


    embed.set_footer(text = features, icon_url=bot_avatar)
    
    return embed


def unauthorized(bot):
    bot_avatar = bot.user.display_avatar
    embed = discord.Embed(
        title=f":no_entry_sign: Unauthorized :no_entry_sign:",
        color=discord.Color.red())  
    embed.set_author(name=COG_NAME, icon_url=bot_avatar)  
    embed.set_thumbnail(url=MUSIC_ICON)   
    return embed

def search_list_prompt(bot):
    bot_avatar = bot.user.display_avatar
    embed = discord.Embed(
        title=f":arrow_down: **Select Song from List** :arrow_down:",
        color=discord.Color.blurple()) 
    embed.set_thumbnail(url=MUSIC_ICON)
    embed.set_author(name=COG_NAME, icon_url=bot_avatar)     
    return embed

def no_match(bot, query):
    bot_avatar = bot.user.display_avatar
    embed = discord.Embed(
        title=f":no_entry_sign: **No search results** :no_entry_sign:",
        description=f"***```Query: {query}```***",
        color=discord.Color.red()) 
    embed.set_thumbnail(url=MUSIC_ICON)
    embed.set_author(name=COG_NAME, icon_url=bot_avatar)     
    return embed

def yt_search_error(bot, song):
    bot_avatar = bot.user.display_avatar
    embed = discord.Embed(
        title=f":x: **Youtube Search Error:x:\nTry Different Input** ",
        description=f"***```Your Input: {song}```***",
        color=discord.Color.red()) 
    embed.set_thumbnail(url=MUSIC_ICON)
    embed.set_author(name=COG_NAME, icon_url=bot_avatar)     
    return embed

def yt_playlist_error(bot, song):
    bot_avatar = bot.user.display_avatar
    embed = discord.Embed(
        title=f":x: **Youtube Playlist Error:x:\nLink Must Contain 'youtube.com/playlist'** ",
        description=f"***```Your Input: {song}```***",
        color=discord.Color.red()) 
    embed.set_thumbnail(url=MUSIC_ICON)
    embed.set_author(name=COG_NAME, icon_url=bot_avatar)     
    return embed

def spotify_playlist_error(bot, song):
    bot_avatar = bot.user.display_avatar
    embed = discord.Embed(
        title=f":x: **Spotify Playlist Error:x:\nLink Must Contain 'spotify.com/playlist'** ",
        description=f"***```Your Input: {song}```***",
        color=discord.Color.red()) 
    embed.set_thumbnail(url=MUSIC_ICON)
    embed.set_author(name=COG_NAME, icon_url=bot_avatar)     
    return embed

def playlist_error(bot, song):
    bot_avatar = bot.user.display_avatar
    embed = discord.Embed(
        title=f":x: **Playlist Error:x:\nSpotify or Youtube Link Only'** ",
        description=f"***```Your Input: {song}```***",
        color=discord.Color.red()) 
    embed.set_thumbnail(url=MUSIC_ICON)
    embed.set_author(name=COG_NAME, icon_url=bot_avatar)     
    return embed