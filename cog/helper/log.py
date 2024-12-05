import os
from datetime import datetime
from GlobVar import LOG_FOLDER_PATH, INVALID_URL_PATH

def song_name(song):
    title = str(song['title'])
    author = str(song['author'])
    return f'{title} - {author}'

def save_log(log_statement, time):
    path = LOG_FOLDER_PATH + f'\\{str(time.date())}.txt'
    if os.path.exists(path) is False:
        with open(path, 'a', encoding='utf-8') as logfile:
            pass
    with open(path, 'a', encoding='utf-8') as logfile:
        logfile.write(log_statement)

def log(guild_name, action:str, description = ''):
    try:
        time= datetime.now()
        action = str(action).upper()
        if type(description) is dict:
            description = song_name(description)
        description = str(description).lower()
        if description != '':
            log_statement = f"{str(time)} | GUILD: {guild_name} | {action} -> {description}"
            print(log_statement)
        else:
            log_statement = f"{str(time)} | GUILD: {guild_name} | {action}"
            print(log_statement)
        log_statement+= '\n'
        save_log(log_statement, time)
    except Exception as e:
        error_log('log', e)
    

def error_log(location, description, item = None, guildName = 'N/A'):
    try:
        time = datetime.now()
        location = str(location).upper()
        description = str(description).lower()
        if item is None:
            log_statement = f'{str(time)} | GUILD: {guildName} | ERROR: {location} | {description}'
            print(log_statement)
        else:
            log_statement = f'{str(time)} | GUILD: {guildName} | ERROR: {location} | Description: {description} | Item: {str(item)}'
            print(log_statement)
        log_statement+= '\n'
        save_log(log_statement, time)    
    except Exception as e:
        error_log('error_log', e)


def save_invalidUrl(platform, url):
    try:
        with open(INVALID_URL_PATH, 'w') as file:
            text = url 
            file.write(text+'\n')
            log(None, 'saved invalid url', text)
    except Exception as e:
        error_log('invalid url save', e)

def initialize_Log():
    if os.path.exists(INVALID_URL_PATH) is False:
        with open(INVALID_URL_PATH, 'w') as file:
            pass
    if os.path.exists(LOG_FOLDER_PATH) is False:
        os.makedirs(LOG_FOLDER_PATH)
    log(None, 'LOGS', 'initialized')