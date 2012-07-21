from contextlib import contextmanager
import os
import os.path
import sys

PATH = os.path.split(os.path.abspath(__file__))[0]

# from https://gist.github.com/3151059
@contextmanager
def suppress_output(fd):
    '''
    Suppress output to the given ``fd``::

       with suppress_fd(sys.stderr):
           # in this block any output to standard error is suppressed

    ``fd`` is an integral file descriptor, or any object with a ``fileno()``
    method.
    '''
    if hasattr(fd, 'fileno'):
        if hasattr(fd, 'flush'):
            fd.flush()
        fd = fd.fileno()

    oldfd = os.dup(fd)
    try:
        devnull = os.open(os.devnull, os.O_WRONLY)
        try:
            os.dup2(devnull, fd)
        finally:
            os.close(devnull)
        yield
        os.dup2(oldfd, fd)
    finally:
        os.close(oldfd)
        
def youtube_dl_launcher(path):
    if sys.platform == 'win32':
        starter = '\n'.join(['@echo off', '', '{} {} %*'])
    else:
        starter = '\n'.join(['#!/bin/sh', '', '{} {} $@'])
    return starter.format(sys.executable, path)

def make_youtube_dl_launcher():
    yt_dl = os.path.join(PATH, 'youtube-dl')
    yt_dl_py = os.path.join(PATH, 'youtube_dl', '__main__.py')
    
    with open(yt_dl, 'w') as f:
        f.write(youtube_dl_launcher(yt_dl_py))
    os.chmod(yt_dl, 0755)
    
    return yt_dl
    

def main():
    from argparse import ArgumentParser
    
    with suppress_output(sys.stderr):
        from chartdl import ChartDownloader
    import chartdl.mtvgt
    
    description = 'Retrieves the german charts from mtv ' \
                  'downloads the corresponding videos from youtube ' \
                  'and if wanted, extracts the audio with ' \
                  'mplayer and lame (flv to mp3).' \
    
    parser = ArgumentParser(description=description)
    parser.add_argument('-c', '--category', dest='category',
                        choices=chartdl.mtvgt.CHARTS.keys(),
                        default='hitlist',
                        help='chart category')
    parser.add_argument('-d', '--database', dest='database',
                        default='sqlite:///music.db',
                        help='path to music database, '
                             'must be a valid sqlalchemy database uri')
    parser.add_argument('-m', '--music-dir', dest='music_dir',
                        default='./downloads',
                        help='path to save the downloaded videos/music')
    parser.add_argument('-a', '--audio-only', dest='audio_only',
                        action='store_true',
                        help='extracts the audio from the '
                             'downloaded video and encodes it with lame')
    parser.add_argument('-n', '--notify', dest='notify',
                        action='store_true',
                        help='enable the libnotify integration '
                             '(requires pynotify)')
    parser.add_argument('-q', '--quiet', dest='quiet',
                        action='store_true',
                        help='disable status information')
    parser.add_argument('-u', '--username', dest='username',
                        help='youtube username')
    parser.add_argument('-p', '--password', dest='password',
                        help='youtube password')
    parser.add_argument('--youtube-dl', dest='youtube_dl',
                        default=None,
                        help='path to youtube-dl executable')
    parser.add_argument('--mplayer', dest='mplayer',
                        default='mplayer',
                        help='path to mplayer executable')
    parser.add_argument('--lame', dest='lame',
                        default='lame',
                        help='path to lame executable')
    
    ns = parser.parse_args()
    
    yt_dl = ns.youtube_dl
    if yt_dl is None:       
        yt_dl = make_youtube_dl_launcher()
    
    chart_downloader = ChartDownloader(ns.database, ns.music_dir,
                                       notify=ns.notify, verbose=not ns.quiet)
    chart_downloader.youtube_dl = yt_dl
    chart_downloader.mplayer = ns.mplayer
    chart_downloader.lame = ns.lame
    
    chart_downloader.download_charts(ns.category,
                                     username=ns.username,
                                     password=ns.password,
                                     audio_only=ns.audio_only)    

if __name__ == '__main__':
    main()