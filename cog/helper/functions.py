import discord
from cog.helper.embed     import Embeds
from cog.helper.log       import *
from cog.helper           import Setting


async def create_bot_channel(guild:discord.guild.Guild):
    try:
        guildID = guild.id
        pocbot_channelID = Setting.get_channelID(guildID)
        channelsIDS = [channel.id for channel in guild.channels]
        if pocbot_channelID in channelsIDS:
            return
        category = None
        for cat in guild.categories:
            if cat.name == 'Text Channels':
                category = cat
                break
        pocbot_channel = await guild.create_text_channel(name='Music Controller', category=category)
        Setting.set_channelID(guildID, pocbot_channel.id)
        return pocbot_channel
    except Exception as e:
        error_log('create_bot_channel', e)
        return 'error'

async def voice_connect(user, voice_client):
    if voice_client is None:
        voice_client = await user.voice.channel.connect(reconnect=True)
        log(voice_client.guild.name, 'Voice Connected', voice_client.channel.name)
    else:
        if voice_client.is_connected() is False:
            await voice_client.move_to(user.voice.channel)
            log(voice_client.guild.name, 'Voice Reconnected', voice_client.channel.name)
    return voice_client

class SearchAlgorithmView(discord.ui.View):
    def __init__(self, music_cog, embObj:Embeds, user):
        super().__init__()
        self.add_item(SearchAlgorithmSelect(music_cog, user, embObj, self))
        self.music_cog = music_cog
        self.embObj = embObj
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
            msg = self.embObj.unauthorized_user_prompt()
            await interaction.response.send_message(embed=msg, ephemeral=True, delete_after=4)
            return False
class SearchAlgorithmSelect(discord.ui.Select):
    def __init__(self, music_cog, user, embObj:Embeds, view):
        self.music_cog = music_cog
        self.embObj = embObj
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
            await interaction.response.edit_message(embed=self.embObj.search_algorithm_prompt(searchalgo), view=None)
        except Exception as e:
            error_log('SearchAlgorithmSelect',e)