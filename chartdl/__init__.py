from chartdl.mtvgt import get_charts
from chartdl.db import Base, HitlistSong
from chartdl.exc import DownloadError, EncodingError

from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from subprocess import check_call, Popen, PIPE
from urllib import urlretrieve, quote_plus
from lxml import html
from Queue import Queue
from datetime import datetime
from subprocess import CalledProcessError
from os import makedirs
import os.path

try:
    from mutagen.easyid3 import EasyID3
except ImportError:
    EasyID3 = None

try:
    import pynotify
except ImportError:
    pynotify = None
    
if not pynotify is None:
    pynotify.init('chartdl')


DOWNLOAD_ICON = os.path.join(os.path.split(os.path.abspath(__file__))[0],
                             '../src/download_icon.png') 
YT_SEARCH_URL = 'http://www.youtube.com/results?search_type=videos' \
                        '&search_category=10&uni=3?search_query={query}'


class ChartDownloader(object):
    def __init__(self, database_uri, music_dir):
        self.database_uri = database_uri
        self.music_dir = music_dir
        
        self.engine = create_engine(self.database_uri, convert_unicode=True)
        self.Session = sessionmaker(bind=self.engine)
        Base.metadata.create_all(self.engine)

    def download_charts(self, type_, username=None, password=None,
                        audio_only=True, notify=False):
        session = self.Session()
        
        calendar_week = datetime.now().isocalendar()[1]
        
        charts = get_charts(type_)
        chart_queue = Queue()
        [chart_queue.put((chart, 0)) for chart in charts]
        if type_ == 'hitlist':
            DB = HitlistSong
        else:
            raise ValueError
        
        path = os.path.join(self.music_dir, type_, str(calendar_week))
        if not os.path.isdir(path):
            makedirs(path)
        
        while not chart_queue.empty():
            chart, video_result = chart_queue.get()            
            query = session.query(DB).filter(DB.week == calendar_week) \
                                     .filter(DB.position == chart['position'])
            try:
                song = query.one()
            except NoResultFound:
                song = DB.from_chart(chart)
                session.add(song)
            else:
                if song.downloaded:
                    continue
            
            video = self._search_youtube(chart)[video_result]
            video_url = video.get('href')

            try:
                self.download(video_url, song,
                              username=username, password=password,
                              audio_only=audio_only)
            except CalledProcessError:
                pass
            except DownloadError, e:
                if e.is_gema_error:
                    print 'gema error, again', video_result
                    chart_queue.put((chart, video_result+1))
            else:
                song.downloaded = True
                    
            session.commit()
            
            self._notify_download_done(chart, notify, song.downloaded)

    def download(self, url, song, username=None, password=None, audio_only=False):
        flv_path = song.path + '.flv'
        mp3_path = song.path + '.mp3'
            
        args = ['youtube-dl', '--no-continue', '-o', '-']
        
        if not username is None and not password is None:
            args.extend(['-u', username, '-p', password])
        
        args.append(url)
    
        if audio_only:
            youtube_dl = Popen(args, stdout=PIPE, stderr=PIPE)
            ffmpeg = Popen(['ffmpeg', '-y', '-i', 'pipe:0', '-acodec',
                            'libmp3lame', '-ab', '128k', mp3_path],
                           stdin=youtube_dl.stdout, stdout=PIPE, stderr=PIPE)
            youtube_dl.stdout.close()
            ff_stdout, ff_stderr = ffmpeg.communicate()
            youtube_dl.wait()
            
            if not youtube_dl.returncode == 0:
                raise DownloadError(youtube_dl.stderr.readlines()[-1])
            if not ffmpeg.returncode == 0:
                raise EncodingError(ff_stderr.split()[-1])
            
            if not EasyID3 is None:
                audio = EasyID3(mp3_path)
                audio['title'] = song.title
                audio['artist'] = song.artist
                audio.save()
        else:
            with open(flv_path, 'wb') as f:
                check_call(args, stdout=f)
        
    def _search_youtube(self, chart):
        query = quote_plus(' '.join([chart['artist'].encode('utf-8'),
                                     chart['title'].encode('utf-8')])) \
                           .decode('utf-8')
        
        search_url = YT_SEARCH_URL.format(query=query)
    
        root = html.parse(search_url).getroot()
        root.make_links_absolute('http://www.youtube.com/')
        videos = root.cssselect('a.yt-uix-sessionlink')
        
        return videos
    
    def _notify_download_done(self, chart, notify, success):
        if notify and not pynotify is None:
            if chart['image'].get('src'):
                image, _ = urlretrieve(chart['image']['src'])
            else:
                image = DOWNLOAD_ICON
            
            status = 'finished' if success else 'failed'
            title = u'Download {}: #{}'.format(status, chart['position'])
            text = u'{} - {}'.format(chart['artist'], chart['title'])
            msg = pynotify.Notification(title, text, image)
            msg.show()
        
        
        