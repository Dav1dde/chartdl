from subprocess import check_call, Popen, PIPE

try:
    from mutagen.easyid3 import EasyID3
except ImportError:
    EasyID3 = None


def download(url, song, username=None, password=None, audio_only=False):
    flv_path = song.path + '.flv'
    mp3_path = song.path + '.mp3'
        
    args = ['youtube-dl', '--no-continue', '-o', '-']
    
    if not username is None and not password is None:
        args.extend(['-u', username, '-p', password])
    
    args.append(url)

    if audio_only:
        youtube_dl = Popen(args, stdout=PIPE)
        ffmpeg = Popen(['ffmpeg', '-y', '-i', 'pipe:0', '-acodec',
                        'libmp3lame', '-ab', '128k', mp3_path],
                       stdin=youtube_dl.stdout)
        youtube_dl.stdout.close()
        ffmpeg.communicate()
        
        if not EasyID3 is None:
            audio = EasyID3(mp3_path)
            audio['title'] = song.title
            audio['artist'] = song.artist
            audio.save()
    else:
        with open(flv_path, 'wb') as f:
            check_call(args, stdout=f)
