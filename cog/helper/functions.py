import discord
import os
import random
import time
import asyncio
from tinytag              import TinyTag
from cog.helper           import embed
from cog.helper.GuildData import Guild_Music_Properties
from discord.ui           import View, Select, Button
from discord.ext          import commands
from cog.helper.Log       import *
from cog.helper           import Setting
from Paths                import LOCAL_MUSIC_PATH



async def GUI_HANDLER(Music_Cog, guildID, channel):
    async with Music_Cog.data.get_guiLock(guildID):
        try:
            guild = Music_Cog.bot.get_guild(guildID)
            guildName = guild.name
            channelID = Setting.get_channelID(guildID)
            channels = [channel.id for channel in guild.channels]
            if channelID not in channels:
                return
            player_embed = embed.MainGuiPrompt(Music_Cog.bot, Music_Cog.data, guildID)
            try:
                view = MusicFunctions(Music_Cog, Music_Cog.data, guildID)
            except Exception as e:
                error_log('MusicFunctions', e)
                return
            
            if channelID is None: # If channel has not been created
                return
            channel = Music_Cog.bot.get_channel(channelID)
            if channel is None:
                return
            messageID = Setting.get_messageID(guildID)
            if messageID is None:
                message = await channel.send(embed = player_embed, view = view)
                Setting.set_messageID(guildID, message.id)
                log(guildName, 'GUIPrint New', channel.name)
                return
            try:
                message = await channel.fetch_message(messageID)
            except: message = None
            if message is None:
                message = await channel.send(embed = player_embed, view = view)
                Setting.set_messageID(guildID, message.id)
                log(guildName, 'GUIPrint New', channel.name)
                return
            try:
                if channelID != channel.id:
                    await message.edit(embed = player_embed, view = view)
                    log(guildName, 'GUIPrint Edit', channel.name)
                    return
            except Exception as e: 
                error_log('GUI_HANDLER', 'editing gui message')
                log(guildName, 'GUI_HANDLER', 'sending new message')
            new_message = await channel.send(embed = player_embed, view = view)
            Setting.set_messageID(guildID, new_message.id)
            log(guildName, 'GUIPrint Replace', channel.name)
            await message.delete()
        except Exception as e:
            error_log('Gui_handler', e, guildName= guildName)
        

async def promptHandler(embed, channel):
    
    pass

async def create_bot_channel(data:Guild_Music_Properties, guild:discord.guild.Guild):
    try:
        guildID = guild.id
        data.initialize(guildID)

        pocbot_channelID = Setting.get_channelID(guildID)
        channelsIDS = [channel.id for channel in guild.channels]
        if pocbot_channelID in channelsIDS:
            return
        category = None
        for cat in guild.categories:
            if cat.name == 'Text Channels':
                category = cat
                break
        pocbot_channel = await guild.create_text_channel(name='PocBot Controller', category=category)
        Setting.set_channelID(guildID, pocbot_channel.id)
        return pocbot_channel
    except Exception as e:
        error_log('create_bot_channel', e)
        return 'error'

async def command_check(ctx:commands.context.Context):
    guildID = ctx.guild.id
    content = ctx.message.content
    guildPrefix = Setting.get_guildPrefix(guildID)
    prefix = content[:len(guildPrefix)]
    return prefix.lower() == guildPrefix.lower()

# Allows if user is in the same channel as bot
# or if user is in voice channel and bot is not
async def valid_play_command_ctx(data:Guild_Music_Properties, user, channel, voice_client):
    guildName = channel.guild.name
    guildID   = channel.guild.id
    data.initialize(guildID)
    if user.voice is None:
        authorized = False
        msg = embed.user_disconnected_prompt()
    elif voice_client is None or not voice_client.is_connected():
        authorized = True
    elif user.voice.channel.id == voice_client.channel.id:
        authorized = True
    else:
        authorized = False
        msg = embed.invalid_channel_prompt(voice_client.channel)

    if not authorized:
        log(guildName, 'ACCESS DENIED', user)
        await channel.send(embed= msg, delete_after=Setting.get_promptDelay())
    else:
        log(guildName, 'ACCESS GRANTED', user)
        data.set_channel(guildID, channel)
    return authorized

