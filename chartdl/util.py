from __future__ import unicode_literals

from urllib import quote_plus
from datetime import date
import re

from lxml import html


YT_SEARCH_URL = 'http://www.youtube.com/results?search_type=videos' \
                        '&search_query={query}'
ETA_RE = r'\[download\]\s+(?P<progress>\d{1,3}\.\d{1,2}%)\s+of\s+' \
          '(?P<size>\d+\.\d{1,2}\w+)\s+at\s+(?P<speed>\d+\.\d+\s*\w/\w)' \
          '\s+ETA\s+(?P<eta>\d+:\d{2})\n?'
ETA_RE = re.compile(ETA_RE, re.IGNORECASE)

def search_youtube(song):
    query = quote_plus(' '.join([song.artist, song.title]).encode('utf-8')) \
                       .decode('utf-8')
    
    search_url = YT_SEARCH_URL.format(query=query)

    root = html.parse(search_url).getroot()
    root.make_links_absolute('http://www.youtube.com/')
    videos = root.cssselect('a.yt-uix-sessionlink')
    
    return videos

def yield_lines(fd):
    while True:
        line = fd.readline()
        if not line:
            break
        
        yield line

def ytdl_filter(line):
    if 'destination' in line.lower():
        return ''
    if ETA_RE.match(line):
        return '\r' + line.rstrip()
    return line

# assume every friday new charts arrive on the website
def chart_calendarweek():
    today = date.today()
    week = today.isocalendar()[1]
    
    if today.isoweekday() >= 5: # friday
        week += 1
    return week