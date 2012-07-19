from subprocess import CalledProcessError, check_call, Popen, PIPE
from urlparse import urlparse, parse_qs
from urllib import urlretrieve
from datetime import datetime
from Queue import Queue
import os.path
import os
import sys

from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from lxml import html

from chartdl.mtvgt import get_charts
from chartdl.db import Base, HitlistSong
from chartdl.exc import DownloadError, EncodingError
from chartdl.util import search_youtube, yield_lines

try:
    from mutagen.easyid3 import EasyID3
except ImportError:
    EasyID3 = None

try:
    import pynotify
except ImportError:
    pynotify = None
else:
    pynotify.init('chartdl')


DOWNLOAD_ICON = os.path.join(os.path.split(os.path.abspath(__file__))[0],
                             '..', 'src', 'download_icon.png') 

class ChartDownloader(object):
    def __init__(self, database_uri, music_dir, verbose=False, notify=False):
        self.database_uri = database_uri
        self.music_dir = music_dir
        self.verbose = verbose
        self.notify = notify
        self._output_fd = sys.stdout
        
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
            os.makedirs(path)
        
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
            
            video = search_youtube(chart)[video_result]
            video_url = video.get('href')
            video_id = parse_qs(urlparse(video_url).query)['v'][0]
            
            try:
                old = session.query(DB).filter(DB.video_id == video_id) \
                                       .filter(DB.week != song.week) \
                                       .filter(DB.position != song.position) \
                                       .one()
            except NoResultFound:
                pass
            else:
                song_path = os.path.join(self.music_dir, song.path)
                old_path = os.path.join(self.music_dir, old.path)
                suffix = '.mp3' if audio_only else '.flv'
                
                if os.path.exists(old_path + suffix):
                    os.link(old_path + suffix, song_path + suffix)
                    song.video_id = video_id
                    song.downloaded = True

            try:
                self.download(video_url, song,
                              username=username, password=password,
                              audio_only=audio_only)
            except CalledProcessError, e:
                self.log(e)
            except DownloadError, e:
                if e.is_gema_error:
                    chart_queue.put((chart, video_result+1))
            else:
                song.video_id = video_id
                song.downloaded = True
                    
            session.commit()
            
            self._notify_download_done(chart, notify, song.downloaded)

    def download(self, url, song,
                 username=None, password=None, audio_only=False):
        self.log('Downloading: {0!s}\n'.format(song))
        path = os.path.join(self.music_dir, song.path)
        flv_path = path + '.flv'
        mp3_path = path + '.mp3'
            
        args = ['youtube-dl', '--no-continue', '-o', '-']
        
        if not username is None and not password is None:
            args.extend(['-u', username, '-p', password])
        
        args.append(url)
    
        if audio_only:
            youtube_dl = Popen(args, stdout=PIPE, stderr=PIPE,
                               universal_newlines=True, bufsize=1)
            ffmpeg = Popen(['ffmpeg', '-y', '-i', 'pipe:0', '-acodec',
                            'libmp3lame', '-ab', '128k', mp3_path],
                           stdin=youtube_dl.stdout, stdout=PIPE, stderr=PIPE,
                           universal_newlines=True)
            youtube_dl.stdout.close()
            yt_stderr = [self.log(line) for line in
                         yield_lines(youtube_dl.stderr) if line.strip()]
            ff_stdout, ff_stderr = ffmpeg.communicate()
            youtube_dl.wait()
            
            if not youtube_dl.returncode == 0:
                raise DownloadError(yt_stderr[-1])
            if not ffmpeg.returncode == 0:
                raise EncodingError(ff_stderr.splitlines()[-1])
                        
            if not EasyID3 is None:
                audio = EasyID3(mp3_path)
                audio['title'] = song.title
                audio['artist'] = song.artist
                audio.save()
        else:
            with open(flv_path, 'wb') as f:
                check_call(args, stdout=f)
                
    def _notify_download_done(self, chart, notify, success):
        if self.notify and not pynotify is None:
            if chart['image'].get('src'):
                image, _ = urlretrieve(chart['image']['src'])
            else:
                image = DOWNLOAD_ICON
            
            status = 'finished' if success else 'failed'
            title = u'Download {}: #{}'.format(status, chart['position'])
            text = u'{} - {}'.format(chart['artist'], chart['title'])
            self.log(' '.join([title, text, '\n']))
            msg = pynotify.Notification(title, text, image)
            msg.show()
    
    def log(self, message):
        if self.verbose:
            msg = message.encode('utf-8') if isinstance(message, unicode) \
                    else message
            self._output_fd.write(msg)
        return message
        
        