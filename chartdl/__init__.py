from __future__ import unicode_literals

from subprocess import CalledProcessError, check_call, Popen, PIPE
from tempfile import NamedTemporaryFile
from urlparse import urlparse, parse_qs
from urllib import urlretrieve
from Queue import Queue
import os.path
import os
import sys

from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from lxml import html

from chartdl.mtvgt import get_charts
from chartdl.db import Base, HitlistSong, DanceSong, BlackSong
from chartdl.exc import DownloadError, EncodingError
from chartdl.util import (search_youtube, yield_lines,
                          ytdl_filter, chart_calendarweek)

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
        
        self.youtube_dl = 'youtube-dl'
        self.mplayer = 'mplayer'
        self.lame = 'lame'
        
        self.engine = create_engine(self.database_uri, convert_unicode=True)
        self.Session = sessionmaker(bind=self.engine)
        Base.metadata.create_all(self.engine)

    def download_charts(self, category, username=None, password=None,
                        audio_only=False, notify=False):
        action = False
        session = self.Session()
        
        DB = {'hitlist' : HitlistSong,
              'dance' : DanceSong,
              'black' : BlackSong}[category]
        
        charts = list(get_charts(category))
        
        # TODO: 
        #  friday and no new charts list
        calendar_week = chart_calendarweek()
        self.log('Calendar week: {}'.format(calendar_week))
        query = session.query(DB).filter(DB.week == calendar_week)
        if not all(song == charts[song.position-1] for song in query):
            calendar_week += 1
            self.log('/{}.'.format(calendar_week))
        self.log('\n\n')
        
        path = os.path.join(self.music_dir, category, str(calendar_week))
        if not os.path.isdir(path):
            os.makedirs(path)
    
        for chart in charts:
            query = session.query(DB).filter(DB.week == calendar_week) \
                                     .filter(DB.position == chart['position'])
            try:
                song = query.one()
            except NoResultFound:
                song = DB.from_chart(chart)
                song.week = calendar_week
                song.rebuild_path()
                session.add(song)
            else:
                continue
        
        chart_queue = Queue()
        [chart_queue.put((song, 0)) for song in session.query(DB).filter(DB.downloaded == False)]
        
        while not chart_queue.empty():
            song, video_result = chart_queue.get()

            self.log('Downloading #{0} (Week {1}): {2!s}.\n'
                     .format(song.position, song.week, song))
            
            video = search_youtube(song)[video_result]
            video_url = video.get('href')
            
            try:
                video_id = parse_qs(urlparse(video_url).query)['v'][0]
            except KeyError:
                self.log('Unable to retrieve url from youtube: {}'.format(video_url))
                continue
            old = session.query(DB).filter(DB.video_id == video_id) \
                                   .filter(DB.week != song.week) \
                                   .first()

            if not old is None:
                suffix = '.mp3' if audio_only else '.flv'
                song_path = os.path.join(self.music_dir, song.path) + suffix
                old_path = os.path.join(self.music_dir, old.path) + suffix
                
                if os.path.exists(old_path):
                    self.log('File does already exist, creating hardlink.\n')
                    if not os.path.exists(song_path):
                        os.link(old_path, song_path)
                    song.video_id = video_id
                    song.downloaded = True
            else:
                try:
                    self.download(video_url, song,
                                  username=username, password=password,
                                  audio_only=audio_only)
                except CalledProcessError, e:
                    self.log(e.message)
                except DownloadError, e:
                    if e.is_gema_error:
                        chart_queue.put((song, video_result+1))
                else:
                    song.video_id = video_id
                    song.downloaded = True
                    
            action = True
            session.commit()
            self._notify_download_done(song, notify)
        
        if not action:
            self.log('Nothing to do.\n')

    def download(self, url, song,
                 username=None, password=None, audio_only=False):
        path = os.path.join(self.music_dir, song.path)
        flv_path = path + '.flv'
        mp3_path = path + '.mp3'

        args = [self.youtube_dl, '--no-continue', '-o', '-']
        if not username is None and not password is None:
            args.extend(['-u', username, '-p', password])
        args.append(url)
     
        if audio_only:
            tempfile = NamedTemporaryFile(delete=False)
            tempfile.close()
            
            youtube_dl = Popen(args, stdout=PIPE, stderr=PIPE,
                               universal_newlines=True)
            mplayer = Popen([self.mplayer, '-', '-really-quiet',
                             '-vc', 'null', '-vo', 'null',
                             '-ao', 'pcm:fast:file=' + tempfile.name],
                            stdin=youtube_dl.stdout, stdout=PIPE, stderr=PIPE,
                            universal_newlines=True)
            youtube_dl.stdout.close()
            yt_stderr = [self.log(ytdl_filter(line)) for line in
                         yield_lines(youtube_dl.stderr) if line.strip()]
            youtube_dl.stderr.close()
            mp_stdout, mp_stderr = mplayer.communicate()
            youtube_dl.wait()
            
            if not youtube_dl.returncode == 0:
                raise DownloadError(yt_stderr[-1])
            if not mplayer.returncode == 0:
                raise EncodingError(mp_stderr.splitlines()[-1])
            
            self.log('\nStarting lame.\n')
            lame = Popen([self.lame, '-h', tempfile.name, mp3_path],
                         stdout=PIPE, stderr=PIPE)
            lame_stdout, lame_stderr = lame.communicate()
                        
            if not lame.returncode == 0:
                raise EncodingError(lame_stderr.splitlines()[-1])
            self.log('Encoding finished.\n')
            
            if not EasyID3 is None:
                audio = EasyID3()
                audio['title'] = song.title
                audio['artist'] = song.artist
                audio.save(mp3_path)
        else:
            with open(flv_path, 'wb') as f:
                youtube_dl = Popen(args, stdout=f, stderr=PIPE,
                                   universal_newlines=True)
                yt_stderr = [self.log(ytdl_filter(line)) for line in
                             yield_lines(youtube_dl.stderr) if line.strip()]
                youtube_dl.communicate()
                
            if not youtube_dl.returncode == 0:
                raise DownloadError(yt_stderr[-1])
                
    def _notify_download_done(self, song, notify):
        if self.notify and not pynotify is None:
            if song.image_url:
                image, _ = urlretrieve(song.image_url)
            else:
                image = DOWNLOAD_ICON
            
            status = 'finished' if song.downloaded else 'failed'
            title = 'Download {}: #{}/{}'.format(status, song.position, song.week)
            text = '{} - {}'.format(song.artist, song.title)
            self.log(' '.join([title, text, '\n\n']))
            msg = pynotify.Notification(title, text, image)
            msg.show()
    
    def log(self, message):
        if self.verbose:
            self._output_fd.write(message.encode('utf-8'))
            self._output_fd.flush()
        return message
        
        