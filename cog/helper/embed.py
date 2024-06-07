import discord
from   cog.helper.GuildData import Guild_Music_Properties
from cog.helper.Log  import *
import cog.helper.Setting  as Setting

MUSIC_ICON = "https://cdn1.iconfinder.com/data/icons/music-audio-9/24/vinyl_player_retro_dj_disk_music_mix_2-512.png"
ICON_PATH = 'C:/Users/Pocket/Documents/GitHub/Discord-Music-Bot/4105542_audio_melody_music_sound_icon.png'
COG_NAME = "Pocket Muse"   

BLANK = '\u200b'
#ICON_PATH = 'C:/Users/Pocket/Documents/GitHub/Discord-Music-Bot/4105542_audio_melody_music_sound_icon.png'
#file = discord.File(ICON_PATH, filename="thumbnail.png")
#embed.set_thumbnail(url=thumbnail.png)
#ctx.send(file=file, embed = emb)
#####USING########
def title(title, length = 37):
    if len(title) > length:
        title = title[0:length]+'...'
    return title

##### Not From Setting ######
def MainGuiPrompt(bot, data:Guild_Music_Properties, guild_id):
    try:
        bot_avatar = bot.user.display_avatar
        embed = discord.Embed(
            title=f":musical_note:   **MUSIC PLAYER**   :musical_note:",
            #description=f"***```{song}```***",
            color=discord.Color.blurple()) 
        #embed.set_thumbnail(url=MUSIC_ICON)
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
        last_song = data.get_prev_song(guild_id)
        if last_song is None: last_song = '...'
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
        current = data.get_current(guild_id)
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
        features = 'Loop: '
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
    except Exception as e:
        error_log('mainguiprompt', e)

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
    valid_text+= '- Spotify Track Link\n'
    valid_text+= '- Spotify Playlist Link'
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
    

    command_list = '- /play        /p       (play query)\n'
    command_list+= '- /skip        /s       (skip song)\n'
    command_list+= '- /pause       /pause   (pause song)\n'
    command_list+= '- /previous    /prev    (previous song)\n'
    command_list+= '- /play_random /pr      (random songs)\n'
    command_list+= '- /resume      /resume  (resume song)\n'
    command_list+= '- /shuffle     /shuffle (shuffle songs)\n'
    command_list+= '- /reset       /r       (reset bot)\n'
    command_list+= '- /flush       /f       (empty all songs)\n'
    command_list+= '- /help        /h       (open help menu)'
    embed.add_field(
        name=':notepad_spiral:  **Command List**', 
        value = f"*```  Slash        Text     Description\n{command_list}```*",
        inline=False)
    embed.add_field(
        name='', 
        value = "",
        inline=False)
    embed.add_field(
        name='', 
        value = "",
        inline=False)
    ex_text = ' - /play i like to move it move it\n'
    ex_text+= ' - /skip\n'
    ex_text+= ' - /p youtube.com/watch?v=cpKolP6mMec\n'
    ex_text+= ' - /flush'
    embed.add_field(
        name='**:mag_right:  Example Commands**', 
        value = f"*```{ex_text}```*",
        inline=False)

    embed.add_field(
        name='', 
        value = "",
        inline=False)
    embed.add_field(
        name='', 
        value = "",
        inline=False)
    
    ui_text = '\n:track_previous:  -  `Previous song`\n\n'
    ui_text+= ':play_pause:  -  `Play/Pause`\n\n'
    ui_text+= ':track_next:  -  `Next Song`\n\n'
    ui_text+= ':twisted_rightwards_arrows:  -  `Shuffle all songs`\n\n'
    ui_text+= ':arrows_counterclockwise:  -  `Loop current song`\n\n'
    ui_text+= ':infinity: Random  -  `Plays random songs forever`\n\n'
    ui_text+= ':toilet: Flush  -  `Empty all songs`\n\n'
    ui_text+= 'Reset  -  `Erases all data/Disconnects`'
    embed.add_field(
        name='**:musical_note:  Music Player (User Interface)**', 
        value = f"**{ui_text}**",
        inline=False)

    embed.set_footer(text = 'Note:   /  !  ?   can be used interchangeably for text commands', icon_url=bot_avatar)
    #embed.set_thumbnail(url=MUSIC_ICON)
    embed.set_author(name=COG_NAME, icon_url=bot_avatar)     
    
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
    #embed.set_author(name=COG_NAME, icon_url=bot_avatar)  
    embed.set_thumbnail(url=MUSIC_ICON)   
    return embed

def invalid_link(bot, song, platform=''):
    bot_avatar = bot.user.display_avatar
    embed = discord.Embed(
        title=f"**Invalid {platform} Link**\nAllowed:  __Spotify__,  __Youtube__,  __YTMusic__\nPlaylist must be public!",
        description=f"***```Your Input: {song}```***",
        color=discord.Color.red()) 
    #embed.set_thumbnail(url=MUSIC_ICON)
    embed.set_author(name=COG_NAME, icon_url=bot_avatar)     
    return embed

