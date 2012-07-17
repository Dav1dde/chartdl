from chartdl import ChartDownloader
import os
import os.path
import sys

PATH = os.path.split(os.path.abspath(__file__))[0]

def main():
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
                                       u'/home/dav1d/datein/musik/charts/')
    chart_downloader.download_charts('hitlist',
                                     username=username,
                                     password=password)    

if __name__ == '__main__':
    main()