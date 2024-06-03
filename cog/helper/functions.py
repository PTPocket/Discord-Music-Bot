import discord, os, random
from tinytag               import TinyTag
from cog.helper            import embed
from cog.helper.GuildData import Guild_Music_Properties
from discord.ui            import View, Select, Button
from cog.helper.GuildData import Guild_Music_Properties
from cog.helper.Log    import *

BLANK = '\u200b'
LOCAL_MUSIC_PATH = "C:\\Users\\p\\Documents\\SERVER\\music\\Formatted"

async def GUI_HANDLER(Music_Cog, guildID, edit = True, error = False):
    try:
        player_embed = embed.MainGuiPrompt(Music_Cog.bot, Music_Cog.data, guildID, connect = error)
        view = MusicFunctions(Music_Cog, Music_Cog.data, guildID)
        channel = Music_Cog.data.get_channel(guildID)
        last_message = Music_Cog.data.get_message(guildID)
        if last_message is None:
            message = await channel.send(embed = player_embed, view = view)
            Music_Cog.data.set_message(guildID, message)
            return
        if edit is True:
            message = await last_message.edit(embed = player_embed, view = view)
            Music_Cog.data.set_message(guildID, message)
            return
        message = await channel.send(embed = player_embed, view = view)
        await last_message.delete()
        Music_Cog.data.set_message(guildID, message)
    except Exception as e:
        error_log('Gui_handler', e)

async def valid_play_command(interaction:discord.Interaction):
    user = interaction.user
    guild_name = interaction.user.guild.name
    guild_id = interaction.user.guild.id

    voice_client = interaction.client.get_guild(guild_id).voice_client
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
        log(guild_name, 'ACCESS DENIED', user)
        msg = embed.unauthorized_prompt(interaction.client)
        await interaction.response.send_message(embed= msg, ephemeral=True)
    else:
        log(guild_name, 'ACCESS GRANTED', user)
    return authorized

async def valid_play_command2(bot, ctx):
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
        await ctx.send(embed= msg, ephemeral=True)
    else:
        log(guildName, 'ACCESS GRANTED', user)
    return authorized

async def valid_user_REGULAR_FUNC(interaction:discord.Interaction):
    user = interaction.user
    guild_name = interaction.user.guild.name
    guild_id = interaction.user.guild.id
    authorized = None
    voice_client = interaction.client.get_guild(guild_id).voice_client

    if user.voice is None or \
    voice_client is None or \
    not voice_client.is_connected():
        authorized = False
    elif voice_client.channel.id == user.voice.channel.id:
        authorized =  True
    else: 
        authorized =  False

    if authorized is False:
        log(guild_name, 'ACCESS DENIED', user)
        msg = embed.unauthorized_prompt(interaction.client)
        await interaction.response.send_message(embed= msg, ephemeral=True)
    else: log(guild_name, 'ACCESS GRANTED', user) 
    return authorized

async def voice_connect(user, guild_name, guild_id, voice_client):
    if voice_client is None:
        voice_client = await user.voice.channel.connect(reconnect=True)
        log(guild_name, 'Voice Connected', voice_client.channel.name)
    else:
        if voice_client.is_connected() is False:
            await voice_client.move_to(user.voice.channel)
            log(guild_name, 'Voice Reconnected', voice_client.channel.name)

    return voice_client

def check_features(data:Guild_Music_Properties, guild_id):
    if data.get_back(guild_id) is True:
        data.history_to_queue(guild_id)
        data.history_to_queue(guild_id)
        data.flip_back(guild_id)
        return
    if data.get_loop(guild_id) is True:
        data.history_to_queue(guild_id)
        return

    if data.get_shuffle(guild_id) is True:
        queue = data.get_queue(guild_id)
        history = data.get_history(guild_id)
        num_songs = len(queue)+len(history)
        rand_int = random.randint(0, num_songs-1)
        last_shuffle_int = data.get_last_shuffle(guild_id)
        while rand_int == last_shuffle_int and num_songs > 1:
            rand_int = random.randint(0, num_songs-1)
        data.set_last_shuffle(guild_id, rand_int)
        if rand_int < len(history):
            new_history = history[len(history)-rand_int::]
            to_queue = history[0:len(history)-rand_int]
            to_queue.reverse()
            new_queue = to_queue + queue
            data.set_queue(guild_id, new_queue)
            data.set_history(guild_id, new_history)
        else:
            rand_int = rand_int-len(history)
            new_queue = queue[rand_int::]
            to_history = queue[0:rand_int]
            to_history.reverse()
            new_history = to_history+history
            data.set_queue(guild_id, new_queue)
            data.set_history(guild_id, new_history)
        return

    if data.empty_queue(guild_id) is True and data.get_random(guild_id) is True:
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
        data.queue_song(guild_id, song)
        return

