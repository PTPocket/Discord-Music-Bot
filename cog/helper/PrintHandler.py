import random
import asyncio
import discord
from discord.ui             import View, Select, Button
from discord.ext            import commands
import cog.helper.setting   as     Setting
from cog.helper.embed       import Embeds
from cog.helper.guildData   import GuildData
from cog.helper.log         import *

BUTTON_DELAY = 4

class PrintHandler():
    def __init__(self, Music_Cog, bot:commands.Bot, dataObj:GuildData, embObj:Embeds):
        self.Music_Cog = Music_Cog
        self.dataObj = dataObj
        self.embObj  = embObj
        self.bot = bot


    #gui_handler(None, guildID) will Edit
    #gui_handler(channel) will reprint
    async def GUI_HANDLER(self, channel, guildID = None):
        if guildID is None:
            guildID = channel.guild.id 
            guildName = channel.guild.name
        else:
            guild = self.bot.get_guild(guildID)
            guildName = guild.name
        self.dataObj.set_guiLimit(guildID, False)
        async with self.dataObj.get_guiLock(guildID):
            if self.dataObj.get_guiLimit(guildID) is True:
                return
            channelID = Setting.get_channelID(guildID)
            if channelID is None: return
            pocbot_channel = self.bot.get_channel(channelID)
            if pocbot_channel is None: return
            player_embed = self.embObj.MainGuiPrompt(guildID)
            view = MusicFunctions(self.Music_Cog, self.bot, self.dataObj, self.embObj, self, guildID)
            self.dataObj.set_guiLimit(guildID, True)
            messageID = Setting.get_messageID(guildID)
            try:
                if messageID is None:
                    message = await pocbot_channel.send(embed = player_embed, view = view)
                    Setting.set_messageID(guildID, message.id)
                    log(guildName, 'GUIPrint New')
                    return
                try: message = await pocbot_channel.fetch_message(messageID)
                except: message = None
                if message is None:
                    message = await pocbot_channel.send(embed = player_embed, view = view)
                    Setting.set_messageID(guildID, message.id)
                    log(guildName, 'GUIPrint New')
                    return
                try:
                    if channel is None or channelID != channel.id:
                        await message.edit(embed = player_embed, view = view)
                        log(guildName, 'GUIPrint Edit')
                        return
                except Exception as e: 
                    error_log('GUI_HANDLER', e, guildName=guildName)
                    log(guildName, 'GUI_HANDLER', 'sending new message')
                new_message = await pocbot_channel.send(embed = player_embed, view = view)
                Setting.set_messageID(guildID, new_message.id)
                log(guildName, 'GUIPrint Replace')
                await message.delete()
            except Exception as e:
                error_log('Gui_handler', e, guildName= guildName)

    async def nowPlayingHandler(self, guildID):
        if type(guildID) is str:
            emb = self.embObj.finished_prompt()
        else: 
            emb = self.embObj.now_playing_prompt(self.dataObj.get_current(guildID))
        guildID = int(guildID)
        command_channel = self.dataObj.get_channel(guildID)
        pocbot_channelID = Setting.get_channelID(guildID)
        if command_channel.id == pocbot_channelID:
            return
        last_channelID, last_messageID = Setting.get_nowPlayingMessage(guildID)
        async with self.dataObj.get_nowplayingLock(int(guildID)):
            try:
                message = await command_channel.send(embed=emb)
                Setting.set_nowPlayingMessage(guildID, message.channel.id, message.id)
                if last_channelID is not None:
                    last_channel = self.bot.get_channel(last_channelID)
                    last_message = await last_channel.fetch_message(last_messageID)
                    await last_message.delete()
            except Exception as e:
                error_log('nowPlayingHandler', e)
                pass

    async def printHelpPrompt(self, channel, permanent= False):
        guildID = channel.guild.id
        if permanent:
            await channel.send(embed= self.embObj.quickInfoPrompt(guildID))
            await channel.send(embed= self.embObj.all_commands_prompt(guildID))
            return
        await channel.send(embed= self.embObj.quickInfoPrompt(guildID), delete_after=Setting.get_promptDelay()*2)
        await channel.send(embed= self.embObj.all_commands_prompt(guildID), delete_after=Setting.get_promptDelay()*2)



