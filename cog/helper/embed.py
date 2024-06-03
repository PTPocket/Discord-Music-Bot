import discord
from   cog.helper.GuildData import Guild_Music_Properties
import cog.helper.Setting  as Setting

MUSIC_ICON = "https://cdn1.iconfinder.com/data/icons/music-audio-9/24/vinyl_player_retro_dj_disk_music_mix_2-512.png"
COG_NAME = "Pocket Muse"   

BLANK = '\u200b'

#####USING########
def title(title, length = 37):
    if len(title) > length:
        title = title[0:length]+'...'
    return title

def HelpPrompt(bot):
    bot_avatar = bot.user.display_avatar
    embed = discord.Embed(
        title=f"**Help Menu**",
        color=discord.Color.blurple()) 
    
    embed.add_field(
        name='', 
        value = "",
        inline=False)
    
    info_text = '- Uses SLASH and TEXT commands\n'
    info_text+= '- UI generated in the text channel\n'
    info_text+= '- Searches youtube to play songs\n'
    embed.add_field(
        name=':information_source:  **Quick Info**', 
        value = f"*```{info_text}```*",
        inline=False)
    
    embed.add_field(
        name='', 
        value = "",
        inline=False)
    embed.add_field(
        name='', 
        value = "",
        inline=False)
    howto_text = 'Slash Command\n'
    howto_text+= '1. Type slash command prefix /\n'
    howto_text+= '2. Select command\n'
    howto_text+= '3. Type query\n'
    howto_text+= '4. Enter\n\n'
    howto_text+= 'Text Command (Short Commands)\n'
    howto_text+= '1. Type text command prefix / ! or ?\n'
    howto_text+= '2. Type a command\n'
    howto_text+= '3. Add space then type query\n'
    howto_text+= '4. Enter'
    embed.add_field(
        name='**:tools:  How to Use**', 
        value = f"*```{howto_text}```*",
        inline=False)
    
    embed.add_field(
        name='', 
        value = "",
        inline=False)
    embed.add_field(
        name='', 
        value = "",
        inline=False)
    valid_text = '- Any Song Title\n'
    valid_text+= '- Youtube Video Link\n'
    valid_text+= '- Youtube Playlist Link\n'
    valid_text+= '- Youtube Music Track Link\n'
    valid_text+= '- Youtube Music Playlist Link\n'
    valid_text+= '- Spotify Track Link'
    valid_text+= '- Playlist Link'
    embed.add_field(
        name='\n:ballot_box_with_check:  **Valid Query**', 
        value = f"*```{valid_text}```*",
        inline=False)
    
    embed.add_field(
        name='', 
        value = "",
        inline=False)
    embed.add_field(
        name='', 
        value = "",
        inline=False)
    command_list = '- /play        /p        /p query\n'
    command_list+= '- /skip        /s        /s\n'
    command_list+= '- /help        /h        /p\n'
    command_list+= '- /play_random /r        /r'
    embed.add_field(
        name=':notepad_spiral:  **Command List**', 
        value = f"*```  Command      Short      Example\n{command_list}```*",
        inline=False)
    embed.set_footer(text = 'Note:   /  !  ?   can be used interchangeably for text commands', icon_url=bot_avatar)
    embed.set_thumbnail(url=MUSIC_ICON)
    embed.set_author(name=COG_NAME, icon_url=bot_avatar)     
    
    return embed
##### Not From Setting ######
def MainGuiPrompt(bot, data:Guild_Music_Properties, guild_id, connect = False):
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
            next_song = title(song['title'],17)
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
    else:last_song= title(last_song['title'],17)
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
    
    current = data.get_current_song(guild_id)
    if current is None:
        current = '...'
    else:
        if current['author'] is None:
            current = current['title']
        else:
            current = current['title'] + ' by ' + current['author']

    embed.add_field(
        name='', 
        value = line,
        inline=False)


    embed.add_field(
        name='Now Playing', 
        value = f'*```{current}```*',
        inline=False)

    features = 'Shuffle: '
    if data.get_shuffle(guild_id) is True:
        features += 'On '
    else: 
        features += 'Off'
    features += '          Loop: '
    if data.get_loop(guild_id) is True:
        features += 'On '
    else: 
        features += 'Off'
    features += '          Random: '
    if data.get_random(guild_id) is True:
        features +='On '
    else:
        features +='Off'

    embed.set_footer(text = features, icon_url=bot_avatar)
    
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

def invalid_link(bot, song, platform=''):
    bot_avatar = bot.user.display_avatar
    embed = discord.Embed(
        title=f"**Invalid {platform} Link**\nAllowed:  __Spotify__,  __Youtube__,  __YTMusic__\nPlaylist must be public!",
        description=f"***```Your Input: {song}```***",
        color=discord.Color.red()) 
    embed.set_thumbnail(url=MUSIC_ICON)
    embed.set_author(name=COG_NAME, icon_url=bot_avatar)     
    return embed

###### From Setting ######



def unauthorized_prompt(bot):
    bot_avatar = bot.user.display_avatar
    text = Setting.get_unauthorizedText()
    embed = discord.Embed(
        title=f":no_entry_sign: **{text}** :no_entry_sign:",
        color=discord.Color.red())  
    embed.set_author(name=COG_NAME, icon_url=bot_avatar)  
    embed.set_thumbnail(url=MUSIC_ICON)   
    return embed

def skip_error_prompt(bot):
    bot_avatar = bot.user.display_avatar
    text = Setting.get_skiperrorText()
    embed = discord.Embed(
        title=f":no_entry_sign: **{text}** :no_entry_sign:",
        color=discord.Color.red())  
    embed.set_author(name=COG_NAME, icon_url=bot_avatar)  
    embed.set_thumbnail(url=MUSIC_ICON)   
    return embed

def queue_prompt(bot, song_name):
    bot_avatar = bot.user.display_avatar
    text = Setting.get_queueText()
    embed = discord.Embed(
        color=discord.Color.green())  
    embed.add_field(
        name=f'**{text}**', 
        value = f'*```{song_name}```*',
        inline=False)
    embed.set_author(name=COG_NAME, icon_url=bot_avatar)  
    embed.set_thumbnail(url=MUSIC_ICON)   
    return embed

def flush_prompt(bot):
    bot_avatar = bot.user.display_avatar
    text = Setting.get_flushText()
    embed = discord.Embed(
        color=discord.Color.green())  
    embed.add_field(
        name=f'**{text}**', 
        value = '',
        inline=False)
    embed.set_author(name=COG_NAME, icon_url=bot_avatar)  
    embed.set_thumbnail(url=MUSIC_ICON)   
    return embed

def finished_prompt(bot):
    bot_avatar = bot.user.display_avatar
    text = Setting.get_finishedText()
    embed = discord.Embed(
        color=discord.Color.green())  
    embed.add_field(
        name=f'**{text}**', 
        value = '',
        inline=False)
    embed.set_author(name=COG_NAME, icon_url=bot_avatar)  
    embed.set_thumbnail(url=MUSIC_ICON)   
    return embed


##### Unused
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