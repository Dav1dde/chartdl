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
        
def main():
    with suppress_output(sys.stderr):
        from chartdl import ChartDownloader
    
    yt_dl = os.path.join(PATH, 'youtube-dl')
    yt_dl_py = os.path.join(PATH, 'youtube_dl', '__main__.py')
    
    with open(yt_dl, 'w') as f:
        f.write('\n'.join(['#!/bin/sh', '',
                           'python2 {} $@'.format(yt_dl_py)]))
    os.chmod(yt_dl, 0755)
    
    os.environ['PATH'] += ':' + PATH
    
    if len(sys.argv) == 3:
        _, username, password = sys.argv
    else:
        username, password = None, None
    
    chart_downloader = ChartDownloader(u'sqlite:///music.db',
                                       u'/home/dav1d/datein/musik/charts/',
                                       notify=True,
                                       verbose=True)
    chart_downloader.download_charts('hitlist',
                                     username=username,
                                     password=password)    

if __name__ == '__main__':
    main()