from chartdl.mtvgt import get_charts
from chartdl.ytdl import download
from chartdl.db import init_db, Session, HitlistSong
from chartdl.config import MUSIC_PATH, DOWNLOAD_ICON

from sqlalchemy.orm.exc import NoResultFound
from urllib import quote_plus
from lxml import html
from datetime import datetime
from subprocess import CalledProcessError
from os import makedirs
import os.path

try:
    import pynotify
except ImportError:
    pynotify = None


init_db()

def download_charts(type_, username=None, password=None, audio_only=True, notify=True):
    if notify and not pynotify is None:
        pynotify.init('chartdl')
    
    session = Session()
    
    calendar_week = datetime.now().isocalendar()[1]
    
    charts = get_charts(type_)
    if type_ == 'hitlist':
        DB = HitlistSong
    else:
        raise ValueError
    
    path = os.path.join(MUSIC_PATH, type_, str(calendar_week))
    if not os.path.isdir(path):
        makedirs(path)
    
    for chart in charts:
        print chart
        
        query = session.query(DB).filter(DB.week == calendar_week) \
                                 .filter(DB.position == chart['position'])
        try:
            song = query.one()
        except NoResultFound:
            song = DB.from_chart(chart)
            session.add(song)
        
        if song.downloaded:
            continue
        
        
        url = u'http://www.youtube.com/results?search_query='.encode('utf-8') + \
                quote_plus(' '.join([chart['artist'].encode('utf-8'),
                                     chart['title'].encode('utf-8')]))

        root = html.parse(url).getroot()
        root.make_links_absolute('http://www.youtube.com/')
        videos = root.cssselect('a.yt-uix-sessionlink')
        
        if videos:
            video_url = videos[0].get('href')
            
            try:
                download(video_url, song.path, username=username, password=password,
                         audio_only=audio_only)
            except CalledProcessError:
                pass
            else:
                song.downloaded = True
                
        session.commit()
        
        if notify and not pynotify is None:
            msg = pynotify.Notification('Download finished: #{}'.format(chart['position']),
                                        '{} - {}'.format(chart['artist'],
                                                         chart['title']),
                                        DOWNLOAD_ICON)
            msg.show()