import os.path

DATABASE_URI = 'sqlite:///music.db'
MUSIC_PATH = u'/home/dav1d/datein/musik/charts/'
DOWNLOAD_ICON = os.path.join(os.path.split(os.path.abspath(__file__))[0], '../src/download_icon.png') 