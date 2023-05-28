import discord
MUSIC_ICON = "https://cdn1.iconfinder.com/data/icons/music-audio-9/24/vinyl_player_retro_dj_disk_music_mix_2-512.png"
COG_NAME = "Pocket Muse"   

BLANK = '\u200b'

def pause(bot, song):
    bot_avatar = bot.user.display_avatar
    embed = discord.Embed(
        title=f":play_pause: **Paused Song** :play_pause:",
        description=f"***```{song}```***",
        color=discord.Color.dark_orange()) 
    embed.set_thumbnail(url=MUSIC_ICON)
    embed.set_author(name=COG_NAME, icon_url=bot_avatar)     
    return embed

def pause_err(bot, song):
        
    bot_avatar = bot.user.display_avatar
    
    if song is None:
        embed = discord.Embed(
            title=f":no_entry_sign: **No song to pause** :no_entry_sign:",
            color=discord.Color.red()) 
    else:
        embed = discord.Embed(
            title=f":play_pause: **Already paused...** :no_entry_sign:",
            description=f"***```{song['title']}```***",
            color=discord.Color.red()) 
    embed.set_thumbnail(url=MUSIC_ICON)
    embed.set_author(name=COG_NAME, icon_url=bot_avatar)     
    return embed

def resume(bot, song):
    bot_avatar = bot.user.display_avatar
    embed = discord.Embed(
        title=f":play_pause: **Resumed Song** :play_pause:",
        description=f"***```{song}```***",
        color=discord.Color.green()) 
    embed.set_thumbnail(url=MUSIC_ICON)
    embed.set_author(name=COG_NAME, icon_url=bot_avatar)     
    return embed

def resume_err(bot, song):
    bot_avatar = bot.user.display_avatar

    if song is None:
        embed = discord.Embed(
            title=f":no_entry_sign: **No song to resume** :no_entry_sign:",
            color=discord.Color.red()) 
    else:
        embed = discord.Embed(
            title=f":play_pause: **Already playing...** :no_entry_sign:",
            description=f"***```{song['title']}```***",
            color=discord.Color.red()) 
    embed.set_thumbnail(url=MUSIC_ICON)
    embed.set_author(name=COG_NAME, icon_url=bot_avatar)     
    return embed

def play(bot, song):
    bot_avatar = bot.user.display_avatar

    song = (song[:30] + '...') if len(song) > 30 else song

    embed = discord.Embed(
        title=f":musical_note: **Now Playing** :musical_note:",
        description=f"***```{song}```***",
        color=discord.Color.blue()) 
    embed.set_thumbnail(url=MUSIC_ICON)
    embed.set_author(name=COG_NAME, icon_url=bot_avatar)     
    return embed

def queue_summary(bot, song_list):

    text_length = 30

    bot_avatar = bot.user.display_avatar
    descr_msg = ''
    for ind, song in enumerate(song_list):
        
        descr_msg += "***```"
        song_text = ''
        if ind == 0:
            song_text += 'Next: '
        else:
            song_text += f'{ind}: '
        
        song = song['title']
        song_text+=f"\"{song}\""
        song_text = (song_text[:text_length] + '..') if len(song_text) > text_length else song_text

        descr_msg += f"{song_text}```*** "
    if len(song_list) == 0:
        descr_msg = "***```empty```***"
    embed = discord.Embed(
        title=f":arrow_right_hook: **Queue** :leftwards_arrow_with_hook:",
        description= descr_msg,
        color=discord.Color.yellow()) 

    embed.set_thumbnail(url=MUSIC_ICON)
    embed.set_author(name=COG_NAME, icon_url=bot_avatar)     
    return embed 