async def validate_command(interaction: discord.Interaction, dataObj: GuildData, embObj:Embeds):

    guildName = interaction.guild.name
    guildID   = interaction.guild.id
    user = interaction.user
    channel = interaction.channel
    voice_client = interaction.client.get_guild(guildID).voice_client
    dataObj.initialize(guildID)
    
    if user.voice is None:
        authorized = False
        msg = embObj.user_disconnected_prompt()
    elif voice_client is None:
        authorized = False
        msg = embObj.bot_disconnected_prompt()
    elif not voice_client.is_connected():
        authorized = False
        msg = embObj.bot_disconnected_prompt()
    elif voice_client.channel.id == user.voice.channel.id:
        authorized =  True
    else: 
        msg = embObj.invalid_channel_prompt(voice_client.channel)
        authorized =  False
    if authorized is False:
        log(guildName, 'ACCESS DENIED', user)
        await interaction.response.send_message(embed= msg, delete_after=BUTTON_DELAY)
    else: 
        log(guildName, 'ACCESS GRANTED', user) 
        dataObj.set_channel(guildID, channel)
    return authorized

async def validate_play_commands(interaction: discord.Interaction, dataObj: GuildData, embObj:Embeds):
    guildName = interaction.guild.name
    guildID   = interaction.guild.id
    user = interaction.user
    channel = interaction.channel
    voice_client = interaction.client.get_guild(guildID).voice_client
    dataObj.initialize(guildID)
    if user.voice is None:
        authorized = False
        msg = embObj.user_disconnected_prompt()
    elif voice_client is None or not voice_client.is_connected():
        authorized = True
    elif user.voice.channel.id == voice_client.channel.id:
        authorized = True
    else:
        authorized = False
        msg = embObj.invalid_channel_prompt(voice_client.channel)
    if not authorized:
        log(guildName, 'ACCESS DENIED', user)
        await interaction.response.send_message(embed= msg, delete_after=BUTTON_DELAY)
    else:
        log(guildName, 'ACCESS GRANTED', user)
        dataObj.set_channel(guildID, channel)
    return authorized