# Allows if user is in the same channel as bot
async def valid_command_ctx(data, user, channel, voice_client):
    guildName = channel.guild.name
    guildID   = channel.guild.id
    data.initialize(guildID)
    if user.voice is None:
        authorized = False
        msg = embed.user_disconnected_prompt()
    elif voice_client is None:
        authorized = False
        msg = embed.bot_disconnected_prompt()
    elif not voice_client.is_connected():
        authorized = False
        msg = embed.bot_disconnected_prompt()
    elif voice_client.channel.id == user.voice.channel.id:
        authorized =  True
    else: 
        msg = embed.invalid_channel_prompt(voice_client.channel)
        authorized =  False
    if authorized is False:
        log(guildName, 'ACCESS DENIED', user)
        await channel.send(embed= msg, delete_after=Setting.get_promptDelay())
    else: 
        log(guildName, 'ACCESS GRANTED', user) 
        data.set_channel(guildID, channel)
    return authorized

async def voice_connect(user, guildName, guildID, voice_client):
    if voice_client is None:
        voice_client = await user.voice.channel.connect(reconnect=True)
        log(guildName, 'Voice Connected', voice_client.channel.name)
    else:
        if voice_client.is_connected() is False:
            await voice_client.move_to(user.voice.channel)
            log(guildName, 'Voice Reconnected', voice_client.channel.name)
    return voice_client

async def printHelpPrompt(channel, bot, guildID):
    await channel.send(embed= embed.quickInfoPrompt(bot,guildID))
    await channel.send(embed= embed.all_commands_prompt(bot,guildID))

def add_random_song(data, guildID):
    flac_song_list = os.listdir(LOCAL_MUSIC_PATH)
    song = random.choice(flac_song_list)
    path = LOCAL_MUSIC_PATH + '\\'+ song
    song_metadata = TinyTag.get(path)
    title = song_metadata.title
    author = song_metadata.artist
    song = {
        'title' : title, 
        'author':author, 
        'url'   : f'{LOCAL_MUSIC_PATH}\\{song}',
        'source': 'local'}
    data.add_song(guildID, song)

def queuePlaylist(guildName, guildID, playlist, playlistType:str, data:Guild_Music_Properties):
        playlistType = playlistType.lower()
        song_names_list = []
        name_list = ''
        last_ind = None
        for ind, song in enumerate(playlist):
            data.add_song(guildID,song)
            title = song['title']
            author = song['author']
            last_ind = ind+1
            row = embed.title(f"{last_ind}. {title} - {author}")
            if len(name_list) + len(row) < 1000:
                name_list += row+'\n'
            else:
                song_names_list.append(name_list)
                name_list = row+'\n'
        song_names_list.append(name_list)
        log(guildName, "QUEUED", f"{len(playlist)} songs ({playlistType})")
        return song_names_list