def no_query_prompt(bot):
    bot_avatar = bot.user.display_avatar
    embed = discord.Embed(
        title=f":no_entry_sign: **Missing Query** :no_entry_sign:",
        description=f'*```/p query```*',
        color=discord.Color.red())  
    embed.set_author(name=COG_NAME, icon_url=bot_avatar)  
    #embed.set_thumbnail(url=MUSIC_ICON)   
    return embed

def loop_prompt(bot, loop, song_name):
    bot_avatar = bot.user.display_avatar
    if loop:
        title = 'Now Looping'
    else:
        title = 'Stopped Looping'
    embed = discord.Embed(
        title=f'**{title}**', 
        description= f'*```{song_name}```*',
        color=discord.Color.green())  
    embed.set_author(name=COG_NAME, icon_url=bot_avatar)  
    #embed.set_thumbnail(url=MUSIC_ICON)   
    return embed

def reset_prompt(bot):
    bot_avatar = bot.user.display_avatar
    text = 'Reset Pocket Music Bot'
    embed = discord.Embed(
        title=f'**{text}**', 
        color=discord.Color.green())  
    embed.set_author(name=COG_NAME, icon_url=bot_avatar)  
    #embed.set_thumbnail(url=MUSIC_ICON)   
    return embed

def random_prompt(bot, random):
    bot_avatar = bot.user.display_avatar
    if random:
        text = 'Playing Random Songs'
    else:
        text = 'Stopped Random Songs'
    embed = discord.Embed(
        title=f'**{text}**', 
        color=discord.Color.green())  
    embed.set_author(name=COG_NAME, icon_url=bot_avatar)  
    #embed.set_thumbnail(url=MUSIC_ICON)   
    return embed

def resume_prompt(bot, song_name):
    bot_avatar = bot.user.display_avatar
    embed = discord.Embed(
        title=f'**Resumed**', 
        description = f'*```{song_name}```*',
        color=discord.Color.green())  
    embed.set_author(name=COG_NAME, icon_url=bot_avatar)  
    return embed

def pause_prompt(bot, song_name):
    bot_avatar = bot.user.display_avatar
    embed = discord.Embed(
        title=f'**Paused**', 
        description = f'*```{song_name}```*',
        color=discord.Color.yellow())  
    embed.set_author(name=COG_NAME, icon_url=bot_avatar)  
    return embed

def skip_prompt(bot, song_name):
    bot_avatar = bot.user.display_avatar
    embed = discord.Embed(
        title=f'**Skipped**', 
        description = f'*```{song_name}```*',
        color=discord.Color.green())  
    embed.set_author(name=COG_NAME, icon_url=bot_avatar)  
    return embed

def previous_prompt(bot, song_name):
    bot_avatar = bot.user.display_avatar
    embed = discord.Embed(
        title=f'**Skipped back to**', 
        description = f'*```{song_name}```*',
        color=discord.Color.green())  
    embed.set_author(name=COG_NAME, icon_url=bot_avatar)  
    return embed

def shuffle_prompt(bot):
    bot_avatar = bot.user.display_avatar
    embed = discord.Embed(
        title=f'**Shuffled all songs**',
        color=discord.Color.green())  
    embed.set_author(name=COG_NAME, icon_url=bot_avatar)  
    return embed

def nothing_prompt(bot, text):
    text = text.lower()
    bot_avatar = bot.user.display_avatar
    embed = discord.Embed(
        title=f'**Nothing to {text}**', 
        color=discord.Color.red())  
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
    #embed.set_thumbnail(url=MUSIC_ICON)   
    return embed

def queue_prompt(bot, song_name):
    bot_avatar = bot.user.display_avatar
    text = Setting.get_queueText()
    embed = discord.Embed(
        title = f'**{text}**',
        description = f'*```{song_name}```*',
        color=discord.Color.green())  
    embed.set_author(name=COG_NAME, icon_url=bot_avatar)  
    #embed.set_thumbnail(url=MUSIC_ICON)   
    return embed

def flush_prompt(bot):
    bot_avatar = bot.user.display_avatar
    text = Setting.get_flushText()
    embed = discord.Embed(
        title=f'**{text}**', 
        color=discord.Color.green())  
    embed.set_author(name=COG_NAME, icon_url=bot_avatar)  
    #embed.set_thumbnail(url=MUSIC_ICON)   
    return embed

def finished_prompt(bot):
    bot_avatar = bot.user.display_avatar
    text = Setting.get_finishedText()
    embed = discord.Embed(
        title = f'**{text}**',
        color=discord.Color.green())  
    embed.set_author(name=COG_NAME, icon_url=bot_avatar)  
    #embed.set_thumbnail(url=MUSIC_ICON)   
    return embed
