from __future__ import unicode_literals, print_function

from urllib2 import urlopen
from contextlib import closing

from lxml import html
try:
    import texttable
except ImportError:
    texttable = None


def get_charts(category):
    url, func = CHARTS[category]

    with closing(urlopen(url)) as source:
        root = html.fromstring(source.read().decode('utf-8'), base_url=url)
        return func(root)


def _find_chart_list(tree):
    return tree.cssselect('#content .charts_list > li > a:first-child')


def _parse_charts(tree):
    for chart in _find_chart_list(tree):
        position, _, last_position, image, _, info = chart
        yield {'position': int(position.text.strip()),
               'last_position': _last_position(last_position.text.strip()),
               'image': _image(image.attrib),
               'title': unicode(info[0].text).strip(),
               'artist': unicode(info[1].text).strip()}


def _parse_video_charts(tree):
    for chart in _find_chart_list(tree):
        position, _, image, _, info = chart
        yield {'position': int(position.text.strip()),
               'image': _image(image.attrib),
               'title': unicode(info[0].text).strip(),
               'artist': unicode(info[1].text).strip()}


def _last_position(pos):
    return -1 if pos == 'new' else int(pos)


def _image(attrib):
    return {'alt': unicode(attrib['alt']),
            'height': int(attrib['height']),
            'width': int(attrib['width']),
            'src': unicode(attrib['src'])}


CHARTS = {'album': ('http://www.mtv.de/charts/4-album-top-50',
                    _parse_charts),
          'hitlist': ('http://www.mtv.de/charts/5-hitlist-germany-top-100',
                      _parse_charts),
          'dance': ('http://www.mtv.de/charts/6-dance-charts',
                    _parse_charts),
          'black': ('http://www.mtv.de/charts/9-deutsche-black-charts',
                    _parse_charts),
          'video': ('http://www.mtv.de/musikvideos/11-mtv-de-videocharts/playlist',
                    _parse_video_charts)}


def make_table(charts, header=None):
    if header is None:
        header = ['position', 'last_position', 'artist', 'title']

    table = texttable.Texttable(max_width=80)
    table.set_deco(table.HEADER | table.HLINES | table.VLINES)
    table.set_cols_dtype(['i', 'i', 't', 't'])
    table.set_cols_width([10, 10, 25, 35])
    table.set_cols_align(['r', 'r', 'l', 'l'])
    table.set_cols_valign(['m', 'm', 'm', 'm'])
    table.header([h.replace('_', ' ') for h in header])
    for chart in charts:
        table.add_row([unicode(chart[k]).encode('utf-8')
                       for k in header])
    return table.draw()


def main():
    from argparse import ArgumentParser
    from itertools import islice
    import json

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
    parser.add_argument('-n', '--number', dest='number',
                        default=100,
                        type=int,
                        help='number of shown charts')
    parser.add_argument('-r', '--reversed', dest='reversed',
                        action='store_true',
                        help='reverse list')

    args = parser.parse_args()

    if args.output == 'table' and texttable is None:
        parser.error('Unable to output table, install `texttable`')

    all_charts = get_charts(args.category)
    if args.reversed:
        all_charts = reversed(list(all_charts))
    charts = islice(all_charts, 0, args.number)
    
    format_charts = {'table': make_table, 'json': json.dumps}[args.output]
    print(format_charts(charts))


if __name__ == '__main__':
    main()