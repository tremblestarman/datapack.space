import os, json
from util.collector import datapack_collector
from util.database import datapack_db
BASE_DIR = os.path.dirname(__file__)
versions = set()
sources = []
DB = datapack_db()

# crawl and insert
DC = datapack_collector(BASE_DIR + '/util/schema/mcbbs.json')
versions = versions | DC.versions
sources.append(DC.schema['id'])
DB.info_import(DC.info_list)
#DB.download_img()

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
