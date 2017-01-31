import logging
import random
logger = logging.getLogger(__name__)

def safe_encode(x):
    if isinstance(x, basestring):
        return x.encode('ascii', 'replace')
    else:
        return str(x)

def convert_facet_entry_to_highchart_entry(x):
    if 'term' in x:
        return [ safe_encode(x['term']), x['count']]
    else:
        return x

def convert_facets_to_highcharts(facets):
    result = map(lambda x: convert_facet_entry_to_highchart_entry(x), facets) if facets is not None else []
    return result

def convert_facet_to_highchart_entry(entry, max_value):
    entry['z'] = entry['count']
    entry['y'] = random.randint(0, max_value)
    return entry

def convert_termfacet_to_bubblechart(facets):
    max_range = facets[0]['count'] if len(facets) > 0 else 0
    result = []
    i = 0
    for entry in facets:
        new_entry = convert_facet_to_highchart_entry(entry, 2 * max_range)
        new_entry['x'] = i
        i += 1
        result.append(new_entry)
    return result