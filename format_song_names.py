import os
from tinytag import TinyTag

LIBRARY_PATH = 'S:\\music\\Music_Directory'

def format_song_names():
    name_list = os.listdir(LIBRARY_PATH)
    for name in name_list:
        filetype = name.split('.')[1]
        if ('.jpg' in name) or ('.png' in name):
            os.remove(f'{LIBRARY_PATH}\\{name}')
            continue
        path = LIBRARY_PATH+'\\'+name
        song_metadata = TinyTag.get(path)
        title = song_metadata.title
        author = song_metadata.artist
        if title is None or author is None:
            new_path = f'{LIBRARY_PATH}\\TESTFormatted\\{name}.{filetype}'
            if name[0].isalpha() is True:
                if os.path.isfile(path):
                    os.rename(path, new_path)
                continue
            copy = name
            while copy[0].isalpha() is False:
                copy = copy[1::]
            if copy[0] == '.':
                continue
            try:
                os.rename(path,new_path)
                print(f'Renamed file : {name} -> {copy}')
            except: 
                try:
                    os.remove(f'{LIBRARY_PATH}\\{name}')
                    print(f'Removed Duplicate : {name}')
                except Exception as e: print(e)
        filename = f'{title} by {author}'
        new_path = f'{LIBRARY_PATH}\\TESTFormatted\\{filename}.{filetype}'
        os.rename(path,new_path)



if __name__ == '__main__':
    format_song_names()
