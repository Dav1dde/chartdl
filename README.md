chartdl
=======

Retrieves the german charts from mtv, downloads the corresponding videos
from youtube (with [youtube-dl](http://rg3.github.com/youtube-dl/)) 
and if wanted, extracts the audio with [mplayer](http://www.mplayerhq.hu/) and 
[lame](http://lame.sourceforge.net/) (flv to mp3).


## Usage

```
usage: chartdl.py [-h] [-c {album,dance,video,hitlist,black}]
                  [--database DATABASE] [--music-dir MUSIC_DIR] [-a] [-n] [-q]
                  [--username USERNAME] [--password PASSWORD]
                  [--youtube-dl YOUTUBE_DL] [--mplayer MPLAYER] [--lame LAME]

Retrieves the german charts from mtv downloads the corresponding videos from
youtube and if wanted, extracts the audio with mplayer and lame (flv to mp3).

optional arguments:
  -h, --help            show this help message and exit
  -c {album,dance,video,hitlist,black}, --category {album,dance,video,hitlist,black}
                        chart category
  --database DATABASE   path to music database, must be a valid sqlalchemy
                        database uri
  --music-dir MUSIC_DIR
                        path to save the downloaded videos/music
  -a, --audio-only      extracts the audio from the downloaded video and
                        encodes it with lame
  -n, --notify          enable the libnotify integration (requires pynotify)
  -q, --quiet           disable status information
  --username USERNAME   youtube username
  --password PASSWORD   youtube password
  --youtube-dl YOUTUBE_DL
                        path to youtube-dl executable
  --mplayer MPLAYER     path to mplayer executable
  --lame LAME           path to lame executable
```