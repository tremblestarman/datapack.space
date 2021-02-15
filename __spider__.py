import os, json
from time import sleep
from util.collector import datapack_collector
from util.cache import datapack_cache
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
versions = set()
sources = []
CACHE = datapack_cache() # when spider run, clear all cache

for schema in os.listdir(BASE_DIR + '/util/schema'):
    # crawl and insert
    CRAWLER = datapack_collector(BASE_DIR + '/util/schema/' + schema, refill=True)
    while CRAWLER.post_pool.__len__() > 0:
        CRAWLER.analyze_all()
        print('==== start import ====')
        CACHE.fill(CRAWLER.info_list)
        CRAWLER.info_list.clear()
        print('still', CRAWLER.post_pool.__len__(), 'to be analyzed and inserted into cache.')
        print('==== a package just have finished, sleep 10s to prevent being banned ====')
        sleep(10)
    versions = versions | CRAWLER.versions
    sources.append(CRAWLER.schema['id'])
    del CRAWLER
CACHE.delete_unexisted()

# update sources and versions
with open(BASE_DIR + '/templates/generic/combo-temp.tmpl', 'r', encoding='utf-8') as tmpl:
    combo = tmpl.read()
with open(BASE_DIR + '/templates/generic/combo.tmpl', 'w+', encoding='utf-8') as tmpl:
    fmt = '    <option value="%s">%s</option>'
    combo = combo.replace(r'%%s%%', '\n'.join([fmt % (s, s) for s in list(sorted(sources))]))
    combo = combo.replace(r'%%v%%', '\n'.join([fmt % (v, v) for v in list(sorted(versions))]))
    combo = combo.replace(r'-temp', '')
    tmpl.write(combo)
versions.clear()
sources.clear()