def add_random_song(data, guild_id):
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
    data.prepend_to_queue(guild_id, song)

def queuePlaylist(guildName, guildID, playlist, playlistType:str, data:Guild_Music_Properties):
        playlistType = playlistType.lower()
        song_names_list = []
        name_list = ''
        last_ind = None
        for ind, song in enumerate(playlist):
            data.queue_song(guildID,song)
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
        self.add_item(self.PreviousButton  (music_cog, data))
        self.add_item(self.PlayPause       (data))
        self.add_item(self.NextButton      (music_cog, data))
        self.add_item(self.ShuffleButton   (music_cog, data, guildID))
        self.add_item(self.LoopButton      (music_cog, data, guildID))
        self.add_item(self.RandomButton    (music_cog, data, guildID))
        self.add_item(self.ResetButton(music_cog, data))
        self.add_item(self.DisconnectButton(music_cog, data))
        
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
            await interaction.response.defer()
            return False

    class PlayPause(Button):
        def __init__(self, data:Guild_Music_Properties):
            super().__init__(emoji = '⏯', style= discord.ButtonStyle.blurple)
            self.data = data
        async def callback(self, interaction: discord.Interaction):
            try:
                guildName = interaction.user.guild.name
                guildID = interaction.user.guild.id
                voice_client = interaction.client.get_guild(guildID).voice_client
                log(guildName, 'BUTTON', 'play/pause')
                song = self.data.get_current_song(guildID)
                if voice_client is None:
                    self.style = discord.ButtonStyle.grey
                    await interaction.response.edit_message(view=self.view)
                    return
                if voice_client.is_playing() and not voice_client.is_paused():
                    log(guildName, 'PAUSED',song['title'])
                    voice_client.pause()
                    self.style = discord.ButtonStyle.grey
                    await interaction.response.edit_message(view=self.view)
                    return
                if not voice_client.is_playing() and voice_client.is_paused():
                    log(guildName, 'RESUMED',song['title'])
                    self.style = discord.ButtonStyle.blurple
                    await interaction.response.edit_message(view=self.view)
                    voice_client.resume()
                    return
                await interaction.response.defer()
            except Exception as e:
                error_log('PlayPause', e)
            
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
                log(guildName, 'BUTTON', 'random')
                if self.data.flip_random(guildID) is True:
                    log(guildName, 'RANDOM', 'On')
                    self.data.set_loop(guildID, False)
                    await self.music_cog.music_player_start(user, guildName, guildID, voice_client, channel, edit = True)
                else: 
                    log(guildName, 'RANDOM', 'Off')
                    await GUI_HANDLER(self.music_cog, guildID)
                await interaction.response.defer()
            except Exception as e:
                error_log('RandomButton', e)
    
    class PreviousButton(Button):
        def __init__(self,music_cog, data:Guild_Music_Properties):
            super().__init__(emoji = "⏮", style= discord.ButtonStyle.blurple)
            self.data = data
            self.music_cog = music_cog

        async def callback(self, interaction: discord.Interaction):
            try:
                user = interaction.user
                guildName = interaction.user.guild.name
                guildID = interaction.user.guild.id
                voice_client = interaction.client.get_guild(guildID).voice_client
                channel = interaction.channel
                log(guildName, 'BUTTON', 'previous')

                #IF VOICE RUNNING
                if voice_client is None:
                    self.data.set_loop(guildID, False)
                    self.data.history_to_queue(guildID)
                    await interaction.response.defer(thinking=True)
                    await self.music_cog.music_player_start(user, guildName, guildID, voice_client, channel, edit = True)
                    await interaction.delete_original_response()
                    return
                if voice_client.is_playing() or voice_client.is_paused():
                    self.data.set_loop(guildID, False)
                    self.data.flip_back(guildID)
                    voice_client.stop()
                    await interaction.response.defer(thinking=True)
                    await self.music_cog.music_player_start(user, guildName, guildID, voice_client, channel, edit = True)
                    await interaction.delete_original_response()
                    return
                self.data.set_loop(guildID, False)
                self.data.history_to_queue(guildID)
                await interaction.response.defer(thinking=True)
                await self.music_cog.music_player_start(user, guildName, guildID, voice_client, channel, edit = True)
                await interaction.delete_original_response()
                return
            except Exception as e:
                error_log('PreviousButton', e)
    
    class NextButton(Button):
        def __init__(self,music_cog, data:Guild_Music_Properties):
            super().__init__(emoji = "⏭", style= discord.ButtonStyle.blurple)
            self.data = data
            self.music_cog = music_cog

        async def callback(self, interaction: discord.Interaction):
            try:
                guildName = interaction.user.guild.name
                guildID = interaction.user.guild.id
                voice_client = interaction.client.get_guild(guildID).voice_client
                log(guildName, 'BUTTON', 'next')
                if voice_client is None:
                    await interaction.response.defer()
                    return
                if (voice_client.is_playing() or voice_client.is_paused()):
                    self.data.set_loop(guildID, False)
                    voice_client.stop()
                    await interaction.response.defer(thinking=True)
                    await GUI_HANDLER(self.music_cog, guildID)
                    await interaction.delete_original_response()
                    return
            except Exception as e:
                error_log('NextButton', e)
            
    class ShuffleButton(Button):
        def __init__(self,music_cog, data:Guild_Music_Properties, guildID):
            if data.get_shuffle(guildID) is True:
                style= discord.ButtonStyle.blurple
            else:
                style= discord.ButtonStyle.grey
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
                log(guildName, 'BUTTON', 'shuffle')
                await interaction.response.defer()
                if voice_client is None:
                    return
                queue = self.data.get_queue(guildID)
                history = self.data.get_history(guildID)
                num_songs = len(queue)+len(history)
                if num_songs > 0 or voice_client.is_playing() or voice_client.is_paused():
                    self.data.set_random(guildID, False)
                    self.data.flip_shuffle(guildID)
                    if self.data.get_shuffle(guildID) is True:
                        log(guildName, 'Shuffle', 'on')
                        await self.music_cog.music_player_start(user, guildName, guildID, voice_client, channel, edit = True)
                    else:
                        log(guildName, 'Shuffle', 'off')
                    await GUI_HANDLER(self.music_cog, guildID)
            except Exception as e:
                error_log('ShuffleButton', e)
    
    class LoopButton(Button):
        def __init__(self,music_cog, data:Guild_Music_Properties, guildID):
            if data.get_loop(guildID) is True:
                style= discord.ButtonStyle.blurple
            else:
                style= discord.ButtonStyle.grey
            super().__init__(emoji = "🔁", style=style)
            self.music_cog = music_cog
            self.data = data
        async def callback(self, interaction: discord.Interaction):
            try:
                guildName = interaction.user.guild.name
                guildID = interaction.user.guild.id
                log(guildName, 'BUTTON', 'loop')
                voice_client = interaction.client.get_guild(guildID).voice_client
                await interaction.response.defer()
                if voice_client is None:
                    return
                if voice_client.is_playing() or voice_client.is_paused():
                    song = self.data.get_current_song(guildID)
                    self.data.flip_loop(guildID)
                    self.data.set_random(guildID, False)
                    if self.data.get_loop(guildID) is True:
                        log(guildName, 'looping', "on")
                    else:
                        log(guildName, 'looping', "off")
                    await GUI_HANDLER(self.music_cog, guildID)
                    return
            except Exception as e:
                error_log('LoopButton', e)
    
    class DisconnectButton(Button):
        def __init__(self,music_cog, data:Guild_Music_Properties):
            super().__init__(label = 'Disconnect', style=discord.ButtonStyle.grey)
            self.music_cog = music_cog
            self.data = data
        async def callback(self, interaction: discord.Interaction):
            try:
                guildName = interaction.user.guild.name
                guildID = interaction.user.guild.id
                voice_client = interaction.client.get_guild(guildID).voice_client
                log(guildName, 'button', 'disconnect')
                self.data.full_reset(guildID)
                if voice_client is not None:
                    channel_name = voice_client.channel.name
                    if voice_client.is_playing() or voice_client.is_paused():
                        voice_client.stop()
                    await voice_client.disconnect()
                    log(guildName, 'DISCONNECTED (force)', channel_name)
                await interaction.response.defer()
                await GUI_HANDLER(self.music_cog, guildID)
            except Exception as e:
                error_log('DisconnectButton', e)
    
    class ResetButton(Button):
        def __init__(self,music_cog, data:Guild_Music_Properties):
            super().__init__(emoji='🚽',label = 'Flush', style=discord.ButtonStyle.grey)
            self.music_cog = music_cog
            self.data = data
        async def callback(self, interaction: discord.Interaction):
            try:
                guildName = interaction.user.guild.name
                guildID = interaction.user.guild.id
                voice_client = interaction.client.get_guild(guildID).voice_client
                log(guildName, 'button', 'flush')
                await interaction.response.defer(ephemeral=True)
                
                self.data.reset(guildID)
                if voice_client is not None:
                    if voice_client.is_playing() or voice_client.is_paused():
                        voice_client.stop()
                self.data.full_reset(guildID)
                #await interaction.response.send_message(embed=embed.flush_prompt(self.music_cog.bot),ephemeral=True)
                await GUI_HANDLER(self.music_cog, guildID)
            except Exception as e:
                error_log('ResetButton', e)