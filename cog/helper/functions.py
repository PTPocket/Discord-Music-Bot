import discord
import os
import random
import time

from tinytag              import TinyTag
from cog.helper           import embed
from cog.helper.GuildData import Guild_Music_Properties
from discord.ui           import View, Select, Button
from cog.helper.GuildData import Guild_Music_Properties
from cog.helper.Log       import *
from cog.helper           import Setting


BLANK = '\u200b'
LOCAL_MUSIC_PATH = "C:\\Users\\p\\Documents\\SERVER\\music\\Formatted"

async def GUI_HANDLER(Music_Cog, guildID, edit):
    try:
        guildName = Music_Cog.bot.get_guild(guildID).name
        player_embed = embed.MainGuiPrompt(Music_Cog.bot, Music_Cog.data, guildID)
        try:
            view = MusicFunctions(Music_Cog, Music_Cog.data, guildID)
        except Exception as e:
            error_log('MusicFunctions', e)
            return
        channel = Music_Cog.data.get_channel(guildID)
        last_message = Music_Cog.data.get_message(guildID)
        if last_message is None:
            message = await channel.send(embed = player_embed, view = view)
            Music_Cog.data.set_message(guildID, message)
            return
        if edit is True:
            message = await last_message.edit(embed = player_embed, view = view)
            return
        message = await channel.send(embed = player_embed, view = view)
        await last_message.delete()
        Music_Cog.data.set_message(guildID, message)
    except Exception as e:
        error_log('Gui_handler', e, guildName= guildName)

# Allows if user is in the same channel as bot
# or if user is in voice channel and bot is not
async def valid_play_command_slash(interaction:discord.Interaction):
    user = interaction.user
    guildName = interaction.user.guild.name
    guildID = interaction.user.guild.id

    voice_client = interaction.client.get_guild(guildID).voice_client
    authorized = None
    if user.voice is None:
        authorized = False
    elif voice_client is None or not voice_client.is_connected():
        authorized = True
    elif user.voice.channel.id == voice_client.channel.id:
        authorized = True
    else:
        authorized = False

    if not authorized:
        log(guildName, 'ACCESS DENIED', user)
        msg = embed.unauthorized_prompt(interaction.client)
        await interaction.response.send_message(embed= msg, ephemeral=True, delete_after=Setting.get_promptDelay())
        time.sleep(Setting.get_promptDelay())
    else:
        log(guildName, 'ACCESS GRANTED', user)
    return authorized

# Allows if user is in the same channel as bot
async def valid_command_slash(interaction:discord.Interaction):
    user = interaction.user
    guildName = interaction.user.guild.name
    guildID = interaction.user.guild.id
    authorized = None
    voice_client = interaction.client.get_guild(guildID).voice_client

    if user.voice is None or \
    voice_client is None or \
    not voice_client.is_connected():
        authorized = False
    elif voice_client.channel.id == user.voice.channel.id:
        authorized =  True
    else: 
        authorized =  False

    if authorized is False:
        log(guildName, 'ACCESS DENIED', user)
        msg = embed.unauthorized_prompt(interaction.client)
        await interaction.response.send_message(embed= msg, ephemeral=True, delete_after=Setting.get_promptDelay())
        time.sleep(Setting.get_promptDelay())
    else: log(guildName, 'ACCESS GRANTED', user) 
    return authorized

# Allows if user is in the same channel as bot
# or if user is in voice channel and bot is not
async def valid_play_command_ctx(bot, ctx):
    user = ctx.author
    guildName = str(ctx.guild)
    guildID = ctx.guild.id

    voice_client = bot.get_guild(guildID).voice_client
    authorized = None
    if user.voice is None:
        authorized = False
    elif voice_client is None or not voice_client.is_connected():
        authorized = True
    elif user.voice.channel.id == voice_client.channel.id:
        authorized = True
    else:
        authorized = False

    if not authorized:
        log(guildName, 'ACCESS DENIED', user)
        msg = embed.unauthorized_prompt(bot)
        await ctx.send(embed= msg, ephemeral=True, delete_after=Setting.get_promptDelay())
        time.sleep(Setting.get_promptDelay())
    else:
        log(guildName, 'ACCESS GRANTED', user)
    return authorized

