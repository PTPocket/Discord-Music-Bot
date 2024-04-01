import os, json
SETTING_PATH    = os.getcwd()+'/Music Bot Setting.json'

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
    setting = {
            'Timeout Minutes'          : 60,
            'Unauthorized Prompt Text' : 'Unauthorized',
            'Skip Error Prompt Text'   : 'Nothing to Skip',
            'Queue Prompt Text'        : 'Queued Song',
            'Flush Prompt Text'        : 'Flushed Data',
            'Finished Prompt Text'     : 'Playlist Uploaded',
        }

    if os.path.exists(SETTING_PATH) is True:
        with open(SETTING_PATH, 'r') as file:
            cur_setting = json.load(file)
        cur_setting_keys = cur_setting.keys()
        for key in setting:
            if key not in cur_setting_keys:
                cur_setting[key] = setting[key]
        with open(SETTING_PATH, 'w') as file:
            json.dump(cur_setting, file, indent=4)
    else:
        with open(SETTING_PATH, 'w') as file:
            json.dump(setting, file, indent=4)
    print('Setting Initialized')

if __name__ == '__main__':
    initialize_settings()
    print(get_timeout())