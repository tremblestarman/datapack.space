import os, pymysql, json
from warnings import filterwarnings
filterwarnings('ignore', category=pymysql.Warning)
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) + '/util'
with open(BASE_DIR + '/languages.json', 'r', encoding="utf-8") as f:
    languages = json.loads(f.read())
with open(BASE_DIR + '/auth.json', 'r', encoding='utf-8') as f:
    auth = json.loads(f.read())
    auth['charset'] = 'UTF8MB4'
    connection = pymysql.connect(**auth)
    cur = connection.cursor()

cur.execute('show databases;')  # initialize database
dbs = cur.fetchall()
if not ('datapack_collection',) in dbs:
    cur.execute('create database datapack_collection;')
cur.execute('use datapack_collection;')
# -translate

# 0-0.cache duplicated (done)
# 0-1.porter insert duplicated (done)
# 0-2.auth check
# 0-3.porter log

# 1.data table + relation table (done)
# 2.cache table (done)
# 3.auth table (done)
# 4.related table (done) (manually)
# 5.port log table (done)
# 6.ii_queue (done)

### tables
# tables of info & relation queried by Web
author_info = '''
create table if not exists authors
(
    id VARCHAR(36) NOT NULL COMMENT 'id of author, a uuid',
    author_uid VARCHAR(32) NOT NULL COMMENT 'uid, varying in different websites',
    author_name TINYTEXT NOT NULL COMMENT 'name of the author',
    avatar TEXT COMMENT 'avatar url of the author',
    thumb INT DEFAULT 0 COMMENT 'thumbs the author got',

    PRIMARY KEY (id) COMMENT 'primary key',
    UNIQUE (author_uid) COMMENT 'unique key',
    INDEX (author_name(36))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
'''
cur.execute(author_info)  # create table: authors

datapack_info = f'''
create table if not exists datapacks
(
    id VARCHAR(36) NOT NULL COMMENT 'id of datapack, a uuid',
    link VARCHAR(255) NOT NULL COMMENT 'link of datapack, a web url',
    source TEXT NOT NULL COMMENT 'source website of datapack',
    author_id VARCHAR(36) NOT NULL COMMENT 'id of author, a uuid',
    full_content MEDIUMTEXT NOT NULL COMMENT 'full content of datapack, html or html-like',

    default_lang TINYTEXT COMMENT 'default language of datapack, eg: English/简体中文',
    default_lang_id TINYTEXT COMMENT 'id of default language, eg: en/zh-CN',
    default_name TINYTEXT COMMENT 'name of datapack in default language',
    {''.join([f"name_{k.replace('-','_')} TINYTEXT COMMENT 'name of datapack in {v['name']}'," for k, v in languages.items()])}
    default_intro TEXT NOT NULL COMMENT 'introduction of datapack in default language',
    {''.join([f"intro_{k.replace('-','_')} TEXT COMMENT 'introduction of datapack in {v['name']}'," for k, v in languages.items()])}

    post_time DATETIME COMMENT 'when the datapack posted',
    update_time DATETIME COMMENT 'when the datapack updated',
    thumb INT DEFAULT 0 COMMENT 'thumbs the datapack got',

    PRIMARY KEY (id) COMMENT 'primary key',
    UNIQUE (link) COMMENT 'unique key',
    INDEX (source(36)),
    INDEX (post_time),
    INDEX (update_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
'''
cur.execute(datapack_info) # create table: datapacks

tag_info = f'''
create table if not exists tags
(
    id VARCHAR(36) NOT NULL COMMENT 'id of tag, a uuid',
    type INT NOT NULL COMMENT 'tag type',

    default_lang TINYTEXT COMMENT 'default language of tag',
    default_lang_id TINYTEXT COMMENT 'id of default language',
    default_tag TINYTEXT NOT NULL COMMENT 'tag name in default language',
    {''.join([f"tag_{k.replace('-','_')} TINYTEXT COMMENT 'tag name in {v['name']}'," for k, v in languages.items()])}

    quotation INT DEFAULT 0 COMMENT 'count of quotation of this tag',
    thumb INT DEFAULT 0 COMMENT 'thumbs the tag got',

    PRIMARY KEY (id) COMMENT 'primary key',
    UNIQUE (default_tag(36)) COMMENT 'unique key',
    INDEX (default_tag(36))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
'''
cur.execute(tag_info) # create table: tags

datapack_tag_relation = '''
create table if not exists datapack_tags
(
    datapack_id VARCHAR(36) NOT NULL COMMENT 'id of datapack in a relation',
    tag_id VARCHAR(36) NOT NULL COMMENT 'id of taga in a relation',

    UNIQUE (datapack_id, tag_id) COMMENT 'unique key',
    INDEX (datapack_id),
    INDEX (tag_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
'''
cur.execute(datapack_tag_relation) # create table: datapack_tags