# Allows if user is in the same channel as bot
async def valid_command_ctx(bot, ctx):
    user = ctx.author
    guildName = str(ctx.guild)
    guildID = ctx.guild.id
    voice_client = bot.get_guild(guildID).voice_client
    if user.voice is None or \
    voice_client is None or \
    not voice_client.is_connected():
        authorized = False
    elif voice_client.channel.id == user.voice.channel.id:
        authorized =  True
    else: 
        authorized =  False
    if authorized is False:
        log(guildName, 'ACCESS DENIED', user)
        msg = embed.unauthorized_prompt(bot)
        await ctx.send(embed= msg, ephemeral=True, delete_after=Setting.get_promptDelay())
        time.sleep(Setting.get_promptDelay())
    else: log(guildName, 'ACCESS GRANTED', user) 
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
            row = embed.title(f"{last_ind}. {title} by {author}")
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
        self.add_item(self.ResetButton(music_cog, data, guildID))
        
    async def interaction_check(self, interaction: discord.Interaction):
        user = interaction.user
        guildName = interaction.user.guild.name
        guildID = interaction.user.guild.id
        voice_client = interaction.client.get_guild(guildID).voice_client
        access = False
        if user.voice is None:
            access = False
        elif voice_client is None:
            access = True
        elif voice_client.channel.id == user.voice.channel.id:
            access = True
        
        if access is True:
            log(guildName, 'ACCESS GRANTED', user) 
            return True
        else:
            log(guildName, 'ACCESS DENIED', user)
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
        async def callback(self, interaction: discord.Interaction):
            try:
                guildName = interaction.user.guild.name
                guildID = interaction.user.guild.id
                voice_client = interaction.client.get_guild(guildID).voice_client
                log(guildName, 'BUTTON', 'play/pause')
                song = self.data.get_current(guildID)
                if voice_client is None:
                    self.style = discord.ButtonStyle.grey
                elif voice_client.is_playing() and not voice_client.is_paused():
                    song_name = f'{song['title']} by {song['author']}'
                    log(guildName, 'PAUSED',song_name)
                    voice_client.pause()
                    self.style = discord.ButtonStyle.grey
                elif not voice_client.is_playing() and voice_client.is_paused():
                    song_name = f'{song['title']} by {song['author']}'
                    log(guildName, 'RESUMED',song_name)
                    self.style = discord.ButtonStyle.blurple
                    voice_client.resume()
                await interaction.response.edit_message(view=self.view)
            except Exception as e:
                error_log('PlayPause', e, guildName= guildName)
            
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
            try:
                user = interaction.user
                guildName = interaction.user.guild.name
                guildID = interaction.user.guild.id
                voice_client = interaction.client.get_guild(guildID).voice_client
                channel = interaction.channel
                log(guildName, 'button', 'play_random')
                self.data.initialize(guildID)
                if self.data.switch_random(guildID) is True:
                    log(guildName, 'RANDOM', 'On')
                else: 
                    log(guildName, 'RANDOM', 'Off')
                await interaction.response.send_message(embed= embed.random_prompt(interaction.client, self.data.get_random(guildID)), delete_after=Setting.get_promptDelay())
                await self.music_cog.music_player_start(user, guildName, guildID, voice_client, channel)
                await GUI_HANDLER(self.music_cog, guildID, edit=True)
            except Exception as e:
                error_log('RandomButton', e, guildName= guildName)
            
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
            try:
                user = interaction.user
                guildName = interaction.user.guild.name
                guildID = interaction.user.guild.id
                voice_client = interaction.client.get_guild(guildID).voice_client
                channel = interaction.channel
                print(guildName, guildID)
                log(guildName, 'button', 'previous')
                self.data.initialize(guildID)
                self.data.pos_backward(guildID)
                self.data.set_loop(guildID, False)
                song= self.data.get_current(guildID) 
                song_name = f'{song['title']} by {song['author']}'
                if voice_client.is_playing() or voice_client.is_paused():
                    voice_client.stop()
                    await interaction.response.edit_message(view=self.view)
                    await GUI_HANDLER(self.music_cog, guildID, edit=True)
                    return
                await interaction.response.edit_message(view=self.view)
                await self.music_cog.music_player_start(user, guildName, guildID, voice_client, channel)
                await GUI_HANDLER(self.music_cog, guildID, edit=True)
            except Exception as e:
                error_log('PreviousButton', e, guildName= guildName)
    
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
            try:
                guildName = interaction.user.guild.name
                guildID = interaction.user.guild.id
                voice_client = interaction.client.get_guild(guildID).voice_client
                log(guildName, 'button', 'skip')
                self.data.initialize(guildID)
                self.data.set_loop(guildID, False)
                song= self.data.get_current(guildID)
                self.data.pos_forward(guildID)
                if song is None:
                    await interaction.response.edit_message(view=self.view)
                    return
                song_name = f'{song['title']} by {song['author']}'
                if (voice_client.is_playing() or voice_client.is_paused()):
                    voice_client.stop()
                    await interaction.response.edit_message(view=self.view)
                    await GUI_HANDLER(self.music_cog, guildID, edit=True)
                    return
                await interaction.response.edit_message(view=self.view)
                await GUI_HANDLER(self.music_cog, guildID, edit = True)
            except Exception as e:
                error_log('SkipButton', e, guildName= guildName)
                
    
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
            try:
                user = interaction.user
                guildName = interaction.user.guild.name
                guildID = interaction.user.guild.id
                voice_client = interaction.client.get_guild(guildID).voice_client
                channel = interaction.channel
                log(guildName, 'button', 'shuffle')
                self.data.initialize(guildID)
                current_song = self.data.get_current(guildID)
                library = self.data.get_queue(guildID)+self.data.get_history(guildID)
                if library == [] and current_song is None:
                    await interaction.response.send_message(embed= embed.nothing_prompt('shuffle'), delete_after=Setting.get_promptDelay())
                    await GUI_HANDLER(self.music_cog, guildID, edit=True)
                    return
                random.shuffle(library)
                if current_song is not None:
                    library.insert(0, current_song)
                self.data.set_new_library(guildID, library)
                await interaction.response.send_message(embed= embed.shuffle_prompt(interaction.client), delete_after=Setting.get_promptDelay())
                await self.music_cog.music_player_start(user, guildName, guildID, voice_client, channel)
                await GUI_HANDLER(self.music_cog, guildID, edit=True)
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
            try:
                guildName = interaction.user.guild.name
                guildID = interaction.user.guild.id
                log(guildName, 'button', 'loop')
                self.data.initialize(guildID)
                voice_client = interaction.client.get_guild(guildID).voice_client
                if voice_client.is_playing() or voice_client.is_paused():
                    song = self.data.get_current(guildID)
                    self.data.switch_loop(guildID)
                    self.data.set_random(guildID, False)
                    loop_var = self.data.get_loop(guildID)
                    if loop_var is True:
                        log(guildName, 'now looping', f'{song['title']} by {song['author']}')
                    else:
                        log(guildName, 'stopped looping', f'{song['title']} by {song['author']}')
                    await interaction.response.edit_message(view=self.view)
                    loop_var = self.data.get_loop(guildID)
                    song= self.data.get_current(guildID) 
                    song_name = f'{song['title']} by {song['author']}'
                    await interaction.channel.send(embed= embed.loop_prompt(interaction.client, loop_var, song_name), delete_after=Setting.get_promptDelay())
                    await GUI_HANDLER(self.music_cog, guildID, edit=True)
                    return
                await interaction.response.edit_message(view=self.view)
            except Exception as e:
                error_log('LoopButton', e, guildName= guildName)
    
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
            try:
                guildName = interaction.user.guild.name
                guildID = interaction.user.guild.id
                voice_client = interaction.client.get_guild(guildID).voice_client
                log(guildName, 'button', 'flush')
                self.data.initialize(guildID)
                self.data.reset(guildID)
                if voice_client.is_playing() or voice_client.is_paused():
                    voice_client.stop()
                self.data.full_reset(guildID)
                await interaction.response.send_message(embed= embed.flush_prompt(interaction.client), delete_after=Setting.get_promptDelay())
                await GUI_HANDLER(self.music_cog, guildID, edit=True)
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
            try:
                guildName = interaction.user.guild.name
                guildID = interaction.user.guild.id
                voice_client = interaction.client.get_guild(guildID).voice_client
                log(guildName, 'button', 'reset')
                self.data.initialize(guildID)
                self.data.full_reset(guildID)
                if voice_client is not None:
                    channel_name = voice_client.channel.name
                    if voice_client.is_playing() or voice_client.is_paused():
                        voice_client.stop()
                    await voice_client.disconnect()
                    log(guildName, 'DISCONNECTED (force)', channel_name)
                await interaction.response.send_message(embed= embed.reset_prompt(interaction.client), delete_after=Setting.get_promptDelay())
                await GUI_HANDLER(self.music_cog, guildID, edit=True)
            except Exception as e:
                error_log('resetbutton', e, guildName= guildName)




                