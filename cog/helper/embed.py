import discord, os
from   cog.helper.GuildData import Guild_Music_Properties
from cog.helper.Log  import *
import cog.helper.Setting  as Setting


SPACE = '\u1CBC'
NUM_SPACES = 1
COMMAND_IDS = {
    'slashcommand'    : 1250539068312260611,
    'play'            : 1248888415630397563,
    'playrandom'      : 1250444887112024185,
    'skip'            : 1248888415630397565,
    'previous'        : 1248888415630397566,
    'help'            : 1248888415718736003,
    'flush'           : 1248888415630397571,
    'generate'        : 1249561601409810586,
    'loop'            : 1248888415630397570,
    'next'            : 1249561601409810585,
    'pause'           : 1248888415630397567,
    'resume'          : 1248888415630397568,
    'shuffle'         : 1248888415630397569,
    'reset'           : 1248888415630397572,
    'join'            : 1249975660248829962,
    'switch_algorithm': 1250546813769879634,
    'prefix'          : 1250546813769879635
}
def title(title, length = 37):
    if len(title) > length:
        title = title[0:length]+'...'
    return title

def channel_emb(channel):
    return f'<#{channel.id}>'

def get_commandText(key):
    if key in COMMAND_IDS:
        return f'</{key}:{COMMAND_IDS[key]}>'
    return None
def duration(dur):
    if ':' not in str(dur):
        minutes= int(dur/60)
        seconds= int(dur%60)
        if seconds < 10:
            seconds = '0'+str(seconds)
        return f'{minutes}:{seconds}'
    return dur
def format_song(song, length = 37, ind=None):
    if song is None:
        return 'None'
    if song['source'] == 'Local':
        text = f'{song['title']} - {song['author']}'
        if len(text) > length:
            text = f'`{text[:length]}` '
        else:
            text = f'`{text}`'
        if ind is not None:
            text = f'{SPACE*(NUM_SPACES)}{ind}.  '+ text
        if song['duration'] is not None:
            text = f'{text} `{duration(song['duration'])}`'
        return text
    title = ''
    if song['title'] is not None:
        title+=song['title']
    title+=' - '
    if song['author'] is not None:
        title+=song['author']
    if len(title) > length:
        title = title[:length]
    index = ''
    if ind is not None:
        index= f'{SPACE*(NUM_SPACES)}{ind}.  '
    text= f'{index}[{title}]('
    if song['url'] is not None:
        text+=song['url']
    text+=') '
    if song['duration'] is not None:
        text+= f'`{duration(song['duration'])}`'
    return text


