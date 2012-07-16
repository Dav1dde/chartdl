from subprocess import check_call, Popen, PIPE
import os

def download(url, path, username=None, password=None, audio_only=False):
    flv_path = path + '.flv'
    mp3_path = path + '.mp3'
        
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
    else:
        with open(flv_path, 'wb') as f:
            check_call(args, stdout=f)
