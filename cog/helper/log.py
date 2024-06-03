from datetime import datetime

def log(guild_name, action:str, description = ''):
    time= str(datetime.now())
    action = str(action).upper()
    description = str(description).lower()
    if description != '':
        print(f"{time} | GUILD: {guild_name} | {action} -> {description}")
    else:
        print(f"{time} | GUILD: {guild_name} | {action}")

def error_log(location, description, item = None):
    time = str(datetime.now())
    location = str(location).upper()
    description = str(description).lower()
    if item is None:
        print(f'{time} | ERROR: {location} | {description}')
    else:
        print(f'{time} | ERROR: {location} | {description} | {str(item)}')