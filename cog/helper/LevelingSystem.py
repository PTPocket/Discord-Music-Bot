import os, json
from cog.helper.Log import *
LEVEL_PATH   = os.getcwd()+'\\Points Data.json'



def initialize_level_system():
    default_setting = {}
    if not os.path.exists(LEVEL_PATH):
        with open(LEVEL_PATH, 'w') as file:
            json.dump(default_setting, file, indent=4)
    log(None, 'initialized', LEVEL_PATH)
