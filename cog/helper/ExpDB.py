import os, json
from cog.helper.log import *
from setting import get_expData
from GlobVar import EXP_FILE_PATH

def add_exp(user, command, expPoints = None):
    exp = 0
    userID = str(user.id)
    init_user(userID)
    if expPoints is None:
        expPoints = get_expData()[command.lower()]

    with open(EXP_FILE_PATH, 'r+') as file:
        expDB = json.load(file)
        multiplier = int(expDB['multiplier'])
        level = int(expDB['level'])
        adjusted_exp = ((150-level)/150)
        expDB[userID]['experience'] += exp*multiplier*adjusted_exp
        exp = expDB[userID]['experience']
        calc_level = int(exp/200)
        if calc_level > level:
            expDB['level'] = calc_level
        
        #RELOAD
        file.seek(0)
        json.dump(EXP_FILE_PATH, file, indent=4)
        file.truncate()

def get_data():
    with open(EXP_FILE_PATH, 'r+') as file:
        expDB = json.load(file)
        return expDB
    
def init_user(userID):
    userID = str(userID)
    with open(EXP_FILE_PATH, 'r+') as file:
        expDB = json.load(file)
        if userID in expDB:
            return
        expDB[userID] = {}
        expDB[userID]['level']      = 1
        expDB[userID]['rank']       = 'None'
        expDB[userID]['experience'] = 0
        expDB[userID]['multiplier'] = 1
        #FOR DATA PURPOSE ONLY
        expDB[userID]['slashcommand_count'] = 0
        expDB[userID]['play_command_count'] = 0
        expDB[userID]['skip_command_count'] = 0
        expDB[userID]['playrandom_command_count'] = 0
        expDB[userID]['shuffle_command_count'] = 0
        expDB[userID]['pause_command_count'] = 0
        expDB[userID]['resume_command_count'] = 0
        expDB[userID]['loop_command_count'] = 0
        expDB[userID]['flush_command_count'] = 0
        expDB[userID]['join_command_count'] = 0
        expDB[userID]['help_command_count'] = 0
        expDB[userID]['reset_command_count'] = 0
        expDB[userID]['switch_algorithm_command_count'] = 0
        expDB[userID]['prefix_command_count'] = 0
        



        file.seek(0)
        json.dump(EXP_FILE_PATH, file, indent=4)
        file.truncate()

def initialize_level_system():
    default_setting = {}
    if not os.path.exists(EXP_FILE_PATH):
        with open(EXP_FILE_PATH, 'w') as file:
            json.dump(default_setting, file, indent=4)
    log(None, 'initialized', EXP_FILE_PATH)