class MusicFunctions(View):
    def __init__(self, music_cog, data:Guild_Music_Properties, guildID):
        super().__init__(timeout=None)
        self.add_item(self.PreviousButton  (music_cog, data, guildID))
        self.add_item(self.PlayPause       (music_cog, data, guildID))
        self.add_item(self.SkipButton      (music_cog, data, guildID))
        self.add_item(self.ShuffleButton   (music_cog, data, guildID))
        self.add_item(self.LoopButton      (music_cog, data, guildID))
        self.add_item(self.RandomButton    (music_cog, data, guildID))
        self.add_item(self.FlushButton     (music_cog, data, guildID))
        self.add_item(self.ResetButton     (music_cog, data, guildID))
        self.add_item(self.HelpButton      (music_cog, data, guildID))

    async def interaction_check(self, interaction: discord.Interaction):
        user = interaction.user
        guildName = interaction.user.guild.name
        guildID = interaction.user.guild.id
        voice_client = interaction.client.get_guild(guildID).voice_client
        access = False
        if user.voice is None:
            access = False
            msg = embed.user_disconnected_prompt()
        elif voice_client is None:
            access = True
        elif voice_client.channel.id == user.voice.channel.id:
            access = True
        else:
            access = False
            msg = embed.invalid_channel_prompt(voice_client.channel)
        if access is True:
            log(guildName, 'ACCESS GRANTED', user) 
            return True
        else:
            log(guildName, 'ACCESS DENIED', user)
            await interaction.response.send_message(embed=msg, delete_after=Setting.get_promptDelay())
            return False

    class PlayPause(Button):
        def __init__(self,music_cog, data:Guild_Music_Properties, guildID):
            voice_client = music_cog.bot.get_guild(guildID).voice_client
            style = None
            if voice_client is None:
                style= discord.ButtonStyle.grey
            elif voice_client.is_playing() and not voice_client.is_paused():
                style= discord.ButtonStyle.blurple
            else:
                style= discord.ButtonStyle.grey
            super().__init__(emoji = '⏯', style= style)
            self.data = data
            self.music_cog = music_cog
        async def callback(self, interaction: discord.Interaction):
            guildName = interaction.user.guild.name
            guildID = interaction.user.guild.id
            voice_client = interaction.client.get_guild(guildID).voice_client
            channel = interaction.channel
            log(guildName, 'BUTTON', 'play/pause')
            try:
                song = self.data.get_current(guildID)
                if voice_client is None:
                    self.style = discord.ButtonStyle.grey
                elif voice_client.is_playing() and not voice_client.is_paused():
                    song_name = f'{song['title']} by {song['author']}'
                    log(guildName, 'PAUSED',song_name)
                    self.style = discord.ButtonStyle.grey
                    voice_client.pause()
                elif not voice_client.is_playing() and voice_client.is_paused():
                    song_name = f'{song['title']} by {song['author']}'
                    log(guildName, 'RESUMED',song_name)
                    self.style = discord.ButtonStyle.blurple
                    voice_client.resume()
                await interaction.response.edit_message(view=self.view)
            except Exception as e:
                error_log('PlayPause', e, guildName= guildName)

    class SkipButton(Button):
        def __init__(self,music_cog, data:Guild_Music_Properties, guildID):
            style = None
            if data.empty_queue(guildID) is True:
                style= discord.ButtonStyle.grey
            else:style=discord.ButtonStyle.blurple
            super().__init__(emoji = "⏭", style= style)
            self.data = data
            self.music_cog = music_cog

        async def callback(self, interaction: discord.Interaction):
            guildName = interaction.user.guild.name
            guildID = interaction.user.guild.id
            channel = interaction.channel
            voice_client = interaction.client.get_guild(guildID).voice_client
            log(guildName, 'button', 'skip')
            self.data.initialize(guildID)
            try:
                self.data.set_loop(guildID, False)
                song= self.data.get_current(guildID)
                if song is None:
                    await interaction.response.edit_message(view=self.view)
                    await interaction.followup.send(embed= embed.no_songs_prompt())
                    await GUI_HANDLER(self.music_cog, guildID, channel)
                    return
                self.data.pos_forward(guildID)
                await interaction.response.edit_message(view=self.view)
                await GUI_HANDLER(self.music_cog, guildID, channel)
                if (voice_client.is_playing() or voice_client.is_paused()):
                    voice_client.stop()
                    return
            except Exception as e:
                error_log('SkipButton', e, guildName= guildName)
            
    class PreviousButton(Button):
        def __init__(self,music_cog, data:Guild_Music_Properties, guildID):
            style = None
            if data.get_prev_song(guildID) is None:
                style= discord.ButtonStyle.grey
            else:style=discord.ButtonStyle.blurple
            super().__init__(emoji = "⏮", style= style)
            self.data = data
            self.music_cog = music_cog

        async def callback(self, interaction: discord.Interaction):
            user = interaction.user
            guildName = interaction.user.guild.name
            guildID = interaction.user.guild.id
            voice_client = interaction.client.get_guild(guildID).voice_client
            channel = interaction.channel
            log(guildName, 'button', 'previous')
            self.data.initialize(guildID)
            try:
                self.data.pos_backward(guildID)
                song= self.data.get_current(guildID) 
                if song is None:
                    await interaction.response.send_message(embed= embed.no_songs_prompt())
                    await GUI_HANDLER(self, guildID, channel)
                    return
                self.data.set_loop(guildID, False)
                await interaction.response.defer()
                await GUI_HANDLER(self.music_cog, guildID, channel)
                if voice_client.is_playing() or voice_client.is_paused():
                    voice_client.stop()
                    return
                await self.music_cog.music_player_start(user, guildName, guildID, voice_client, channel)
            except Exception as e:
                error_log('PreviousButton', e, guildName= guildName)
    
    class ShuffleButton(Button):
        def __init__(self,music_cog, data:Guild_Music_Properties, guildID):
            voice_client = music_cog.bot.get_guild(guildID).voice_client
            style = None
            if voice_client is None:
                style= discord.ButtonStyle.grey
            else:style=discord.ButtonStyle.blurple
            super().__init__(emoji = "🔀", style= style)
            self.data = data
            self.music_cog = music_cog

        async def callback(self, interaction: discord.Interaction):
            user = interaction.user
            guildName = interaction.user.guild.name
            guildID = interaction.user.guild.id
            voice_client = interaction.client.get_guild(guildID).voice_client
            channel = interaction.channel
            log(guildName, 'button', 'shuffle')
            self.data.initialize(guildID)
            try:
                current_song = self.data.get_current(guildID)
                library = self.data.get_queue(guildID)+self.data.get_history(guildID)
                if library == [] and current_song is None:
                    await interaction.response.send_message(embed= embed.no_songs_prompt(), delete_after=Setting.get_promptDelay())
                    return
                random.shuffle(library)
                if current_song is not None:
                    library.insert(0, current_song)
                self.data.set_new_library(guildID, library)
                await interaction.response.send_message(embed= embed.shuffle_prompt(), delete_after=Setting.get_promptDelay())
                await GUI_HANDLER(self.music_cog, guildID, None)
                await self.music_cog.music_player_start(user, guildName, guildID, voice_client, channel)
            except Exception as e:
                error_log('ShuffleButton', e, guildName= guildName)
            
    class LoopButton(Button):
        def __init__(self,music_cog, data:Guild_Music_Properties, guildID):
            if data.get_loop(guildID) is True:
                style= discord.ButtonStyle.blurple
            else:
                style= discord.ButtonStyle.grey
            super().__init__(emoji = "🔄", style=style)
            self.music_cog = music_cog
            self.data = data
        async def callback(self, interaction: discord.Interaction):
            guildName = interaction.user.guild.name
            guildID = interaction.user.guild.id
            channel = interaction.channel
            log(guildName, 'button', 'loop')
            self.data.initialize(guildID)
            voice_client = interaction.client.get_guild(guildID).voice_client
            try:
                if voice_client is None:
                    await interaction.response.defer()
                    return
                if voice_client.is_playing() or voice_client.is_paused():
                    song = self.data.get_current(guildID)
                    self.data.switch_loop(guildID)
                    self.data.set_random(guildID, False)
                    loop_var = self.data.get_loop(guildID)
                    if loop_var is True:
                        log(guildName, 'now looping', song)
                    else:
                        log(guildName, 'stopped looping', song)
                    await interaction.response.edit_message(view=self.view)
                    loop_var = self.data.get_loop(guildID)
                    song= self.data.get_current(guildID) 
                    await interaction.channel.send(embed= embed.loop_prompt(loop_var, song), delete_after=Setting.get_promptDelay())
                    await GUI_HANDLER(self.music_cog, guildID, None)
                    return
                await interaction.response.defer()
            except Exception as e:
                error_log('LoopButton', e, guildName= guildName)
    
    class RandomButton(Button):
        def __init__(self, music_cog, data:Guild_Music_Properties, guildID):
            if data.get_random(guildID) == True:
                style= discord.ButtonStyle.blurple
            else:
                style= discord.ButtonStyle.grey
            super().__init__(emoji='♾', label='Random', style= style)
            self.data = data
            self.music_cog = music_cog

        async def callback(self, interaction: discord.Interaction):
            user = interaction.user
            guildName = interaction.user.guild.name
            guildID = interaction.user.guild.id
            voice_client = interaction.client.get_guild(guildID).voice_client
            channel = interaction.channel
            log(guildName, 'button', 'play_random')
            self.data.initialize(guildID)
            try:
                if self.data.switch_random(guildID) is True:
                    log(guildName, 'RANDOM', 'On')
                else: 
                    log(guildName, 'RANDOM', 'Off')
                await interaction.followup.send(embed= embed.random_prompt(self.data.get_random(guildID)), delete_after=Setting.get_promptDelay())
                await self.music_cog.music_player_start(user, guildName, guildID, voice_client, channel)
                await GUI_HANDLER(self.music_cog, guildID, None)
            except Exception as e:
                error_log('RandomButton', e, guildName= guildName)
            
    class FlushButton(Button):
        def __init__(self,music_cog, data:Guild_Music_Properties, guildID):
            voice_client = music_cog.bot.get_guild(guildID).voice_client
            style = None
            if voice_client is None:
                style= discord.ButtonStyle.grey
            else:style=discord.ButtonStyle.blurple
            super().__init__(emoji='🚽',label = 'Flush', style=style)
            self.music_cog = music_cog
            self.data = data
        async def callback(self, interaction: discord.Interaction):
            guildName = interaction.user.guild.name
            guildID = interaction.user.guild.id
            channel = interaction.channel
            voice_client = interaction.client.get_guild(guildID).voice_client
            log(guildName, 'button', 'flush')
            self.data.initialize(guildID)
            try:
                self.data.reset(guildID)
                if voice_client.is_playing() or voice_client.is_paused():
                    voice_client.stop()
                self.data.full_reset(guildID)
                await interaction.response.send_message(embed= embed.flush_prompt(), delete_after=Setting.get_promptDelay())
                await GUI_HANDLER(self.music_cog, guildID, None)
            except Exception as e:
                error_log('flushbutton', e, guildName= guildName)
    
    class ResetButton(Button):
        def __init__(self,music_cog, data:Guild_Music_Properties, guildID):
            voice_client = music_cog.bot.get_guild(guildID).voice_client
            style = None
            if voice_client is None:
                style= discord.ButtonStyle.grey
            else:style=discord.ButtonStyle.red
            super().__init__(label = 'Reset', style=style)
            self.music_cog = music_cog
            self.data = data
        async def callback(self, interaction: discord.Interaction):
            guildName = interaction.user.guild.name
            guildID = interaction.user.guild.id
            channel = interaction.channel
            voice_client = interaction.client.get_guild(guildID).voice_client
            log(guildName, 'button', 'reset')
            self.data.initialize(guildID)
            try:
                self.data.full_reset(guildID)
                if voice_client is not None:
                    channel_name = voice_client.channel.name
                    if voice_client.is_playing() or voice_client.is_paused():
                        voice_client.stop()
                    await voice_client.disconnect()
                    log(guildName, 'DISCONNECTED (force)', channel_name)
                await interaction.response.send_message(embed= embed.reset_prompt(), delete_after=Setting.get_promptDelay())
            except Exception as e:
                error_log('resetbutton', e, guildName= guildName)

    class HelpButton(Button):
        def __init__(self,music_cog, data:Guild_Music_Properties, guildID):
            super().__init__(emoji = 'ℹ', style=discord.ButtonStyle.blurple)
            self.music_cog = music_cog
            self.data = data
        async def callback(self, interaction: discord.Interaction):
            guildName = interaction.user.guild.name
            guildID = interaction.user.guild.id
            channel = interaction.channel
            log(guildName, 'command', 'HelpButton')
            self.data.initialize(guildID)
            try:
                await printHelpPrompt(channel, self.music_cog.bot, guildID)
                await asyncio.sleep(Setting.get_helpPromptDelay())
                await GUI_HANDLER(self.music_cog, guildID, channel)
            except Exception as e:
                error_log('HelpButton', e, guildName= guildName)
            



