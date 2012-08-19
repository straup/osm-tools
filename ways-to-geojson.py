#!/usr/bin/env python

import sys
import urllib
import xml.etree.ElementTree as xml
import json
import re
import logging

def write_json(data, path, precision=6, indent=False):

    logging.debug("write data to %s" % path)

    kwargs = {}

    if indent:
        kwargs['indent'] = 2

    float_pat = re.compile(r'^-?\d+\.\d+(e-?\d+)?$')

    fh = open(path, 'w')

    encoder = json.JSONEncoder(**kwargs)
    encoded = encoder.iterencode(data)
    
    format = '%.' + str(precision) + 'f'
    
    for token in encoded:
        if float_pat.match(token):
            fh.write(format % float(token))
        else:
            fh.write(token)

    fh.close()

def nodes_for_way(id):

    url = 'http://www.openstreetmap.org/api/0.6/way/%s' % id
    logging.debug("fetch way %s" % url)

    nodes = []

    rsp = urllib.urlopen(url)
    tree = xml.fromstring(rsp.read())

    for nd in tree.findall('*//nd'):
        attrs = nd.attrib
        nodes.append(attrs['ref'])

    return nodes

def coords_for_node(id):

    url = 'http://www.openstreetmap.org/api/0.6/node/%s' % id
    logging.debug("fetch node %s" % url)

    rsp = urllib.urlopen(url)
    tree = xml.fromstring(rsp.read())

    node = tree.find('node')
    attrs = node.attrib

    return (
        float(attrs['lon']),
        float(attrs['lat'])
        )

def ways_to_geojson(ids):

    features = []

    for id in ids:

        nodes = nodes_for_way(id)
        coords = []

        swlat = None
        swlon = None
        nelat = None
        nelon = None

        for n in nodes:

            pt = coords_for_node(n)
            coords.append(pt)

            if swlat:
                swlat = min(swlat, pt[1])
            else:
                swlat = pt[1]                

            if swlon:
                swlon = min(swlat, pt[0])
            else:
                swlon = pt[0]   

            if nelat:
                nelat = max(nelat, pt[1])
            else:
                nelat = pt[1]

            if nelon:
                nelon = max(nelon, pt[0])
            else:
                nelon = pt[0]

        bbox = [ swlon, swlat, nelon, nelat ]

        # TO DO: check to see if this a closed set of
        # coordinates or not...

        type = 'Polygon'

        properties = {
            'id': id
            }

        geom = {
            'type': type,
            'coordinates': [ coords ]
            }
    
        feature = {
            'type': 'Feature',
            'bbox': bbox,
            'properties': properties,
            'geometry' : geom
            }
    
        features.append(feature)

    geojson = {
        'type': 'FeatureCollection',
        'features': features
        }

    return geojson

if __name__ == '__main__':

    import optparse

    parser = optparse.OptionParser(usage="python ways-to-geojson.py --options way-ids")

    parser.add_option('--path', dest='path',
                        help='Where to write your GeoJSON file. Default filename is the concationation of all the way IDs, dot json.',
                        action='store')

    parser.add_option('--precision', dest='precision',
                        help='The decimal precision for your GeoJSON file. Default is 6.',
                        action='store', default=None)

    parser.add_option('--indent', dest='indent',
                        help='Indent your GeoJSON file. Default is false.',
                        action='store_true', default=False)

    parser.add_option('--debug', dest='debug',
                        help='Enable debug logging',
                        action='store_true', default=False)

    options, ids = parser.parse_args()

    if options.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    if len(ids) == 0:
        logging.error("missing way IDs")
        sys.exit()

    if options.path:
        path = options.path
    else:
        path = "-".join(ids) + ".json"

    data = ways_to_geojson(ids)

    write_json(data, path, options.precision, options.indent)

    logging.info("done")