def skip(bot, song):
    embed= None
    if song is not None:
        if len(song) > 28:
            song = song[0:28]+"..."
        bot_avatar = bot.user.display_avatar
        embed = discord.Embed(
            title=f"**Skipped Song**",
            description=f"***```{song}```***",
            color=discord.Color.green()) 
        embed.set_thumbnail(url=MUSIC_ICON)
        embed.set_author(name=COG_NAME, icon_url=bot_avatar)     
    else: 
        bot_avatar = bot.user.display_avatar
        embed = discord.Embed(
            title=f"Nothing to skip...",
            color=discord.Color.red()) 
        embed.set_thumbnail(url=MUSIC_ICON)
        embed.set_author(name=COG_NAME, icon_url=bot_avatar)     
    return embed

def loop(bot, song, loop):
    embed= None
    bot_avatar = bot.user.display_avatar
    if loop is None:
        embed = discord.Embed(
            title=f"Nothing to loop...",
            color=discord.Color.red()) 
        embed.set_thumbnail(url=MUSIC_ICON)
        embed.set_author(name=COG_NAME, icon_url=bot_avatar)
    else:
        if len(song) > 28:
                song= f"{song[0:28]}..."
        if loop:
            embed = discord.Embed(
                title=f":musical_note: **Looping  Song** :musical_note:",
                description=f"***```{song}```***",
                color=discord.Color.green()) 
            embed.set_thumbnail(url=MUSIC_ICON)
            embed.set_author(name=COG_NAME, icon_url=bot_avatar)     
        else:
            embed = discord.Embed(
                title=f":musical_note: **Stopped Looping  Song** :musical_note:",
                description=f"***```{song}```***",
                color=discord.Color.dark_orange()) 
            embed.set_thumbnail(url=MUSIC_ICON)
            embed.set_author(name=COG_NAME, icon_url=bot_avatar)
    return embed

def unauthorized(bot):
    bot_avatar = bot.user.display_avatar
    embed = discord.Embed(
        title=f":no_entry_sign: Unauthorized :no_entry_sign:",
        color=discord.Color.red())  
    embed.set_author(name=COG_NAME, icon_url=bot_avatar)  
    embed.set_thumbnail(url=MUSIC_ICON)   
    return embed

def yt_search_error(bot, song):
    bot_avatar = bot.user.display_avatar
    embed = discord.Embed(
        title=f":x: **Youtube Search Error:x:\nTry Different Input** ",
        description=f"***```Your Input: {song}```***",
        color=discord.Color.yellow()) 
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

def search_list_prompt(bot):
    bot_avatar = bot.user.display_avatar
    embed = discord.Embed(
        title=f":arrow_down: **Select Song from List** :arrow_down:",
        color=discord.Color.blurple()) 
    embed.set_thumbnail(url=MUSIC_ICON)
    embed.set_author(name=COG_NAME, icon_url=bot_avatar)     
    return embed
def timeout_error(bot):
    bot_avatar = bot.user.display_avatar
    embed = discord.Embed(
        title=f":alarm_clock: Options Timed Out :alarm_clock:",
        color=discord.Color.red())  
    embed.set_author(name=COG_NAME, icon_url=bot_avatar)  
    embed.set_thumbnail(url=MUSIC_ICON)   
    return embed
####### NOT USING ####################
def queue(bot, song):
    bot_avatar = bot.user.display_avatar
    embed = discord.Embed(
        title=f":arrows_counterclockwise: **Queued** :arrows_counterclockwise:",
        description=f"***```{song}```***",
        color=discord.Color.yellow()) 
    embed.set_thumbnail(url=MUSIC_ICON)
    embed.set_author(name=COG_NAME, icon_url=bot_avatar)     
    return embed
def reset(bot):
    bot_avatar = bot.user.display_avatar
    embed = discord.Embed(
        title=f":arrows_counterclockwise: Bot Reset :arrows_counterclockwise:",
        color=discord.Color.green())  
    embed.set_author(name=COG_NAME, icon_url=bot_avatar)  
    embed.set_thumbnail(url=MUSIC_ICON)   
    return embed

