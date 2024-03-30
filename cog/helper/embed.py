import discord
from cog.helper.guild_data import Guild_Music_Properties

MUSIC_ICON = "https://cdn1.iconfinder.com/data/icons/music-audio-9/24/vinyl_player_retro_dj_disk_music_mix_2-512.png"
COG_NAME = "Pocket Muse"   

BLANK = '\u200b'

#####USING########
def title(title, length = 37):
    temp_title = str(title).split(' by ')
    if len(temp_title) > 1:
        remove_artist_ind = (len(title)-len(temp_title[len(temp_title)-1]))-4
        title = title[0:remove_artist_ind]
        if len(title) > length:
            title = title[0:length]+'...'
    else:
        if len(title) > length:
            title = title[0:length]+'...'
    return title


def gui_embed(bot, data:Guild_Music_Properties, guild_id, connect = False):
    bot_avatar = bot.user.display_avatar
    embed = discord.Embed(
        title=f":musical_note:   **MUSIC PLAYER**   :musical_note:",
        #description=f"***```{song}```***",
        color=discord.Color.blurple()) 
    embed.set_thumbnail(url=MUSIC_ICON)

    next_song = None
    queue_msg = ''
    queue = data.get_queue(guild_id)
    for ind, song in enumerate(queue):
        if ind == 0:
            next_song = title(song['title'],20)
        else: 
            song_title = title(f"{ind}. {song['title']}")
            queue_msg = song_title +"\n" + queue_msg
        

        if ind > 3 and ind < len(queue)-1:
            if ind < len(queue)-2:
                queue_msg = f'-  ...\n' + queue_msg
            song_title = title(f"{len(queue)-1}. {queue[len(queue)-1]['title']}")
            queue_msg = song_title +'\n'+queue_msg
            break



    if queue_msg == '': queue_msg = '...'
    if connect is True:
        queue_msg = 'Connected!'
    embed.add_field(
        name='**Queue**', 
        value = f"*```{queue_msg}```*",
        inline=False)
    if next_song is None:
        next_song = '...'
    line = ''
    embed.add_field(
        name='', 
        value=line,
        inline=False)
    #NEXT AND PREVIOUS SONG #####
    last_song = data.get_last_played(guild_id)
    if last_song is None:last_song = '...'
    else:last_song= title(last_song['title'],20)
    if len(next_song) > len(last_song):
        length_diff = len(next_song)-len(last_song)
        last_song = last_song + (' '*length_diff)
    elif len(last_song) > len(next_song):
        length_diff = len(last_song)-len(next_song)
        next_song = next_song + (' '*length_diff)
    embed.add_field(
        name='**Next**', 
        value = f"*```{next_song}```*",
        inline=True)
    embed.add_field(
        name='**Previous**', 
        value = f"*```{last_song}```*",
        inline=True)
    
    if connect is True:
        playing = 'Click or Enter Command' 
    else: 
        current = data.get_current_song(guild_id)
        if current is None:
            current = '...'
        else:
            current = current['title']
    embed.add_field(
        name='', 
        value = line,
        inline=False)


    embed.add_field(
        name='Now Playing', 
        value = f'*```{current}```*',
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
        title=f":no_entry_sign: **Unauthorized** :no_entry_sign:",
        color=discord.Color.red())  
    embed.set_author(name=COG_NAME, icon_url=bot_avatar)  
    embed.set_thumbnail(url=MUSIC_ICON)   
    return embed

def skip_error(bot):
    bot_avatar = bot.user.display_avatar
    embed = discord.Embed(
        title=f":no_entry_sign: **Nothing to Skip** :no_entry_sign:",
        color=discord.Color.red())  
    embed.set_author(name=COG_NAME, icon_url=bot_avatar)  
    embed.set_thumbnail(url=MUSIC_ICON)   
    return embed

def skip_prompt(bot, song_name):
    bot_avatar = bot.user.display_avatar
    embed = discord.Embed(
        color=discord.Color.green())  
    embed.add_field(
        name=':track_next: **Skipped Song** :track_next:', 
        value = f'*```{song_name}```*',
        inline=False)
    embed.set_author(name=COG_NAME, icon_url=bot_avatar)  
    embed.set_thumbnail(url=MUSIC_ICON)   
    return embed

def queue_prompt(bot, song_name):
    bot_avatar = bot.user.display_avatar
    embed = discord.Embed(
        color=discord.Color.green())  
    embed.add_field(
        name='**Queued**', 
        value = f'*```{song_name}```*',
        inline=False)
    embed.set_author(name=COG_NAME, icon_url=bot_avatar)  
    embed.set_thumbnail(url=MUSIC_ICON)   
    return embed

def queued_playlist_prompt(bot, song_names_list, num_of_songs, url, type):
    bot_avatar = bot.user.display_avatar
    embed = discord.Embed(
        color=discord.Color.green())  
    embed.add_field(
        name=f'**Playlist**', 
        value = '',
        inline=False)
    maximum_length = 5000
    current_total = 0
    for song_list in song_names_list:
        if current_total+len(song_list) > maximum_length:
            break
        song_list = song_list.replace('*','').replace('`','')
        embed.add_field(
            name='', 
            value = f'*```{song_list}```*',
            inline=False)
        current_total += len(song_list)
    embed.add_field(
        name='', 
        value='',
        inline=False)
    embed.add_field(
        name=f'**{type} Playlist**', 
        value = f'*```{url}```*',
        inline=False)
    embed.add_field(
        name='', 
        value='',
        inline=False)
    embed.add_field(
        name=f'**Queued**  __**{num_of_songs}**__  **Songs!**', 
        value = '',
        inline=False)
    embed.set_author(name=COG_NAME, icon_url=bot_avatar)  
    embed.set_thumbnail(url=MUSIC_ICON)   
    return embed

def flush_prompt(bot):
    bot_avatar = bot.user.display_avatar
    embed = discord.Embed(
        color=discord.Color.green())  
    embed.add_field(
        name='**Flushed Data**', 
        value = '',
        inline=False)
    embed.set_author(name=COG_NAME, icon_url=bot_avatar)  
    embed.set_thumbnail(url=MUSIC_ICON)   
    return embed

def finished_prompt(bot):
    bot_avatar = bot.user.display_avatar
    embed = discord.Embed(
        color=discord.Color.green())  
    embed.add_field(
        name='**Done**', 
        value = '',
        inline=False)
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


def invalid_link(bot, song, platform=''):
    bot_avatar = bot.user.display_avatar
    embed = discord.Embed(
        title=f"**Invalid {platform} Link**\nAllowed:  __Spotify__,  __Youtube__,  __YTMusic__\nPlaylist must be public!",
        description=f"***```Your Input: {song}```***",
        color=discord.Color.red()) 
    embed.set_thumbnail(url=MUSIC_ICON)
    embed.set_author(name=COG_NAME, icon_url=bot_avatar)     
    return embed


