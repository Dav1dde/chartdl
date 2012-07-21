from lxml import html

def get_charts(category):
    url, func = CHARTS[category]
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
                       'title' : info[0].text.strip(),
                       'artist' : info[1].text.strip()})
        
    return result

def _parse_video_charts(lxml_html):
    content = lxml_html.get_element_by_id('content')
    charts_list = content.find_class('charts_list')[0]
    
    result = list()
    for position, _, image, _, info in (e[0] for e in charts_list):
        result.append({'position' : int(position.text.strip()),
                       'image' :  dict(image.attrib),
                       'title' : info[0].text.strip(),
                       'artist' : info[1].text.strip()})
        
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


def main():
    from argparse import ArgumentParser
    import json
    
    try:
        import texttable
    except ImportError:
        texttable = None
    
    def make_table(charts, header=None):
        if header is None:
            header = ['position', 'last_position', 'artist', 'title']
        
        if not texttable is None:
            table = texttable.Texttable(max_width=80)
            table.set_deco(table.HEADER | table.HLINES | table.VLINES)
            table.set_cols_dtype(['i', 'i', 't', 't'])
            table.set_cols_width([10, 10, 25, 35])
            table.set_cols_align(['r', 'r', 'l', 'l'])
            table.set_cols_valign(['m', 'm', 'm', 'm'])
            table.header([h.replace('_', ' ') for h in header])
            for chart in charts:
                table.add_row([chart[k].encode('utf-8')
                                if isinstance(chart[k], unicode)
                                else chart[k]
                               for k in header])
            return table.draw()
        else:
            parser.error('Unable to output table, install `texttable`')
        
    parser = ArgumentParser(description='fetches the german music'
                                        ' charts from mtv')
    parser.add_argument('-c', '--category', dest='category',
                        choices=CHARTS.keys(),
                        default='hitlist',
                        help='chart category')
    parser.add_argument('-o', '--output', dest='output',
                        choices=['table', 'json'],
                        default='table',
                        help='output format')
    
    ns = parser.parse_args()
    
    charts = get_charts(ns.category)
    print {'table' : make_table, 'json' : json.dumps}[ns.output](charts)


if __name__ == '__main__':
    main()