from subprocess import check_call
import os

def download(url, path, username=None, password=None, audio_only=False):
    flv_path = path + '.flv'
    mp3_path = path + '.mp3'
        
    args = ['youtube-dl', '--no-continue', '-o', '-']
    
    if not username is None and not password is None:
        args.extend(['-u', username, '-p', password])
    
    args.append(url)
    
    with open(flv_path, 'wb') as f:
        check_call(args, stdout=f)
    
    if audio_only:
        check_call(['ffmpeg', '-y', '-i', flv_path, '-acodec', 'libmp3lame', '-ab', '128k', mp3_path])
        os.remove(flv_path)