def MainGuiPrompt(bot, data:Guild_Music_Properties, guildID):
    try:
        bot_avatar = bot.user.display_avatar
        line = ''
        embed = discord.Embed(color=discord.Color.blurple()) 
        next_text = None
        queue_msg = ''
        queue_title = f'**__Queue__**'
        queue = data.get_queue(guildID)
        for ind, song in enumerate(queue):
            if ind == 0:
                next_text = format_song(song, 20)
            else: 
                song_title = format_song(song, 25, ind=ind)
                queue_msg = song_title +"\n" + queue_msg
            if ind == len(queue)-2:
                queue_msg = f'...\n' + queue_msg
                song_title = format_song(queue[len(queue)-1],length=25, ind=len(queue)-1)
                queue_msg = song_title +'\n'+queue_msg
                break
            if ind > 4 and ind < len(queue)-2:
                queue_msg = f'{SPACE*(NUM_SPACES)}...\n' + queue_msg
                song_title = format_song(queue[len(queue)-1],length=25, ind=len(queue)-1)
                queue_msg = song_title +'\n'+queue_msg
                break
        if queue_msg == '': 
            queue_title= f'**__All commands__**'
            queue_msg = f'\n**Miscellaneous functions**\n'    
            queue_msg+= f'{get_commandText('join')} | {get_commandText('flush')}| {get_commandText('generate')}\n'
            queue_msg+= f'{get_commandText('reset')} | {get_commandText('prefix')} |{get_commandText('help')}\n'
            queue_msg+= f'{get_commandText('switch_algorithm')}'
            queue_msg+= f'\n\n**Music Player functions**\n'
            queue_msg+= f'{get_commandText('skip')} | {get_commandText('next')} | {get_commandText('previous')}\n'
            queue_msg+= f'{get_commandText('pause')} | {get_commandText('resume')}\n'
            queue_msg+= f'{get_commandText('shuffle')} | {get_commandText('loop')}'
            queue_msg+= f'\n\n**Play a song or playlist**\n'
            queue_msg+= f'{get_commandText('play')} | {get_commandText('playrandom')}'
        
        #NEXT AND PREVIOUS SONG #####
        last_song = data.get_prev_song(guildID)

        if next_text is None:
            next_text = ''
        previous_text = ''
        if last_song is not None: 
            previous_text = format_song(last_song, length=20)
        song = data.get_current(guildID)
        if song is None:
            song_text = f'No songs ! Queue a song with {get_commandText('play')} '
            embed.set_image(url=bot_avatar)
        else:
            if song['thumbnail'] is not None:
                embed.set_image(url=song['thumbnail'])
            song_text = format_song(song)

        queue_msg     = queue_msg
        queue_title   = queue_title
        next_text     = next_text
        previous_text = previous_text
        footer_text   = f'Search Algo : {Setting.get_searchAlgorithm(guildID)}'
        footer_url    = bot_avatar

        embed.set_author(name = bot.user.name+' '+'Controller', icon_url=bot_avatar)
        embed.add_field(
            name='', 
            value=line,
            inline=False)
        embed.add_field(
            name=f'**{queue_title}**', 
            value = f"{queue_msg}",
            inline=False)
        embed.add_field(
            name='', 
            value=line,
            inline=False)
        embed.add_field(
            name='**__Next__**', 
            value = f"\n{next_text}",
            inline=True)
        embed.add_field(
            name=f'**__Previous__**', 
            value = f"\n{previous_text}",
            inline=True)
        embed.add_field(
            name='', 
            value = line,
            inline=False)
        embed.add_field(
            name='__Now Playing__', 
            value = f'\n{song_text}',
            inline=False)
        embed.set_footer(text = footer_text, icon_url=footer_url)
        return embed
    except Exception as e:
        error_log('mainguiprompt', e)

def quickInfoPrompt(bot, guildID):
    embed = discord.Embed(
        title=f"**__Quick Info__**",
        color=discord.Color.blurple()) 
    searchAlgo = Setting.get_searchAlgorithm(guildID)
    commandPrefix = Setting.get_guildPrefix(guildID)
    quickinfo = f'**Command Prefix : **`{commandPrefix}`\n'
    quickinfo+= f' - Change command prefix with {get_commandText('prefix')}\n'
    quickinfo+= f'\n**Search Algorithm : **`{searchAlgo}`\n'
    quickinfo+= f' - Change search algorithm with {get_commandText('switch_algorithm')}\n'
    quickinfo+= f'\n**Supports : **[Spotify](https://open.spotify.com/) | [Youtube](https://www.youtube.com) | [YoutubeMusic](https://music.youtube.com/)\n'

    prefix = Setting.get_guildPrefix(guildID)
    commandsTitle = f'**__All Commands__**'
    commandsText = '**Command Format**\n'
    commandsText+= f' - {get_commandText('slashcommand')} | `/textcommand` - `Description`\n'
    commandsText+= '\n**Play Song/Playlist Commands**\n'
    commandsText+= f'- {get_commandText('play')} | `{prefix}p` - `Play a song or playlist`\n'
    commandsText+= f'- {get_commandText('playrandom')} | `{prefix}pr` - `Play random songs forever (local library)`\n'
    bot_avatar = bot.user.display_avatar
    embed.add_field(
        name='', 
        value = quickinfo,
        inline=False)
    embed.add_field(
        name='', 
        value = '',
        inline=False)
    embed.add_field(
        name='', 
        value = '',
        inline=False)
    embed.add_field(
        name='', 
        value = '',
        inline=False)
    embed.add_field(
        name=commandsTitle, 
        value = commandsText,
        inline=False)
    embed.set_author(icon_url=bot_avatar, name = 'Quick Info')
    return embed
