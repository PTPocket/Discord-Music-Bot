    
import os
from cog.helper.Log import *
from Paths import INVALID_URL_PATH

def save(platform, url):
    try:
        with open(INVALID_URL_PATH, 'w') as file:
            text = platform + ':' + url 
            file.write(text+'\n')
            log(None, 'saved invalid url', text)
    except Exception as e:
        error_log('invalid url save', e)

def initialize():
    if os.path.exists(INVALID_URL_PATH) is False:
        with open(INVALID_URL_PATH, 'w') as file:
            pass
    log(None, 'initialized', INVALID_URL_PATH)
