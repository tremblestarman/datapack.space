import os, json
from time import sleep
from util.collector import datapack_collector
from util.database import datapack_db
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
versions = set()
sources = []
DB = datapack_db()
enable_delete = True

for schema in os.listdir(BASE_DIR + '/util/schema'):
    # crawl and insert
    DC = datapack_collector(BASE_DIR + '/util/schema/' + schema, refill=True)
    if DC.schema_err:
        enable_delete = False
    while DC.post_pool.__len__() > 0:
        DC.analyze_all()
        print('==== start import ====')
        DB.info_import(DC.info_list)
        DB.download_img()
        DC.info_list.clear()
        print('still', DC.post_pool.__len__(), 'to be analyzed and inserted into database.')
        print('==== a package just have finished, sleep 10s to prevent being banned ====')
        sleep(10)
    versions = versions | DC.versions
    sources.append(DC.schema['id'])
    del DC
# delete recordis that do not exist
if enable_delete:
    DB.info_delete_nonexistent()
else:
    print('skipped deletion because schema error occurs.')

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
