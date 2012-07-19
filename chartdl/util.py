from urllib import quote_plus
from lxml import html
import re


YT_SEARCH_URL = 'http://www.youtube.com/results?search_type=videos' \
                        '&search_query={query}'
ETA_RE = r'\[download\]\s+(?P<progress>\d{1,3}\.\d{1,2}%)\s+of\s+' \
          '(?P<size>\d+\.\d{1,2}\w+)\s+at\s+(?P<speed>\d+\.\d+\s*\w/\w)' \
          '\s+ETA\s+(?P<eta>\d+:\d{2})\n?'
ETA_RE = re.compile(ETA_RE, re.IGNORECASE)

def search_youtube(chart):
    query = quote_plus(' '.join([chart['artist'].encode('utf-8'),
                                 chart['title'].encode('utf-8')])) \
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
    if ETA_RE.match(line):
        return '\r' + line.rstrip()
    return line