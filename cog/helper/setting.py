import os, json
from cog.helper.Log import *

SETTING_PATH    = os.getcwd()+'\\Music Bot Setting.json'

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
def set_guildPrefix(guildID, prefix):
    with open(SETTING_PATH, 'r+') as file:
        setting = json.load(file)
        setting['Guild Prefix'][str(guildID)] = prefix
        file.seek(0)
        json.dump(setting, file, indent=4)
        file.truncate()

### GET ###
def get_timeout():
    with open(SETTING_PATH, 'r') as file:
        setting = json.load(file)
    return int(setting['Timeout Minutes'])*60

def get_skiperrorText():
    with open(SETTING_PATH, 'r') as file:
        setting = json.load(file)
    return setting['Skip Error Prompt']

def get_queueText():
    with open(SETTING_PATH, 'r') as file:
        setting = json.load(file)
    return setting['Queue Prompt']

def get_flushText():
    with open(SETTING_PATH, 'r') as file:
        setting = json.load(file)
    return setting['Flush Prompt']

def get_finishedText():
    with open(SETTING_PATH, 'r') as file:
        setting = json.load(file)
    return setting['Finished Prompt']

def get_promptDelay():
    with open(SETTING_PATH, 'r') as file:
        setting = json.load(file)
    return setting['Prompt Delay']

def get_helpPromptDelay():
    with open(SETTING_PATH, 'r') as file:
        setting = json.load(file)
    return setting['Help Prompt Delay']

def get_shuffleText():
    with open(SETTING_PATH, 'r') as file:
        setting = json.load(file)
    return setting['Shuffle Prompt']

def get_prevText():
    with open(SETTING_PATH, 'r') as file:
        setting = json.load(file)
    return setting['Prev Prompt']

def get_resetText():
    with open(SETTING_PATH, 'r') as file:
        setting = json.load(file)
    return setting['Reset Prompt']

def get_channelID(guildID):
    with open(SETTING_PATH, 'r') as file:
        setting = json.load(file)
    if str(guildID) in setting['PocBot Text Channel']:
        return setting['PocBot Text Channel'][str(guildID)]
    return None

def get_messageID(guildID):
    with open(SETTING_PATH, 'r') as file:
        setting = json.load(file)
    if str(guildID) in setting['Last Message']:
        return setting['Last Message'][str(guildID)]
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

def get_botdisconnectText():
    with open(SETTING_PATH, 'r') as file:
        setting = json.load(file)
    return setting['Bot Disconnected Prompt']

def get_generatedText():
    with open(SETTING_PATH, 'r') as file:
        setting = json.load(file)
    return setting['Generated Prompt']

def get_invalid_channelText():
    with open(SETTING_PATH, 'r') as file:
        setting = json.load(file)
    return setting['Invalid Channel Prompt']

def get_user_disconnectedText():
    with open(SETTING_PATH, 'r') as file:
        setting = json.load(file)
    return setting['User Disconnected Prompt']

def get_previousText():
    with open(SETTING_PATH, 'r') as file:
        setting = json.load(file)
    return setting['Previous Prompt']

def get_alreadygeneratedText():
    with open(SETTING_PATH, 'r') as file:
        setting = json.load(file)
    return setting['Already Generated Prompt']



def initialize_settings():
    default_setting = {
            'Skip Error Prompt'        : 'Nothing to Skip',
            'Queue Prompt'             : 'Queued',
            'Flush Prompt'             : 'Flushed Data',
            'Shuffle Prompt'           : 'Shuffled Songs',
            'Prev Prompt'              : 'Skipped back to',
            'Reset Prompt'             : 'Reset PocBot',
            'Bot Disconnected Prompt'  : "Connect the bot to a voice channel with  /play",
            'Generated Prompt'         : 'Generated text channel and music player interface',
            'Invalid Channel Prompt'   : 'Already in use',
            'User Disconnected Prompt' : 'Join a voice channel first',
            'Previous Prompt'          : 'Skipped back to',
            'Already Generated Prompt' : 'Already generated text channel and music player interface',
            
            'Timeout Minutes'          : 60,
            'Prompt Delay'             : 3,
            'Help Prompt Delay'        : 60,
            'PocBot Text Channel'      : {},
            'Last Message'             : {},
            'Guild Prefix'             : {}
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
    log(None, 'initialized', 'settings file')