class SearchAlgorithmView(discord.ui.View):

    def __init__(self, music_cog, user):
        super().__init__()
        self.add_item(SearchAlgorithmSelect(music_cog, user, self))
        self.user = user
    async def interaction_check(self, interaction: discord.Interaction):
        clicked_user = interaction.user
        guildName = interaction.user.guild.name
        access = False
        if self.user.id == clicked_user.id:
            access = True
        if access is True:
            log(guildName, 'ACCESS GRANTED', clicked_user) 
            return True
        else:
            log(guildName, 'ACCESS DENIED', clicked_user)
            msg = embed.unauthorized_user_prompt()
            await interaction.response.send_message(embed=msg, ephemeral=True, delete_after=Setting.get_promptDelay())
            return False
class SearchAlgorithmSelect(discord.ui.Select):
    def __init__(self, music_cog, user, view):
        self.music_cog = music_cog
        self.superview = view
        self.user = user
        currentAlgo = Setting.get_searchAlgorithm(user.guild.id)
        if currentAlgo == 'spotify':
            spotify = discord.SelectOption(label='Spotify', description="Choose spotify search algorithm",default=True)
            youtube = discord.SelectOption(label='Youtube', description="Choose youtube search algorithm")
        else:
            spotify = discord.SelectOption(label='Spotify', description="Choose spotify search algorithm")
            youtube = discord.SelectOption(label='Youtube', description="Choose youtube search algorithm",default=True)
        options = [
            spotify,
            youtube
        ]
        super().__init__(placeholder="Choose a Search Algorithm", min_values=1, max_values=1, options=options)
    
    async def callback(self, interaction: discord.Interaction):
        try:
            guildID = interaction.user.guild.id
            selected_option = str(self.values[0]).lower()
            Setting.set_searchAlgorithm(guildID, selected_option)
            searchalgo = Setting.get_searchAlgorithm(guildID)
            log('SearchAlgorithmselect','set search algorithm', searchalgo)
            await interaction.response.edit_message(embed=embed.search_algorithm_prompt(searchalgo), view=None)
        except Exception as e:
            error_log('SearchAlgorithmSelect',e)