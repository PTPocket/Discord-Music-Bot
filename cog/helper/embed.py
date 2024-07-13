import discord, os
from   cog.helper.GuildData import GuildData
from discord.ext            import commands
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
class Embeds():
    def __init__(self, bot:commands.Bot, dataObj:GuildData):
        self.bot = bot
        self.dataObj = dataObj

    def title(self, title, length = 37):
        if len(title) > length:
            title = title[0:length]+'...'
        return title

    def channel_emb(self, channel):
        return f'<#{channel.id}>'

    def get_commandText(self, key):
        if key in COMMAND_IDS:
            return f'</{key}:{COMMAND_IDS[key]}>'
        return None

    def duration(self, dur):
        if ':' not in str(dur):
            minutes= int(dur/60)
            seconds= int(dur%60)
            if seconds < 10:
                seconds = '0'+str(seconds)
            return f'{minutes}:{seconds}'
        return dur

    def format_song(self, song, length = 37, ind=None):
        if song['source'] == 'Local':
            text = f'{song['title']} - {song['author']}'
            if len(text) > length:
                text = f'`{text[:length]}` '
            else:
                text = f'`{text}`'
            if ind is not None:
                text = f'{SPACE*(NUM_SPACES)}{ind}.  '+ text
            if song['duration'] is not None:
                text = f'{text} `{self.duration(song['duration'])}`'
            return text
        title = ''
        if song['title'] is not None:
            song_title = song['title'].replace('[','')
            song_title = song_title.replace(']','')
            title+=song_title
        title+=' - '
        if song['author'] is not None:
            author = song['author'].replace('[','')
            author = author.replace(']','')
            title+=author
        if len(title) > length:
            title = title[:length-3]+'...'
        index = ''
        if ind is not None:
            index= f'{SPACE*(NUM_SPACES)}{ind}.  '
        text= f'{index}[{title}]('
        if song['url'] is not None:
            text+=song['url']
        text+=') '
        if song['duration'] is not None:
            text+= f'`{self.duration(song['duration'])}`'
        return text


    def MainGuiPrompt(self, guildID):
        try:
            bot_avatar = self.bot.user.display_avatar
            line = ''
            embed = discord.Embed(color=discord.Color.blurple()) 
            next_text = None
            queue_msg = ''
            queue_title = f'**__Queue__**'
            queue = self.dataObj.get_queue(guildID)
            for ind, song in enumerate(queue):
                if ind == 0:
                    next_text = self.format_song(song, 20)
                else: 
                    song_title = self.format_song(song, 25, ind=ind)
                    queue_msg = song_title +"\n" + queue_msg

                if ind > 4 and ind < len(queue)-2:
                    queue_title += f' +({len(queue)-ind-1} songs)'
                    #queue_msg = f'{SPACE}+ {len(queue)-ind-1} songs\n' + queue_msg
                    break

            if queue_msg == '': 
                queue_title= f'**__All commands__**'
                queue_msg+= f'\n\n**Music Player functions**\n'
                queue_msg+= f'{self.get_commandText('skip')} | {self.get_commandText('next')} | {self.get_commandText('previous')}\n'
                queue_msg+= f'{self.get_commandText('pause')} | {self.get_commandText('resume')}\n'
                queue_msg+= f'{self.get_commandText('shuffle')} | {self.get_commandText('loop')}'
                queue_msg+= f'\n\n**Play a song or playlist**\n'
                queue_msg+= f'{self.get_commandText('play')} | {self.get_commandText('playrandom')}'
            
            #NEXT AND PREVIOUS SONG #####
            last_song = self.dataObj.get_prev_song(guildID)

            if next_text is None:
                next_text = ''
            previous_text = ''
            if last_song is not None: 
                previous_text = self.format_song(last_song, length=20)
            song = self.dataObj.get_current(guildID)
            if song is None:
                song_text = f'No songs ! Queue a song with {self.get_commandText('play')} '
                embed.set_image(url=bot_avatar)
            else:
                if song['thumbnail'] is not None:
                    embed.set_image(url=song['thumbnail'])
                song_text = self.format_song(song)

            queue_msg     = queue_msg
            queue_title   = queue_title
            next_text     = next_text
            previous_text = previous_text
            footer_text   = f'Search Algo : {Setting.get_searchAlgorithm(guildID)}'
            footer_url    = bot_avatar

            embed.set_author(name = self.bot.user.name+' '+'Controller', icon_url=bot_avatar)
            embed.add_field(
                name='', 
                value=line,
                inline=False)
            embed.add_field(
                name=f'{queue_title}', 
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

    def quickInfoPrompt(self, guildID):
        embed = discord.Embed(
            title=f"**__Quick Info__**",
            color=discord.Color.blurple()) 
        searchAlgo = Setting.get_searchAlgorithm(guildID)
        commandPrefix = Setting.get_guildPrefix(guildID)
        quickinfo = f'**Command Prefix : **`{commandPrefix}`\n'
        quickinfo+= f' - Change command prefix with {self.get_commandText('prefix')}\n'
        quickinfo+= f'\n**Search Algorithm : **`{searchAlgo}`\n'
        quickinfo+= f' - Change search algorithm with {self.get_commandText('switch_algorithm')}\n'
        quickinfo+= f'\n**Supports : **[Spotify](https://open.spotify.com/) | [Youtube](https://www.youtube.com) | [YoutubeMusic](https://music.youtube.com/)\n'

        prefix = Setting.get_guildPrefix(guildID)
        commandsTitle = f'**__All Commands__**'
        commandsText = '**Command Format**\n'
        commandsText+= f' - {self.get_commandText('slashcommand')} | `/textcommand` - `Description`\n'
        commandsText+= '\n**Play Song/Playlist Commands**\n'
        commandsText+= f'- {self.get_commandText('play')} | `{prefix}p` - `Play a song or playlist`\n'
        commandsText+= f'- {self.get_commandText('playrandom')} | `{prefix}pr` - `Play random songs forever (local library)`\n'
        bot_avatar = self.bot.user.display_avatar
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
    def all_commands_prompt(self, guildID):
        bot_avatar = self.bot.user.display_avatar
        embed = discord.Embed(
            color=discord.Color.blurple()) 
        searchAlgo = Setting.get_searchAlgorithm(guildID)
        prefix = Setting.get_guildPrefix(guildID)
        commandsText = '**Music Player Commands**\n'
        commandsText+= f'- {self.get_commandText('skip')} | `{prefix}s` - `Skips song`\n'
        commandsText+= f'- {self.get_commandText('next')} | `{prefix}n` - `Same as skip`\n'
        commandsText+= f'- {self.get_commandText('previous')} | `{prefix}prev` - `Previous song`\n'
        commandsText+= f'- {self.get_commandText('pause')} | `{prefix}pa` - `Pauses song`\n'
        commandsText+= f'- {self.get_commandText('resume')} | `{prefix}r` - `Resumes song`\n'
        commandsText+= f'- {self.get_commandText('shuffle')} | `{prefix}sh` - `Shuffles songs`\n'
        commandsText+= f'- {self.get_commandText('loop')} | `{prefix}l` - `Loops currently playing song`\n'
        commandsText+= '\n**Miscellaneous Commands**\n'
        commandsText+= f'- {self.get_commandText('flush')} | `{prefix}f` - `Empty music library`\n'
        commandsText+= f'- {self.get_commandText('join')} | `{prefix}j` - `Join PocBot to voice channel`\n'
        commandsText+= f'- {self.get_commandText('help')} | `{prefix}h` - `Help information`\n'
        commandsText+= f'- {self.get_commandText('reset')} - `Empty music library and disconnect`\n'
        commandsText+= f'- {self.get_commandText('prefix')} - `Change command prefix`\n'
        commandsText+= f'- {self.get_commandText('generate')} - `Generates text channel for music controller`\n'
        commandsText+= f'- {self.get_commandText('switch_algorithm')} - `Change the search algorithm`\n'
        
        
        footer_text = f'Search Algo: {searchAlgo}'

        embed.add_field(
            name= '', 
            value = commandsText,
            inline=False)
        embed.set_footer(icon_url=bot_avatar, text=footer_text)
        return embed

    def queued_playlist_prompt(self, song_names_list, num_of_songs, url, type):
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
            name=f'**{type.capitalize()} Playlist**', 
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
        return embed

    ###################
    def uniform_emb(self, text, color = None, searchAlgorithm = None, imgUrl = None):
        embed = discord.Embed(description = text)
        if searchAlgorithm is not None:
            embed.set_footer()
        if imgUrl is not None:
            embed.set_image(url = imgUrl)
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
    def now_playing_prompt(self, song):
        if song is None:
            text = f'Now playing...'
            songthumbnail  = ''
        else:
            text = f'Now playing : {self.format_song(song)}'
            songthumbnail  = song['thumbnail']
        return self.uniform_emb(text,color='green',imgUrl=songthumbnail)

    def resume_prompt(self, song):
        text = f'Resumed : {self.format_song(song)}'
        return self.uniform_emb(text,color='green')

    def joined_prompt(self, channel):
        guild = self.channel_emb(channel)
        text = f'Joined : {guild}'
        return self.uniform_emb(text,color='green')

    def flush_prompt(self):
        text = 'Removed all songs'
        return self.uniform_emb(text,color='green')

    def generated_prompt(self):
        text = 'Generated text channel and music player interface'
        return self.uniform_emb(text,color='green')

    def reset_prompt(self):
        text = 'Reset PocBot'
        return self.uniform_emb(text,color='green')

    def search_algorithm_prompt(self, searchAlgo):
        text = f'Switch to {searchAlgo} search algorithm'
        return self.uniform_emb(text,color='green')

    def search_algorithm_prompt(self, searchAlgo):
        text = f'Switch to {searchAlgo} search algorithm'
        return self.uniform_emb(text,color='green')

    def changed_prefix_prompt(self, prefix):
        text = f'Changed prefix : `{prefix}`'
        return self.uniform_emb(text, color='green')

    def synced_prompt(self):
        text = f'Synced commands'
        return self.uniform_emb(text, color='green')

    #### YELLOW EMBEDS ###
    def shuffle_prompt(self):
        text = 'Shuffled songs'
        return self.uniform_emb(text,color='yellow')

    def skip_prompt(self, song):
        text = f'Skipped : {self.format_song(song)}'
        return self.uniform_emb(text,color='yellow')

    def previous_prompt(self, song):
        text = f'Skipped back to : {self.format_song(song)}'
        return self.uniform_emb(text,color='yellow')

    def queue_prompt(self, song):
        text = f'Queued : {self.format_song(song)}'
        return self.uniform_emb(text,color='yellow')

    def loop_prompt(self, loop, song):
        if loop:
            title = 'Now looping'
            color='green'
        else:
            title = 'Stopped looping'
            color='yellow'
        text = f'{title} : {self.format_song(song)}'
        return self.uniform_emb(text,color=color)

    def random_prompt(self, random):
        if random:
            text = 'Playing random songs'
            color='green'
        else:
            text = 'Stopped random songs'
            color='yellow'
        return self.uniform_emb(text,color=color)

    def pause_prompt(self, song):
        text = f'Paused : {self.format_song(song)}'
        return self.uniform_emb(text,color='yellow')

    def finished_prompt(self):
        command = self.get_commandText('play')
        text = f'No more songs ! Queue song with {command}'
        return self.uniform_emb(text,color='yellow')

    def already_paused_prompt(self, song):
        text = f'Already paused : {self.format_song(song)}'
        return self.uniform_emb(text,color='yellow')

    def already_playing_prompt(self, song):
        text = f'Already playing : {self.format_song(song)}'
        return self.uniform_emb(text,color='yellow')

    def try_again_prompt(self):
        text = 'Overloaded ! Try again in a few seconds'
        return self.uniform_emb(text,color='yellow')

    #### RED EMBEDS ###
    def blank_prefix_prompt(self, prefix):
        text = f'Prefix cannot be blank`'
        return self.uniform_emb(text, color='red')

    def no_space_prefix_prompt(self, prefix):
        text = f'Prefix cannot have spaces`'
        return self.uniform_emb(text, color='red')

    def invalid_channel_prompt(self, channel):
        text = f'Join {self.channel_emb(channel)} to use the music player'
        return self.uniform_emb(text,color='red')

    def no_search_result_prompt(self, query):
        text = 'Song not found for query : *`{query}`*'
        return self.uniform_emb(text,color='red')

    def user_disconnected_prompt(self):
        text = 'Join a voice channel first'
        return self.uniform_emb(text,color='red')

    def already_generated_prompt(self):
        text = 'Already generated text channel and music player interface'
        return self.uniform_emb(text,color='red')

    def bot_disconnected_prompt(self):
        text = f'Nothing playing ! Queue song with {self.get_commandText('play')}'
        return self.uniform_emb(text,color='red')

    def invalid_link(self, query, platform=''):
        text = f"Invalid {platform.lower()} url : {query}"
        save_invalidUrl(platform, query)
        return self.uniform_emb(text,color='red')

    def no_query_prompt(self):
        text = f'Missing query after {self.get_commandText('play')}'
        return self.uniform_emb(text,color='red')

    def no_songs_prompt(self):
        text = f'No songs ! Queue song with {self.get_commandText('play')}'
        return self.uniform_emb(text,color='red')

    def unauthorized_user_prompt(self):
        text = 'Unauthorized user ! You did not call this command'
        return self.uniform_emb(text,color='red')

    def already_joined_prompt(self, channel):
        text = 'Already joined a voice channel : ' + self.channel_emb(channel)
        return self.uniform_emb(text,color='red')
