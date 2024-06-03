import os
from datetime import datetime
LOG_FOLDER    = os.getcwd()+'\\Music Bot Log Folder'



def log(guild_name, action:str, description = ''):
    time= datetime.now()
    action = str(action).upper()
    description = str(description).lower()
    if description != '':
        log_statement = f"{str(time)} | GUILD: {guild_name} | {action} -> {description}"
        print(log_statement)
    else:
        log_statement = f"{str(time)} | GUILD: {guild_name} | {action}"
        print(log_statement)

    path = LOG_FOLDER + f'\\{str(time.date())}.txt'
    log_statement+= '\n'
    if os.path.exists(path) is False:
        LogFolderInitialize()
        with open(path, 'a') as logfile:
            pass
    with open(path, 'a') as logfile:
        logfile.write(log_statement)
    
def error_log(location, description, item = None):
    time = datetime.now()
    location = str(location).upper()
    description = str(description).lower()
    if item is None:
        log_statement = f'{str(time)} | ERROR: {location} | {description}'
        print(log_statement)
    else:
        log_statement = f'{str(time)} | ERROR: {location} | {description} | {str(item)}'
        print(log_statement)
    path = LOG_FOLDER + f'\\{time.date()}.txt'
    log_statement+= '\n'
    if os.path.exists(path) is False:
        with open(path, 'a') as logfile:
            LogFolderInitialize()
            logfile.write(log_statement)
    else:
        with open(path, 'a+') as logfile:
            logfile.write(log_statement)

def LogFolderInitialize():
    if os.path.exists(LOG_FOLDER) is False:
        os.makedirs(LOG_FOLDER)
