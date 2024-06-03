import os

LIBRARY_PATH = 'S:\\music'

def format_song_names():
    name_list = os.listdir(LIBRARY_PATH)
    for name in name_list:

        if name[0].isalpha() is True:
            if os.path.isfile(f'{LIBRARY_PATH}\\{name}'):
                os.rename(f'{LIBRARY_PATH}\\{name}', f'{LIBRARY_PATH}\\Formated\\{name}')
            continue
        if ('.jpg' in name) or ('.png' in name):
            os.remove(f'{LIBRARY_PATH}\\{name}')
            continue
        copy = name
        while copy[0].isalpha() is False:
            copy = copy[1::]
        if copy[0] == '.':
            continue
        try:
            os.rename(f'{LIBRARY_PATH}\\{name}',f'{LIBRARY_PATH}\\Formated\\{copy}')
            print(f'Renamed file : {name} -> {copy}')
        except: 
            try:
                os.remove(f'{LIBRARY_PATH}\\{name}')
                print(f'Removed Duplicate : {name}')
            except Exception as e: print(e)
        


if __name__ == '__main__':
    format_song_names()
