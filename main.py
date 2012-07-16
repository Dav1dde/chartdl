import chartdl
import os
import os.path

PATH = os.path.split(os.path.abspath(__file__))[0]

def main():
    yt_dl = os.path.join(PATH, 'youtube-dl')
    yt_dl_py = os.path.join(PATH, 'youtube_dl', '__main__.py')
    
    with open(yt_dl, 'w') as f:
        f.write('\n'.join(['#!/bin/sh', '', 'python2 {} $@'.format(yt_dl_py)]))
    os.chmod(yt_dl, 0755)
    
    os.environ['PATH'] += ':' + PATH 
    
    chartdl.download_charts('hitlist', username='ytdlalex', password='thisismypasswor')    

if __name__ == '__main__':
    main()