class MusicFunctions(View):
    def __init__(self, music_cog, bot:commands.bot, dataObj:GuildData, embObj:Embeds, pHandler:PrintHandler,  guildID):
        super().__init__(timeout=None)
        self.music_cog = music_cog
        self.bot = bot
        self.dataObj = dataObj
        self.embObj = embObj
        self.pHandler = pHandler

        self.add_item(self.PreviousButton  (music_cog, bot, dataObj, embObj, pHandler, guildID))
        self.add_item(self.PlayPause       (music_cog, bot, dataObj, embObj, pHandler, guildID))
        self.add_item(self.SkipButton      (music_cog, bot, dataObj, embObj, pHandler, guildID))
        self.add_item(self.ShuffleButton   (music_cog, bot, dataObj, embObj, pHandler, guildID))
        self.add_item(self.LoopButton      (music_cog, bot, dataObj, embObj, pHandler, guildID))
        self.add_item(self.RandomButton    (music_cog, bot, dataObj, embObj, pHandler, guildID))
        self.add_item(self.FlushButton     (music_cog, bot, dataObj, embObj, pHandler, guildID))
        self.add_item(self.ResetButton     (music_cog, bot, dataObj, embObj, pHandler, guildID))
        self.add_item(self.HelpButton      (music_cog, bot, dataObj, embObj, pHandler, guildID))
    

    class PreviousButton(Button):
        def __init__(self, music_cog,bot:commands.bot, dataObj:GuildData, embObj:Embeds, pHandler:PrintHandler,  guildID):
            self.music_cog = music_cog
            self.bot = bot
            self.dataObj = dataObj
            self.embObj  = embObj
            self.pHandler = pHandler
            style = discord.ButtonStyle.blurple
            if dataObj.get_prev_song(guildID) is None:
                style= discord.ButtonStyle.grey

            super().__init__(emoji = "⏮", style= style)
        async def callback(self, interaction: discord.Interaction):
            if await validate_play_commands(interaction, self.dataObj, self.embObj) is False: return
            await interaction.response.edit_message(view = self.view)
            user = interaction.user
            guildName = interaction.user.guild.name
            guildID = interaction.user.guild.id
            voice_client = interaction.client.get_guild(guildID).voice_client
            channel = interaction.channel
            log(guildName, 'button', 'previous')
            try:
                self.dataObj.pos_backward(guildID)
                song= self.dataObj.get_current(guildID) 
                if song is None:
                    await self.pHandler.GUI_HANDLER(None, guildID)
                    return
                self.dataObj.set_loop(guildID, False)
                await self.pHandler.GUI_HANDLER(None, guildID)
                if voice_client.is_playing() or voice_client.is_paused():
                    voice_client.stop()
                    return
                await self.music_cog.music_player_start(user, guildName, guildID, voice_client)
            except Exception as e:
                error_log('PreviousButton', e, guildName= guildName)
    
    class ShuffleButton(Button):
        def __init__(self, music_cog, bot:commands.bot, dataObj:GuildData, embObj:Embeds, pHandler:PrintHandler,  guildID):
            self.music_cog = music_cog
            self.bot = bot
            self.dataObj = dataObj
            self.embObj  = embObj
            self.pHandler = pHandler
            voice_client = self.bot.get_guild(guildID).voice_client
            style = style=discord.ButtonStyle.blurple
            if voice_client is None:
                style= discord.ButtonStyle.grey
            super().__init__(emoji = "🔀", style= style)
        async def callback(self, interaction: discord.Interaction):
            if await validate_play_commands(interaction, self.dataObj, self.embObj) is False: return
            user = interaction.user
            guildName = interaction.user.guild.name
            guildID = interaction.user.guild.id
            voice_client = interaction.client.get_guild(guildID).voice_client
            channel = interaction.channel
            log(guildName, 'button', 'shuffle')
            
            try:
                current_song = self.dataObj.get_current(guildID)
                library = self.dataObj.get_queue(guildID)+self.dataObj.get_history(guildID)
                if library == [] and current_song is None:
                    await interaction.response.send_message(embed= self.embObj.no_songs_prompt(), delete_after=BUTTON_DELAY)
                    return
                random.shuffle(library)
                if current_song is not None:
                    library.insert(0, current_song)
                self.dataObj.set_new_library(guildID, library)
                await interaction.response.send_message(embed= self.embObj.shuffle_prompt(), delete_after=BUTTON_DELAY)
                await self.pHandler.GUI_HANDLER(None, guildID)
                await self.music_cog.music_player_start(user, guildName, guildID, voice_client)
            except Exception as e:
                error_log('ShuffleButton', e, guildName= guildName)
            
    class RandomButton(Button):
        def __init__(self, music_cog,bot:commands.bot, dataObj:GuildData, embObj:Embeds, pHandler:PrintHandler,  guildID):
            self.music_cog = music_cog
            self.bot = bot
            self.dataObj = dataObj
            self.embObj  = embObj
            self.pHandler = pHandler
            style = discord.ButtonStyle.grey
            if self.dataObj.get_random(guildID) is True:
                style= discord.ButtonStyle.blurple

            super().__init__(emoji='♾', label='Random', style= style)
        async def callback(self, interaction: discord.Interaction):
            if await validate_play_commands(interaction, self.dataObj, self.embObj) is False: return
            user = interaction.user
            guildName = interaction.user.guild.name
            guildID = interaction.user.guild.id
            voice_client = interaction.client.get_guild(guildID).voice_client
            channel = interaction.channel
            log(guildName, 'button', 'play_random')
            
            try:
                if self.dataObj.switch_random(guildID) is True:
                    log(guildName, 'RANDOM', 'On')
                    self.style = discord.ButtonStyle.blurple
                else: 
                    log(guildName, 'RANDOM', 'Off')
                    self.style = discord.ButtonStyle.grey
                await interaction.response.edit_message(view = self.view)
                await channel.send(embed= self.embObj.random_prompt(self.dataObj.get_random(guildID)), delete_after=BUTTON_DELAY)
                await self.music_cog.music_player_start(user, guildName, guildID, voice_client)
            except Exception as e:
                error_log('RandomButton', e, guildName= guildName)
            


    class PlayPause(Button):
        def __init__(self, music_cog,bot:commands.bot, dataObj:GuildData, embObj:Embeds, pHandler:PrintHandler,  guildID):
            self.music_cog = music_cog
            self.bot = bot
            self.dataObj = dataObj
            self.embObj  = embObj
            self.pHandler = pHandler
            voice_client = self.bot.get_guild(guildID).voice_client
            style = discord.ButtonStyle.grey
            if voice_client is None:
                style= discord.ButtonStyle.grey
            elif voice_client.is_playing() and not voice_client.is_paused():
                style= discord.ButtonStyle.blurple
            super().__init__(emoji = '⏯', style= style)
        async def callback(self, interaction: discord.Interaction):
            if await validate_command(interaction, self.dataObj, self.embObj) is False: return
            guildName = interaction.user.guild.name
            guildID = interaction.user.guild.id
            voice_client = interaction.client.get_guild(guildID).voice_client
            channel = interaction.channel
            log(guildName, 'BUTTON', 'play/pause')
            try:
                song = self.dataObj.get_current(guildID)
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
                await interaction.response.edit_message(view = self.view)
            except Exception as e:
                error_log('PlayPause', e, guildName= guildName)

    class SkipButton(Button):
        def __init__(self, music_cog,bot:commands.bot, dataObj:GuildData, embObj:Embeds, pHandler:PrintHandler,  guildID):
            self.music_cog = music_cog
            self.bot = bot
            self.dataObj = dataObj
            self.embObj  = embObj
            self.pHandler = pHandler
            style = discord.ButtonStyle.blurple
            if self.dataObj.empty_queue(guildID) is True:
                style= discord.ButtonStyle.grey
            super().__init__(emoji = "⏭", style= style)
        async def callback(self, interaction: discord.Interaction):
            if await validate_command(interaction, self.dataObj, self.embObj) is False: return
            await interaction.response.edit_message(view = self.view)
            guildName = interaction.user.guild.name
            guildID = interaction.user.guild.id
            channel = interaction.channel
            voice_client = interaction.client.get_guild(guildID).voice_client
            log(guildName, 'button', 'skip')
            try:
                self.dataObj.set_loop(guildID, False)
                song= self.dataObj.get_current(guildID)
                if song is None:
                    await self.pHandler.GUI_HANDLER(None, guildID)
                    await interaction.channel.send(embed= self.embObj.no_songs_prompt())
                    return
                self.dataObj.pos_forward(guildID)
                await self.pHandler.GUI_HANDLER(None, guildID)
                if (voice_client.is_playing() or voice_client.is_paused()):
                    voice_client.stop()
                    return
            except Exception as e:
                error_log('SkipButton', e, guildName= guildName)
    
    class LoopButton(Button):
        def __init__(self, music_cog,bot:commands.bot, dataObj:GuildData, embObj:Embeds, pHandler:PrintHandler,  guildID):
            self.music_cog = music_cog
            self.bot = bot
            self.dataObj = dataObj
            self.embObj  = embObj
            self.pHandler = pHandler
            style= discord.ButtonStyle.grey
            if self.dataObj.get_loop(guildID) is True:
                style= discord.ButtonStyle.blurple
            super().__init__(emoji = "🔄", style=style)
        async def callback(self, interaction: discord.Interaction):
            if await validate_command(interaction, self.dataObj, self.embObj) is False: return
            guildName = interaction.user.guild.name
            guildID = interaction.user.guild.id
            channel = interaction.channel
            log(guildName, 'button', 'loop')
            voice_client = interaction.client.get_guild(guildID).voice_client
            try:
                if voice_client is None:
                    await interaction.response.defer()
                    return
                if voice_client.is_playing() or voice_client.is_paused():
                    song = self.dataObj.get_current(guildID)
                    self.dataObj.switch_loop(guildID)
                    self.dataObj.set_random(guildID, False)
                    loop_var = self.dataObj.get_loop(guildID)
                    if loop_var is True:
                        log(guildName, 'now looping', song)
                    else:
                        log(guildName, 'stopped looping', song)
                    await interaction.response.edit_message(view=self.view)
                    song= self.dataObj.get_current(guildID) 
                    await channel.send(embed= self.embObj.loop_prompt(loop_var, song), delete_after=BUTTON_DELAY)
                    return
                await interaction.response.defer()
            except Exception as e:
                error_log('LoopButton', e, guildName= guildName)
      
    class FlushButton(Button):
        def __init__(self, music_cog,bot:commands.bot, dataObj:GuildData, embObj:Embeds, pHandler:PrintHandler,  guildID):
            self.music_cog = music_cog
            self.bot = bot
            self.dataObj = dataObj
            self.embObj  = embObj
            self.pHandler = pHandler
            voice_client = self.bot.get_guild(guildID).voice_client
            style = discord.ButtonStyle.blurple
            if voice_client is None:
                style= discord.ButtonStyle.grey
            super().__init__(emoji='🚽',label = 'Flush', style=style)
        async def callback(self, interaction: discord.Interaction):
            if await validate_command(interaction, self.dataObj, self.embObj) is False: return
            guildName = interaction.user.guild.name
            guildID = interaction.user.guild.id
            channel = interaction.channel
            voice_client = interaction.client.get_guild(guildID).voice_client
            log(guildName, 'button', 'flush')
            try:
                self.dataObj.reset(guildID)
                if voice_client.is_playing() or voice_client.is_paused():
                    voice_client.stop()
                self.dataObj.full_reset(guildID)
                await interaction.response.send_message(embed= self.embObj.flush_prompt(), delete_after=BUTTON_DELAY)
                await self.pHandler.GUI_HANDLER(None, guildID)
            except Exception as e:
                error_log('flushbutton', e, guildName= guildName)
    
    class ResetButton(Button):
        def __init__(self, music_cog,bot:commands.bot, dataObj:GuildData, embObj:Embeds, pHandler:PrintHandler,  guildID):
            self.music_cog = music_cog
            self.bot = bot
            self.dataObj = dataObj
            self.embObj  = embObj
            self.pHandler = pHandler
            voice_client = self.bot.get_guild(guildID).voice_client
            style=discord.ButtonStyle.red
            if voice_client is None:
                style= discord.ButtonStyle.grey
            super().__init__(label = 'Reset', style=style)
        async def callback(self, interaction: discord.Interaction):
            if await validate_command(interaction, self.dataObj, self.embObj) is False: return
            guildName = interaction.user.guild.name
            guildID = interaction.user.guild.id
            channel = interaction.channel
            voice_client = interaction.client.get_guild(guildID).voice_client
            log(guildName, 'button', 'reset')
            try:
                self.dataObj.full_reset(guildID)
                if voice_client is not None:
                    channel_name = voice_client.channel.name
                    if voice_client.is_playing() or voice_client.is_paused():
                        voice_client.stop()
                    await voice_client.disconnect()
                    log(guildName, 'DISCONNECTED (force)', channel_name)
                await self.pHandler.GUI_HANDLER(None, guildID)
                await interaction.response.send_message(embed= self.embObj.reset_prompt(), delete_after=BUTTON_DELAY)
            except Exception as e:
                error_log('resetbutton', e, guildName= guildName)

    class HelpButton(Button):
        def __init__(self, music_cog,bot:commands.bot, dataObj:GuildData, embObj:Embeds, pHandler:PrintHandler,  guildID):
            self.music_cog = music_cog
            self.bot = bot
            self.dataObj = dataObj
            self.embObj  = embObj
            self.pHandler = pHandler
            super().__init__(emoji = 'ℹ', style=discord.ButtonStyle.blurple)
        async def callback(self, interaction: discord.Interaction):
            guildName = interaction.user.guild.name
            guildID = interaction.user.guild.id
            channel = interaction.channel
            log(guildName, 'command', 'HelpButton')
            
            try:
                await interaction.response.defer()
                await self.pHandler.printHelpPrompt(channel)
                await asyncio.sleep(Setting.get_promptDelay())
                await self.pHandler.GUI_HANDLER(None, guildID)
            except Exception as e:
                error_log('HelpButton', e, guildName= guildName)
            

