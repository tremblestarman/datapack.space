import os, pymysql, json
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) + '/util'
with open(BASE_DIR + '/languages.json', 'r', encoding="utf-8") as f:
    languages = json.loads(f.read())
with open(BASE_DIR + '/auth.json', 'r', encoding='utf-8') as f:
    auth = json.loads(f.read())
    auth['charset'] = 'UTF8MB4'
    connection = pymysql.connect(**auth)
    cur = connection.cursor()
cur.execute('use datapack_collection;')
ii_columns = ["name_" + lang.replace('-', '_') for lang, _ in languages.items()] + ["intro_" + lang.replace('-', '_') for lang, _ in languages.items()] + ['default_name', 'default_intro']
cur.execute(f'''
drop table if exists
datapacks, tags, authors, datapack_tags,
datapacks_cache, tags_cache, authors_cache, datapack_tag_relations_cache, images_cache,
authorizations,
datapacks_related, authors_related,
port_log,
{','.join([f"ii_queue_{column}" for column in ii_columns])}
;''')
