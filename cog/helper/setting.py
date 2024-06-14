import os, json
from cog.helper.Log import *
from Paths import SETTING_PATH

### INITIALIZE ###
def initialize_settings():
    default_setting = {
            'Timeout Minutes'    : 60,
            'Prompt Delay'       : 60,
            'PocBot Text Channel': {},
            'Last Message'       : {},
            'Now Playing ChannelID' : {},
            'Now Playing MessageID': {},
            'Guild Prefix'       : {},
            'Search Algorithm'   : {},
            'Exp Point Data'     : {
                'play'        : 3,
                'play_random' : 7,
                'shuffle'     : 9,
                'skip'        : 2,
                'next'        : 2,
                'previous'    : 3,
                'pause'       :-1,
                'resume'      : 1,
                'loop'        : 5,
                'reset'       : 6,
                'help'        : 10,
                'generate'    : 10,
                'join'        : 4,
                'flush'       : 3,
                'prefix' : 10,
                'switch_algorithm' : 10,
                'slashcommand' : 50
                }
    }

    if os.path.exists(SETTING_PATH) is True:
        with open(SETTING_PATH, 'r') as file:
            cur_setting = json.load(file)
        cur_setting_keys = cur_setting.keys()
        for key in default_setting:
            if key not in cur_setting_keys:
                cur_setting[key] = default_setting[key]
        with open(SETTING_PATH, 'w') as file:
            json.dump(cur_setting, file, indent=4)
    else:
        with open(SETTING_PATH, 'w') as file:
            json.dump(default_setting, file, indent=4)
    log(None, 'initialized', SETTING_PATH)

### SET ###
def set_channelID(guildID,id):
    setting = None
    with open(SETTING_PATH, 'r+') as file:
        setting = json.load(file)
        setting['PocBot Text Channel'][str(guildID)] = id
        file.seek(0)
        json.dump(setting, file, indent=4)
        file.truncate()
def set_messageID(guildID, id):
    setting = None
    with open(SETTING_PATH, 'r+') as file:
        setting = json.load(file)
        setting['Last Message'][str(guildID)] = id
        file.seek(0)
        json.dump(setting, file, indent=4)
        file.truncate()

def set_nowPlayingMessage(guildID, channelID, messageID):
    setting = None
    with open(SETTING_PATH, 'r+') as file:
        setting = json.load(file)
        setting['Now Playing MessageID'][str(guildID)] = messageID
        setting['Now Playing ChannelID'][str(guildID)] = channelID
        file.seek(0)
        json.dump(setting, file, indent=4)
        file.truncate()

def set_guildPrefix(guildID, prefix):
    with open(SETTING_PATH, 'r+') as file:
        setting = json.load(file)
        setting['Guild Prefix'][str(guildID)] = prefix
        file.seek(0)
        json.dump(setting, file, indent=4)
        file.truncate()

def set_searchAlgorithm(guildID, algorithm):
    with open(SETTING_PATH, 'r+') as file:
        setting = json.load(file)
        setting['Search Algorithm'][str(guildID)] = algorithm
        file.seek(0)
        json.dump(setting, file, indent=4)
        file.truncate()

### GET ###
def get_nowPlayingMessage(guildID):
    with open(SETTING_PATH, 'r') as file:
        setting = json.load(file)
    if str(guildID) in setting['Now Playing MessageID']:
        messageID = setting['Now Playing MessageID'][str(guildID)]
        channelID = setting['Now Playing ChannelID'][str(guildID)]
        return int(channelID), int(messageID)
    return None, None
def get_timeout():
    with open(SETTING_PATH, 'r') as file:
        setting = json.load(file)
    return int(setting['Timeout Minutes'])*60

def get_promptDelay():
    with open(SETTING_PATH, 'r') as file:
        setting = json.load(file)
    return setting['Prompt Delay']

def get_channelID(guildID):
    with open(SETTING_PATH, 'r') as file:
        setting = json.load(file)
    if str(guildID) in setting['PocBot Text Channel']:
        return int(setting['PocBot Text Channel'][str(guildID)])
    return None

def get_messageID(guildID):
    with open(SETTING_PATH, 'r') as file:
        setting = json.load(file)
    if str(guildID) in setting['Last Message']:
        return int(setting['Last Message'][str(guildID)])
    return None

def get_guildPrefix(guildID):
    with open(SETTING_PATH, 'r+') as file:
        setting = json.load(file)
        if str(guildID) in setting['Guild Prefix']:
            return setting['Guild Prefix'][str(guildID)]
        setting['Guild Prefix'][str(guildID)] = '/'
        file.seek(0)
        json.dump(setting, file, indent=4)
        file.truncate()
        return '/'

def get_searchAlgorithm(guildID):
    with open(SETTING_PATH, 'r+') as file:
        setting = json.load(file)
        if str(guildID) in setting['Search Algorithm']:
            return setting['Search Algorithm'][str(guildID)]
        setting['Search Algorithm'][str(guildID)] = 'spotify'
        file.seek(0)
        json.dump(setting, file, indent=4)
        file.truncate()
        return 'spotify'
    
def get_expData():
    with open(SETTING_PATH, 'r') as file:
        setting = json.load(file)
        return setting['Exp Point Data']


