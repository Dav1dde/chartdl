from __future__ import unicode_literals

from contextlib import contextmanager
from itertools import izip_longest
import os.path
import sys

PATH = os.path.split(os.path.abspath(__file__))[0]


class ValidationError(Exception):
    def __init__(self, key, value, validator):
        self.key = key
        self.value = value
        self.validator = validator
        self.expected = {config_bool : 'boolean',
                         float : 'float',
                         int : 'int'}[self.validator]
    
    def __unicode__(self):
        return 'Unable to validate entry `{self.key}: {self.value}`, ' \
               'expected {self.expected}'.format(self=self)
    
    def __str__(self):
        return self.__unicode__().encode('utf-8')


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


def config_bool(b):
    if isinstance(b, basestring):
        if not b.lower() in ('yes', '1', 'true', 'on',
                             'no', '0', 'false', 'off'):
            raise ValueError
        return b.lower() in ('yes', '1', 'true', 'on')
    raise ValueError

def validate_config(items, booleans=None, floats=None, ints=None):
    validators = dict()
    if not booleans is None:
        validators.update(izip_longest(booleans, [], fillvalue=config_bool))
    if not floats is None:
        validators.update(izip_longest(floats, [], fillvalue=float))
    if not ints is None:
        validators.update(izip_longest(ints, [], fillvalue=int))
    null_validator = lambda x: x
    
    result = list()
    
    for key, value in items:
        validator = validators.get(key, null_validator)
        try:
            value = validator(value)
        except ValueError:
            raise ValidationError(key, value, validator)
        result.append((key, value))

    return result


def main():
    from ConfigParser import SafeConfigParser
    from argparse import ArgumentParser
    
    description = 'Retrieves the german charts from mtv ' \
                  'downloads the corresponding videos from youtube ' \
                  'and if wanted, extracts the audio with ' \
                  'mplayer and lame (flv to mp3).' \
    
    parser = ArgumentParser(description=description)
    parser.add_argument('--config', dest='config',
                        metavar='FILE',
                        help='specify config file')
    
    defaults = dict()
    if not '-h' in sys.argv and not '--help' in sys.argv: 
        arg, remaining_args = parser.parse_known_args()
        
        if not arg.config is None:
            config = SafeConfigParser()
            config.read(arg.config)
            try:
                items = validate_config(config.items('chartdl'),
                                        booleans=['audio_only', 'notify', 
                                                  'debug', 'quiet'])
            except ValidationError, e:
                parser.error(unicode(e))
            defaults.update(items)
    else:
        remaining_args = sys.argv
    
    parser.add_argument('-c', '--category', dest='category',
                        choices=['hitlist'],
                        default='hitlist',
                        help='chart category')
    parser.add_argument('--database', dest='database',
                        default='sqlite:///music.db',
                        help='path to music database, '
                             'must be a valid sqlalchemy database uri')
    parser.add_argument('--music-dir', dest='music_dir',
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
    parser.add_argument('--username', dest='username',
                        help='youtube username')
    parser.add_argument('--password', dest='password',
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
    parser.add_argument('--debug', dest='debug',
                        action='store_true',
                        help='shows every error')
    
    parser.set_defaults(**defaults)
    
    ns = parser.parse_args(remaining_args)

    if ns.debug:
        from chartdl import ChartDownloader
    else:
        with suppress_output(sys.stderr):
            from chartdl import ChartDownloader
    
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