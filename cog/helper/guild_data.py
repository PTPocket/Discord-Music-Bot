import discord
from datetime import datetime

def send_log(log_name, description, result = ''):
    time= str(datetime.now())
    print(f"{time} | Guild : {log_name} | {description} -> {result}")

class Guild_Music_Properties():
    def __init__(self):
        #SONG PLACEMENT
        self.queue   = {}
        self.history = {}
        self.current = {}
        #MUSIC PLAYER FEATURES
        self.loop    = {}
        self.random  = {}
        self.back    = {}
        self.mystery = {}
        self.shuffle = {}
        self.last_shuffle = {}
        #FOR GUI
        self.channel = {}
        self.message = {}

        #AutoDisconnect
        self.time   = {}


    def initialize(self, interaction:discord.Interaction):
        log_name = interaction.user.guild.name
        description = 'Initialized Variables for Guild'
        guild_id = interaction.user.guild.id
        if guild_id not in self.queue:
            self.queue  [guild_id] = []
            self.history[guild_id] = []
            self.time   [guild_id] = None
            self.current[guild_id] = None
            self.loop   [guild_id] = False
            self.back   [guild_id] = False
            self.random [guild_id] = False
            self.mystery[guild_id] = False
            self.shuffle[guild_id] = False
            self.last_shuffle[guild_id] = None
            self.channel[guild_id] = None
            self.message[guild_id] = None
            send_log(log_name, description )
    
    #RETRIEVE VALUES FUNCTIONS
    def get_last_played(self, guild_id):
        if self.history[guild_id] == []:
            return None
        else:
            return self.history[guild_id][0]
    # def get_all_songs(self, guild_id):
    #     past_songs = self.history[guild_id]
    #     next_songs =  self.queue[guild_id]
    #     if self.current[guild_id] is None:
    #         all_songs = past_songs+next_songs
    #         return all_songs
    #     else:
    #         next_songs.insert(0,self.current[guild_id])
    #         all_songs = past_songs+next_songs
    #         return all_songs
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
    def get_shuffle(self,guild_id):
        return self.shuffle[guild_id]
    def get_last_shuffle(self,guild_id):
        return self.last_shuffle[guild_id]
    def get_channel(self,guild_id):
        return self.channel[guild_id]
    def get_message(self,guild_id):
        return self.message[guild_id]
    def get_guild_ids(self):
        return self.queue.keys()
    def get_back(self, guild_id):
        return self.back[guild_id]
    def get_mystery(self, guild_id):
        return self.mystery[guild_id]
    def get_time(self, guild_id):
        return self.time[guild_id]
    
    
    #SET VALUE FUNCTIONS
    def set_queue_pos(self,guild_id, song, ind):
        self.queue[guild_id][ind] = song
    def set_queue(self,guild_id, queue):
        self.queue[guild_id] = queue
    def set_history(self,guild_id,history):
        self.history[guild_id] = history
    def set_current_song(self,guild_id, song):
        self.current[guild_id] = song
    def set_loop(self,guild_id, value):
        self.loop[guild_id] = value
    def set_random(self, guild_id, value):
        self.random[guild_id] = value
    def set_shuffle(self, guild_id, value):
        self.shuffle[guild_id] = value
    def set_last_shuffle(self,guild_id, value):
        self.last_shuffle[guild_id] = value
    def set_channel(self, guild_id, channel):
        self.channel[guild_id] = channel
    def set_message(self,guild_id, message):
        self.message[guild_id] = message
    def set_back(self,guild_id, value):
        self.back[guild_id] = value
    def set_idle_timestamp(self,guild_id):
        self.time[guild_id] = datetime.today()

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
            self.history[guild_id].insert(0,current_song)
            self.set_current_song(guild_id, None)
            return True
        return False
    
    def history_to_queue(self,guild_id):
        if self.empty_history(guild_id) is False:
            recent = self.history[guild_id].pop(0)
            self.prepend_to_queue(guild_id, recent)
            return True
        return False
    
    def empty_history(self, guild_id):
        if self.history[guild_id] == []:
            return True
        else: return False

    def empty_queue(self, guild_id):
        if self.queue[guild_id] == []:
            return True
        else: return False
    
    def delete_queue(self,guild_id):
        self.queue[guild_id] = []



    #FEATURES FUNCTIONS
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

    def flip_shuffle(self,guild_id):
        if self.get_shuffle(guild_id) is True:
            self.set_shuffle(guild_id, False)
        else:
            self.set_shuffle(guild_id, True)

    def reset_features(self, guild_id):
        self.loop[guild_id]   = False
        self.random[guild_id] = False
    
    def reset(self, guild_id):
        self.current_to_history(guild_id)
        self.queue[guild_id]  = []
        self.loop   [guild_id] = False
        self.back   [guild_id] = False
        self.random [guild_id] = False
        self.mystery[guild_id] = False
        self.shuffle[guild_id] = False
    
    def full_reset(self, guild_id):
        self.queue  [guild_id] = []
        self.history[guild_id] = []
        self.current[guild_id] = None
        self.loop   [guild_id] = False
        self.back   [guild_id] = False
        self.random [guild_id] = False
        self.mystery[guild_id] = False
        self.shuffle[guild_id] = False