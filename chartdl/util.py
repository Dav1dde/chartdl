from lxml import html
from urllib import quote_plus


YT_SEARCH_URL = 'http://www.youtube.com/results?search_type=videos' \
                        '&search_category=10&uni=3&search_query={query}'

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