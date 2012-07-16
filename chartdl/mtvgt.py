from lxml import html

def get_charts(type_):
    url, func = CHARTS[type_]
    return func(html.parse(url).getroot())

def _parse_charts(lxml_html):
    content = lxml_html.get_element_by_id('content')
    charts_list = content.find_class('charts_list')[0]
    
    result = list()
    for position, _, last_position, image, _, info in (e[0] for e in charts_list):
        result.append({'position' : int(position.text.strip()),
                       'last_position' : _last_position_conv(last_position \
                                                           .text.strip()),
                       'image' :  dict(image.attrib),
                       'title' : info[1].text.strip(),
                       'artist' : info[0].text.strip()})
        
    return result

def _parse_video_charts(lxml_html):
    content = lxml_html.get_element_by_id('content')
    charts_list = content.find_class('charts_list')[0]
    
    result = list()
    for position, _, image, _, info in (e[0] for e in charts_list):
        result.append({'position' : int(position.text.strip()),
                       'image' :  dict(image.attrib),
                       'title' : info[1].text.strip(),
                       'artist' : info[0].text.strip()})
        
    return result
    

def _last_position_conv(pos):
    return -1 if pos == 'new' else int(pos) 


CHARTS = {'album' : ('http://www.mtv.de/charts/4-album-top-50',
                     _parse_charts),
          'hitlist' : ('http://www.mtv.de/charts/5-hitlist-germany-top-100',
                       _parse_charts),
          'dance' : ('http://www.mtv.de/charts/6-dance-charts',
                     _parse_charts),
          'black' : ('http://www.mtv.de/charts/9-deutsche-black-charts',
                     _parse_charts),
          'video' : ('http://www.mtv.de/musikvideos/11-mtv-de-videocharts/playlist',
                     _parse_video_charts)}


if __name__ == '__main__':
    import json
    
    hitlist = get_charts('hitlist')
    
    print json.dumps(hitlist)
