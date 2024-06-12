import os
from datetime import datetime
LOG_FOLDER    = os.getcwd()+'\\Music Bot Log Folder'
def song_name(song):
    title = str(song['title'])
    author = str(song['author'])
    return f'{title} - {author}'

def LogFolderInitialize():
    if os.path.exists(LOG_FOLDER) is False:
        os.makedirs(LOG_FOLDER)

def save_log(log_statement, time):
    path = LOG_FOLDER + f'\\{str(time.date())}.txt'
    if os.path.exists(path) is False:
        LogFolderInitialize()
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