def all_commands_prompt(bot, guildID):
    bot_avatar = bot.user.display_avatar
    embed = discord.Embed(
        color=discord.Color.blurple()) 
    searchAlgo = Setting.get_searchAlgorithm(guildID)
    prefix = Setting.get_guildPrefix(guildID)
    commandsText = '**Music Player Commands**\n'
    commandsText+= f'- {get_commandText('skip')} | `{prefix}s` - `Skips song`\n'
    commandsText+= f'- {get_commandText('next')} | `{prefix}n` - `Same as skip`\n'
    commandsText+= f'- {get_commandText('previous')} | `{prefix}prev` - `Previous song`\n'
    commandsText+= f'- {get_commandText('pause')} | `{prefix}pa` - `Pauses song`\n'
    commandsText+= f'- {get_commandText('resume')} | `{prefix}r` - `Resumes song`\n'
    commandsText+= f'- {get_commandText('shuffle')} | `{prefix}sh` - `Shuffles songs`\n'
    commandsText+= f'- {get_commandText('loop')} | `{prefix}l` - `Loops currently playing song`\n'
    commandsText+= '\n**Miscellaneous Commands**\n'
    commandsText+= f'- {get_commandText('flush')} | `{prefix}f` - `Empty music library`\n'
    commandsText+= f'- {get_commandText('join')} | `{prefix}j` - `Join PocBot to voice channel`\n'
    commandsText+= f'- {get_commandText('help')} | `{prefix}h` - `Help information`\n'
    commandsText+= f'- {get_commandText('reset')} - `Empty music library and disconnect`\n'
    commandsText+= f'- {get_commandText('prefix')} - `Change command prefix`\n'
    commandsText+= f'- {get_commandText('generate')} - `Generates music channel for controller`\n'
    commandsText+= f'- {get_commandText('switch_algorithm')} - `Change music search algorithm`\n'
    
    
    footer_text = f'Search Algo: {searchAlgo}'

    embed.add_field(
        name= '', 
        value = commandsText,
        inline=False)
    embed.set_footer(icon_url=bot_avatar, text=footer_text)
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
    embed.set_footer(icon_url=bot_avatar)
    return embed

###################
def uniform_emb(text, color = None, searchAlgorithm = None, imgUrl = None, searchAlgo = None, bot=None):
    embed = discord.Embed(description = text)
    if searchAlgorithm is not None:
        embed.set_footer()
    if imgUrl is not None:
        embed.set_image(url = imgUrl)
    if searchAlgo is not None:
        embed.set_footer(icon_url=bot.user.display_avatar, text=f'Search Algo : {searchAlgo}')
    if color == 'red':
        embed.color=discord.Color.red()
        return embed
    elif color == 'yellow':
        embed.color=discord.Color.yellow()
        return embed
    else:
        embed.color=discord.Color.green()
        return embed

### GREEN EMBED ###
def now_playing_prompt(bot, song, guildID):
    if song is None:
        text = f'Now playing : `random`'
        songthumbnail  = ''
    else:
        text = f'Now playing : {format_song(song)}'
        songthumbnail  = song['thumbnail']
    return uniform_emb(text,color='green',imgUrl=songthumbnail, bot= bot)

def resume_prompt(song):
    text = f'Resumed : {format_song(song)}'
    return uniform_emb(text,color='green')

def joined_prompt(channel):
    guild = channel_emb(channel)
    text = f'Joined : {guild}'
    return uniform_emb(text,color='green')

