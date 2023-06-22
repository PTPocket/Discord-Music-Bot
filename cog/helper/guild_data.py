import discord
from datetime import datetime


def send_log(log_name, description, result = ''):
    time= str(datetime.now())
    print(f"{time} | Guild : {log_name} | {description} -> {result}")

class Guild_Music_Properties():
    def __init__(self):
        self.voice   = {}
        #SONG PLACEMENT
        self.queue   = {}
        self.history = {}
        self.current = {}
        #MUSIC PLAYER FEATURES
        self.loop    = {}
        self.random  = {}
        self.back    = {}
        self.mystery = {}
        #FOR GUI
        self.channel = {}
        self.message = {}

    def initialize(self, interaction:discord.Interaction):
        log_name = interaction.user.guild.name
        description = 'Initialized Variables for Guild'
        guild_id = interaction.user.guild.id
        if guild_id not in self.voice:
            self.voice[guild_id]   = False
            self.queue[guild_id]   = []
            self.history[guild_id] = []
            self.current[guild_id] = None
            self.loop[guild_id]    = False
            self.back[guild_id]    = False
            self.random[guild_id]  = False
            self.mystery[guild_id] = False
            self.channel[guild_id] = None
            self.message[guild_id] = None
            send_log(log_name, description )
    
    #RETRIEVE VALUES FUNCTIONS
    def get_voice(self, guild_id):
        return self.voice[guild_id]
    def get_queue(self, guild_id):
        return self.queue[guild_id]
    def get_history(self, guild_id):
        return self.history[guild_id]
    def get_current_song(self,guild_id):
        return self.current[guild_id]
    def get_loop(self,guild_id):
        return self.loop[guild_id]
    def get_random(self,guild_id):
        return self.random[guild_id]
    def get_channel(self,guild_id):
        return self.channel[guild_id]
    def get_message(self,guild_id):
        return self.message[guild_id]
    def get_guild_ids(self):
        return self.voice.keys()
    def get_back(self, guild_id):
        return self.back[guild_id]
    def get_mystery(self, guild_id):
        return self.mystery[guild_id]
    #SET VALUE FUNCTIONS
    def set_voice(self, guild_id, voice):
        self.voice[guild_id] = voice
    def set_current_song(self,guild_id, song):
        self.current[guild_id] = song
    def set_loop(self,guild_id, value):
        self.loop[guild_id] = value
    def set_random(self, guild_id, value):
        self.random[guild_id] = value
    def set_channel(self, guild_id, channel):
        self.channel[guild_id] = channel
    def set_message(self,guild_id, message):
        self.message[guild_id] = message
    def set_back(self,guild_id, value):
        self.back[guild_id] = value

    #SONG MOVE FUNCTIONS
    def queue_song(self, guild_id, song):
        self.queue[guild_id].append(song)
    def prepend_to_queue(self, guild_id, song):
        self.queue[guild_id].insert(0,song)
    def queue_to_current(self, guild_id):
        if self.queue[guild_id] != []:
            self.current[guild_id] = self.queue[guild_id].pop(0)
            return True
        return False
    def current_to_queue(self, guild_id):
        if self.current[guild_id] is not None:
            self.queue[guild_id].insert(0,self.current[guild_id])
            self.set_current_song(guild_id, None)
            return True
        return False

    def current_to_history(self, guild_id):
        current_song = self.get_current_song(guild_id)
        if current_song is not None:
            self.history[guild_id].append(current_song)
            if len(self.history[guild_id]) > 30:
                self.history[guild_id] = self.history[guild_id][0:30]
            self.set_current_song(guild_id, None)
            return True
        return False
    
    def history_to_queue(self,guild_id):
        if self.empty_history(guild_id) is False:
            recent = self.history[guild_id].pop()
            self.prepend_to_queue(guild_id, recent)
            return True
        return False
        
    def flip_mystery(self, guild_id):
        if self.mystery[guild_id] is True:
            self.mystery[guild_id] = True
        else:
            self.mystery[guild_id] = False
    def flip_loop(self,guild_id):  
        if self.loop[guild_id] is True:
            self.loop[guild_id] = False
        else:
            self.loop[guild_id] = True

    def flip_random(self,guild_id):
        if self.random[guild_id] is True:
            self.random[guild_id] = False
        else:
            self.random[guild_id] = True
        return self.random[guild_id]

    def flip_back(self,guild_id):
        if self.get_back(guild_id) is True:
            self.set_back(guild_id, False)
        else:
            self.set_back(guild_id, True)

    def empty_history(self, guild_id):
        if self.history[guild_id] == []:
            return True
        else: return False

    def empty_queue(self, guild_id):
        if self.queue[guild_id] == []:
            return True
        else: return False

    #check_state
    def voice_in_action(self, guild_id):
        voice = self.get_voice(guild_id)
        if voice is None:
            return False
        if voice.is_playing() is True or voice.is_paused() is True:
            return True
        else:
            return False


    def reset_features(self, guild_id):
        self.loop[guild_id]   = False
        self.random[guild_id] = False
    def soft_reset(self, guild_id):
        self.voice[guild_id]   = False
        self.queue[guild_id]  = []
        self.history[guild_id] = []
        self.loop[guild_id]   = False
        self.random[guild_id] = False
        self.loop[guild_id]    = False
        self.back[guild_id]    = False
        self.mystery[guild_id] = False

    def hard_reset(self, guild_id):
        
        self.queue[guild_id]   = []
        self.history[guild_id] = []
        self.loop[guild_id]    = False
        self.back[guild_id]    = False
        self.random[guild_id]  = False
        self.mystery[guild_id] = False
        
        self.current[guild_id] = None
        self.channel[guild_id] = None
        self.message[guild_id] = None