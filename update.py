import os, json
from time import sleep
from util.collector import datapack_collector
from util.database import datapack_db
BASE_DIR = os.path.dirname(__file__)
versions = set()
sources = []
DB = datapack_db()

for schema in os.listdir(BASE_DIR + '/util/schema'):
    # crawl and insert
    if (schema == 'mcbbs.json'):
        DC = datapack_collector(BASE_DIR + '/util/schema/' + schema, refill=True)
    else:
        DC = datapack_collector(BASE_DIR + '/util/schema/' + schema, refill=False)
    while DC.post_pool.__len__() > 0:
        DC.analyze_all()
        print('==== start import ====')
        DB.info_import(DC.info_list)
        DB.download_img()
        DC.info_list.clear()
        print('==== a package just have finished, sleep 10s to prevent being banned ====')
        sleep(10)
    versions = versions | DC.versions
    sources.append(DC.schema['id'])
    del DC
# delete recordis that do not exist
DB.info_delete_nonexistent()

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