# tables of cache
datapack_cache = f'''
create table if not exists datapacks_cache
(
    id VARCHAR(36) COMMENT 'id of datapack, a uuid',
    link VARCHAR(255) COMMENT 'link of datapack, a web url',
    source TEXT COMMENT 'source website of datapack',
    author_id VARCHAR(36) COMMENT 'id of author, a uuid',
    full_content MEDIUMTEXT COMMENT 'full content of datapack, html or html-like',

    default_lang TINYTEXT COMMENT 'default language of datapack, eg: English/简体中文',
    default_lang_id TINYTEXT COMMENT 'id of default language, eg: en/zh-CN',
    default_name TINYTEXT COMMENT 'name of datapack in default language',
    default_intro TEXT COMMENT 'introduction of datapack in default language',

    post_time DATETIME COMMENT 'when the datapack posted',
    update_time DATETIME COMMENT 'when the datapack updated',

    status VARCHAR(4) COMMENT 'status of cache',

    PRIMARY KEY (id) COMMENT 'primary key'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
'''
cur.execute(datapack_cache) # create table: datapacks_cache

tag_cache = f'''
create table if not exists tags_cache
(
    id VARCHAR(36) COMMENT 'id of tag, a uuid',
    type INT COMMENT 'tag type',

    default_lang TINYTEXT COMMENT 'default language of tag',
    default_lang_id TINYTEXT COMMENT 'id of default language',
    default_tag TINYTEXT COMMENT 'tag name in default language',

    status VARCHAR(4) COMMENT 'status of cache',

    PRIMARY KEY (id) COMMENT 'primary key'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
'''
cur.execute(tag_cache) # create table: tags_cache

author_cache = '''
create table if not exists authors_cache
(
    id VARCHAR(36) COMMENT 'id of author, a uuid',
    author_uid VARCHAR(32) COMMENT 'uid, varying in different websites',
    author_name TINYTEXT COMMENT 'name of the author',
    avatar TEXT COMMENT 'avatar url of the author',

    status VARCHAR(4) COMMENT 'status of cache',

    PRIMARY KEY (id) COMMENT 'primary key'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
'''
cur.execute(author_cache) # create table: authors_cache

datapack_tag_relation_cache = '''
create table if not exists datapack_tag_relations_cache
(
    datapack_id VARCHAR(36) COMMENT 'id of datapack in a relation',
    tag_id VARCHAR(36) COMMENT 'id of taga in a relation',

    status VARCHAR(4) COMMENT 'status of cache',

    UNIQUE (datapack_id, tag_id) COMMENT 'unique key'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
'''
cur.execute(datapack_tag_relation_cache) # create table: datapack_tags

image_cache = '''
create table if not exists images_cache
(
    local_url TINYTEXT COMMENT 'local storage path',
    web_url TINYTEXT COMMENT 'web path',

    status VARCHAR(4) COMMENT 'status of cache',

    UNIQUE (local_url(63), web_url(63)) COMMENT 'unique key'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
'''
cur.execute(image_cache) # create table: images_cache

# auth table
auth_table = '''
create table if not exists authorizations
(
    id VARCHAR(36) NOT NULL COMMENT 'id of datapack in a relation',
    type VARCHAR(8) NOT NULL COMMENT 'type of authorization, author or datapack',

    PRIMARY KEY (id) COMMENT 'primary key'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
'''
cur.execute(auth_table) # create table: authorizations

# related table
datapack_related = '''create table if not exists datapacks_related
(
    datapack_id VARCHAR(36) NOT NULL,
    related TEXT,
    INDEX (datapack_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
'''
cur.execute(datapack_related)
author_related = '''create table if not exists authors_related
(
    author_id VARCHAR(36) NOT NULL,
    related TEXT,
    INDEX (author_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
'''
cur.execute(author_related)

# log table
log_table = '''create table if not exists port_log
(
    id VARCHAR(36) NOT NULL COMMENT 'id for datapack, author or tag',
    type VARCHAR(8) NOT NULL COMMENT 'datapack, author or tag',
    operation VARCHAR(4) NOT NULL COMMENT 'operation like +, - or *',
    time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT 'time of port operation'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
'''
cur.execute(log_table) # create table: port_log (only for datapacks, authors and tags)

# ii queue
def ii_queue_of(column): return f'''create table if not exists ii_queue_{column}
(
    id VARCHAR(36) NOT NULL, operate VARCHAR(4),
    INDEX (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
'''
columns = ["name_" + lang.replace('-', '_') for lang, _ in languages.items()] + ["intro_" + lang.replace('-', '_') for lang, _ in languages.items()] + ['default_name', 'default_intro']
for col in columns:
    cur.execute(ii_queue_of(col))