def flush_prompt():
    text = 'Removed all songs'
    return uniform_emb(text,color='green')

def generated_prompt():
    text = 'Generated text channel and music player interface'
    return uniform_emb(text,color='green')

def reset_prompt():
    text = 'Reset PocBot'
    return uniform_emb(text,color='green')

def search_algorithm_prompt(searchAlgo):
    text = f'Switch to {searchAlgo} search algorithm'
    return uniform_emb(text,color='green')

def search_algorithm_prompt(searchAlgo):
    text = f'Switch to {searchAlgo} search algorithm'
    return uniform_emb(text,color='green')

def changed_prefix_prompt(prefix):
    text = f'Changed prefix : `{prefix}`'
    return uniform_emb(text, color='green')

def synced_prompt():
    text = f'Synced commands'
    return uniform_emb(text, color='green')

#### YELLOW EMBEDS ###
def shuffle_prompt():
    text = 'Shuffled songs'
    return uniform_emb(text,color='yellow')

def skip_prompt(song):
    text = f'Skipped : {format_song(song)}'
    return uniform_emb(text,color='yellow')

def previous_prompt(song):
    text = f'Skipped back to : {format_song(song)}'
    return uniform_emb(text,color='yellow')

def queue_prompt(bot, song, guildID):
    text = f'Queued : {format_song(song)}'
    return uniform_emb(text,color='yellow', searchAlgo=Setting.get_searchAlgorithm(guildID), bot=bot)

def loop_prompt(loop, song):
    if loop:
        title = 'Now looping'
        color='green'
    else:
        title = 'Stopped looping'
        color='yellow'
    text = f'{title} : {format_song(song)}'
    return uniform_emb(text,color=color)

def random_prompt(random):
    if random:
        text = 'Playing random songs'
        color='green'
    else:
        text = 'Stopped random songs'
        color='yellow'
    return uniform_emb(text,color=color)

def pause_prompt(song):
    text = f'Paused : {format_song(song)}'
    return uniform_emb(text,color='yellow')

def finished_prompt():
    text = 'No more songs ! Queue song with'
    command = get_commandText('play')
    text = f'No more songs ! Queue song with {command}'
    return uniform_emb(text,color='yellow')

def already_paused_prompt(song):
    text = f'Already paused : {format_song(song)}'
    return uniform_emb(text,color='yellow')

def already_playing_prompt(song):
    text = f'Already playing : {format_song(song)}'
    return uniform_emb(text,color='yellow')


#### RED EMBEDS ###
def blank_prefix_prompt(prefix):
    text = f'Prefix cannot be blank`'
    return uniform_emb(text, color='red')

def no_space_prefix_prompt(prefix):
    text = f'Prefix cannot have spaces`'
    return uniform_emb(text, color='red')

def invalid_channel_prompt(channel):
    text = f'Join {channel_emb(channel)} to use the music player'
    return uniform_emb(text,color='red')

def no_search_result_prompt(query):
    text = 'Song not found for query : *`{query}`*'
    return uniform_emb(text,color='red')

def user_disconnected_prompt():
    text = 'Join a voice channel first'
    return uniform_emb(text,color='red')

def already_generated_prompt():
    text = 'Already generated text channel and music player interface'
    return uniform_emb(text,color='red')

def bot_disconnected_prompt():
    text = f'Nothing playing ! Queue song with {get_commandText('play')}'
    return uniform_emb(text,color='red')

def invalid_link(song, platform=''):
    text = f"Invalid {platform.lower()} url : {song}"
    return uniform_emb(text,color='red')

def no_query_prompt():
    text = f'Missing query after {get_commandText('play')}'
    return uniform_emb(text,color='red')

def no_songs_prompt():
    text = f'No songs ! Queue song with {get_commandText('play')}'
    return uniform_emb(text,color='red')

def unauthorized_user_prompt():
    text = 'Unauthorized user ! You did not call this command'
    return uniform_emb(text,color='red')
