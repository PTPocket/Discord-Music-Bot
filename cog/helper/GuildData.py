from datetime import datetime
import asyncio

class Guild_Music_Properties():
    def __init__(self):
        #SONG PLACEMENT
        self.library   = {}
        self.pos = {}
        #MUSIC PLAYER FEATURES
        self.loop    = {}
        self.random  = {}
        #AutoDisconnect
        self.time   = {}
        self.playing = {}

        #Other
        self.channel = {}
        self.npLocks = {}
        self.guiLocks = {}
    def initialize(self, guildID):
        if guildID not in self.library:
            self.library [guildID] = []
            self.pos     [guildID] = None
            self.loop    [guildID] = False
            self.random  [guildID] = False
            self.time    [guildID] = None
            self.playing [guildID] = False
            self.channel [guildID] = None
            self.guiLocks[guildID] = asyncio.Lock()
            self.npLocks [guildID] = asyncio.Lock()
    #SET VALUE FUNCTIONS
    def set_new_library(self, guildID, new_library):
        self.library[guildID] = new_library
        self.pos[guildID] = 0
    def set_pos(self,guildID, value):
        self.pos[guildID] = value
    def set_current(self, guildID, value):
        if self.pos[guildID] is None and len(self.library[guildID]) > 0:
            self.library[guildID][0] = value
            return
        if self.pos[guildID] is None:
            return
        self.library[guildID][self.pos[guildID]] = value
    def set_loop(self,guildID, value):
        self.loop[guildID] = value
    def set_random(self, guildID, value):
        self.random[guildID] = value
    def set_idle_timestamp(self,guildID):
        self.time[guildID] = datetime.today()
    def set_playing(self, guildID, value):
        self.playing[guildID] = value
    def set_channel(self, guildID, channel):
        self.channel[guildID] = channel
    #RETRIEVE VALUES FUNCTIONS
    def get_library(self, guildID):
        return self.library[guildID]
    def get_pos(self, guildID):
        return self.pos[guildID]
    def get_loop(self,guildID):
        return self.loop[guildID]
    def get_random(self,guildID):
        return self.random[guildID]
    def get_guildIDs(self):
        return self.library.keys()
    def get_time(self, guildID):
        return self.time[guildID]
    def get_playing(self, guildID):
        return self.playing[guildID]
    def get_current(self, guildID):
        if self.pos[guildID] is None and len(self.library[guildID]) > 0:
            return self.library[guildID][0]
        if self.pos[guildID] is None or self.pos[guildID] == len(self.library[guildID]):
            return None
        return self.library[guildID][self.pos[guildID]]
    def get_queue(self, guildID):
        if self.pos[guildID] is None and len(self.library[guildID]) > 0:
            return self.library[guildID][1:]
        if self.pos[guildID] is None:
            return []
        return self.library[guildID][self.pos[guildID]+1:]
    def get_history(self, guildID):
        if self.pos[guildID] is None:
            return []
        return self.library[guildID][:self.pos[guildID]]
    def get_prev_song(self, guildID):
        if self.pos[guildID] is None:
            return None
        if self.pos[guildID] > 0:
            return self.library[guildID][self.pos[guildID]-1]
        return None
    def get_next(self, guildID):
        if self.pos[guildID] is None and len(self.library[guildID]) > 1:
            return self.library[1]
        if self.pos[guildID] is None:
            return None
        if self.pos[guildID] < len(self.library)-2:
            return self.library[guildID][self.pos[guildID]+1]
        return None
    def get_guiLock(self, guildID):
        return self.guiLocks[guildID]
    def get_channel(self, guildID):
        return self.channel[guildID]
    def get_nowplayingLock(self, guildID):
        return self.guiLocks[guildID]
    #SWITCH FUNCTIONS
    def switch_playing(self, guildID):
        if self.playing[guildID] is True:
            self.playing[guildID] = False
        else:
            self.playing[guildID] = True
    
    def switch_loop(self,guildID):  
        if self.loop[guildID] is True:
            self.loop[guildID] = False
        else:
            self.loop[guildID] = True
        return self.loop[guildID]

    def switch_random(self,guildID):
        if self.random[guildID] is True:
            self.random[guildID] = False
        else:
            self.random[guildID] = True
        return self.random[guildID]

    def empty_queue(self, guildID):
        if len(self.library[guildID]) == self.pos[guildID] or self.library[guildID] is None:
            return True
        else:
            False


    def pos_forward(self, guildID):
        if self.pos[guildID] is None:
            self.pos[guildID] = 0
            return self.pos[guildID]
        if self.pos[guildID] < len(self.library[guildID]):
            self.pos[guildID]+=1
            return self.pos[guildID]

    def pos_backward(self, guildID):
        if self.pos[guildID] is None:
            return self.pos[guildID]
        if self.pos[guildID] == 0:
            self.pos[guildID] = None
            return self.pos[guildID]
        self.pos[guildID]-=1
    
    def add_song(self, guildID, song):
        self.library[guildID].append(song)
        


    def reset(self, guildID):
        self.library [guildID] = []
        self.pos     [guildID] = None
        self.loop    [guildID] = False
        self.random  [guildID] = False

    def full_reset(self, guildID):
        self.library [guildID] = []
        self.pos     [guildID] = None
        self.loop    [guildID] = False
        self.random  [guildID] = False
        self.playing [guildID] = False