import os, json, time
from util.porters import resource_porter, record_porter
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) + '/util'
with open(BASE_DIR + '/languages.json', 'r', encoding="utf-8") as f:
    languages = json.loads(f.read())

# datapack porter
def datapack_callback(self, cache_dict: dict):
    # log
    self.cur.execute(f"insert into port_log(id, type, operation) values('{cache_dict['id']}', 'datapack', '{cache_dict['status']}');")
    # ii queue
    ii_op = '+' # default is '+'
    if cache_dict['status'] == '-':
        ii_op = '-'
    self.cur.execute(f'''insert into ii_queue_default_name(id, operate) values ('{cache_dict['id']}', '{ii_op}');''')
    self.cur.execute(f'''insert into ii_queue_default_intro(id, operate) values ('{cache_dict['id']}', '{ii_op}');''')
    for lang, _ in languages.items():
        self.cur.execute(f'''insert into ii_queue_name_{lang.replace('-', '_')}(id, operate) values ('{cache_dict['id']}', '{ii_op}');''')
        self.cur.execute(f'''insert into ii_queue_intro_{lang.replace('-', '_')}(id, operate) values ('{cache_dict['id']}', '{ii_op}');''')
datapack_porter = record_porter('datapacks_cache', 'datapacks', callback=datapack_callback)
datapack_porter.start()

# author porter
def author_callback(self, cache_dict: dict):
    # log
    self.cur.execute(f"insert into port_log(id, type, operation) values('{cache_dict['id']}', 'author', '{cache_dict['status']}');")
author_porter = record_porter('authors_cache', 'authors', callback=author_callback)
author_porter.start()

# tag porter
def tag_callback(self, cache_dict: dict):
    # log
    self.cur.execute(f"insert into port_log(id, type, operation) values('{cache_dict['id']}', 'tag', '{cache_dict['status']}');")
tag_porter = record_porter('tags_cache', 'tags', callback=tag_callback)
tag_porter.start()

# datapack-tag relations porter
def datapack_tag_relation_callback(self, cache_dict: dict):
    # no log
    # update quotation count of the tag
    if cache_dict['status'] == '+':
        self.cur.execute(f"update tags set quotation = quotation + 1 where id = '{cache_dict['tag_id']}';")
    elif cache_dict['status'] == '-':
        self.cur.execute(f"update tags set quotation = quotation - 1 where id = '{cache_dict['tag_id']}';")
datapack_tag_relation_porter = record_porter('datapack_tag_relations_cache', 'datapack_tags', callback=datapack_tag_relation_callback)
datapack_tag_relation_porter.start()

# image porter
RESOURCE_DIR = os.path.dirname(BASE_DIR) + f"/bin/img"
DOMAIN_BLOCK = ['img.youtube.com']
image_porter = resource_porter('images_cache', resource_dir=RESOURCE_DIR, domain_block=DOMAIN_BLOCK, ignoreFailed=True)
image_porter.start()

datapack_porter.join()
author_porter.join()
tag_porter.join()
datapack_tag_relation_porter.join()
image_porter.join()
time.sleep(60)