import os, json
SETTING_PATH    = os.curdir+'/setting.json'


def get_timeout():
    with open(SETTING_PATH, 'r') as file:
        setting = json.load(file)
    return int(setting['Timeout Minutes'])*60

def get_unauthorizedText():
    with open(SETTING_PATH, 'r') as file:
        setting = json.load(file)
    return setting['Unauthorized Prompt Text']

def get_skiperrorText():
    with open(SETTING_PATH, 'r') as file:
        setting = json.load(file)
    return setting['Skip Error Prompt Text']

def get_queueText():
    with open(SETTING_PATH, 'r') as file:
        setting = json.load(file)
    return setting['Queue Prompt Text']

def get_flushText():
    with open(SETTING_PATH, 'r') as file:
        setting = json.load(file)
    return setting['Flush Prompt Text']

def get_finishedText():
    with open(SETTING_PATH, 'r') as file:
        setting = json.load(file)
    return setting['Finished Prompt Text']

def get_finishedText():
    with open(SETTING_PATH, 'r') as file:
        setting = json.load(file)
    return setting['Finished Prompt Text']

def initialize_settings():
    if os.path.exists(SETTING_PATH) is True:
        return
    with open(SETTING_PATH, 'w') as file:
        setting = {
            'Timeout Minutes'     : 60,

            'Unauthorized Prompt Text' : 'Unauthorized',
            'Skip Error Prompt Text'   : 'Nothing to Skip',
            'Queue Prompt Text'        : 'Queued',
            'Flush Prompt Text'        : 'Flushed Data',
            'Finished Prompt Text'     : 'Done',

        }
        json.dump(setting, file, indent=4)
    pass


if __name__ == '__main__':
    initialize_settings()
    print(get_timeout())