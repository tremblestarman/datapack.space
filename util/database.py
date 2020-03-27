import pymysql, json, os, uuid, urllib, socket, time
from warnings import filterwarnings
from googletrans import Translator
from multiprocessing.dummy import Pool as thread_pool
from emoji import demojize
filterwarnings('ignore',category=pymysql.Warning)
BASE_DIR = os.path.dirname(__file__)
socket.setdefaulttimeout(30)
class translator:
    limit = 50
    current_time = 0
    timeout = 60
    trans = Translator()
    def translate(self, text: str, lang: str):
        text = demojize(text)
        if self.current_time >= self.limit:
            print('sleep to prevent being banned. (wait 1 minute')
            time.sleep(self.timeout)
            self.current_time = 0
        self.current_time += 1
        try:
            result = self.trans.translate(text, dest=lang).text
            return result
        except Exception as e:
            count = 1
            print(f"- translate '{text}' to '{lang}' error:", e)
            while count <= 5:
                print('error might caused by being banned or slow network speed.\n\
                    (wait 15s to be unbanned or to fix network problem.')
                time.sleep(15)
                try:
                    result = self.trans.translate(text, dest=lang).text
                    return result
                except Exception as e:
                    print(f"- translate '{text}' to '{lang}' error:", e)
                    print('- reloading for %d time' % count if count == 1 else '- reloading for %d times' % count)
                    count += 1
            if count > 5:
                print("- translation failed!")
                return text
class datapack_db:
    img_queue = []
    translated_tags = {}
    trans = translator()
    timeout = 5
    def __init__(self):
        try:
            with open(BASE_DIR + '/auth.json', 'r', encoding='utf-8') as f:
                auth = json.loads(f.read())
                auth['charset'] = 'UTF8MB4'
                self.db = pymysql.connect(**auth)
            with open(BASE_DIR + '/languages.json', 'r', encoding="utf-8") as f:
                self.languages = json.loads(f.read())
            self.cur = self.db.cursor()
            self.cur.execute('show databases;') # initialize database
            if not ('datapack_collection',) in self.cur.fetchall():
                self.cur.execute('create database datapack_collection;')
            self.cur.execute('use datapack_collection;')
            self.cur.execute('drop table if exists datapack_tags;') # delete relation table
            datapack_info = f'''create table if not exists datapacks
            (
                id VARCHAR(36) NOT NULL,
                link VARCHAR(255) NOT NULL,
                author_id VARCHAR(36) NOT NULL,
                intro TEXT NOT NULL,
                full_content MEDIUMTEXT NOT NULL,
                default_lang TINYTEXT,
                default_lang_id TINYTEXT,
                {' '.join([f"name_{k.replace('-','_')} TINYTEXT," for k, _ in self.languages.items()])}
                default_tags_str TEXT,
                {' '.join([f"tags_str_{k.replace('-','_')} TEXT," for k, _ in self.languages.items()])}
                default_name TINYTEXT,
                source TEXT NOT NULL,
                post_time DATETIME,
                update_time DATETIME,
                thumb INT DEFAULT 0,
                PRIMARY KEY (id),
                FOREIGN KEY (author_id) REFERENCES authors(id),
                UNIQUE (link)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;'''
            tag_info = f'''create table if not exists tags
            (
                id VARCHAR(36) NOT NULL,
                default_lang TINYTEXT,
                default_lang_id TINYTEXT,
                {' '.join([f"tag_{k.replace('-','_')} TINYTEXT," for k, _ in self.languages.items()])}
                default_tag TINYTEXT NOT NULL,
                quotation INT DEFAULT 1,
                type INT NOT NULL,
                thumb INT DEFAULT 0,
                PRIMARY KEY (id),
                UNIQUE (id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;'''
            author_info = '''create table if not exists authors
            (
                id VARCHAR(36) NOT NULL,
                author_uid VARCHAR(32) NOT NULL,
                author_name TINYTEXT NOT NULL,
                avatar TEXT,
                thumb INT DEFAULT 0,
                PRIMARY KEY (id),
                UNIQUE (author_uid)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;'''
            datapack_tag = '''create table if not exists datapack_tags
            (
                id INT NOT NULL AUTO_INCREMENT,
                datapack_id VARCHAR(36) NOT NULL,
                tag_id VARCHAR(36) NOT NULL,
                PRIMARY KEY (id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;'''
            self.cur.execute(tag_info)
            self.cur.execute(author_info)
            self.cur.execute(datapack_info)
            self.cur.execute(datapack_tag)
            print('connect successfully')
            # add colums
            def alter(table: str, col: str, type: str):
                for k, _ in self.languages.items():
                    operated = True
                    try:
                        add_col = f'''ALTER TABLE {table} ADD {col}_{k.replace('-','_')} {type};'''
                        self.cur.execute(add_col)
                    except:
                        operated = False
                    if operated:
                        print(f'{table} added "', k.replace('-', '_'), f'" of colum {col}')
            alter('datapacks', 'name', 'TINYTEXT')
            alter('datapacks', 'tags_str', 'TEXT')
            alter('tags', 'tag', 'TINYTEXT')
            self.cur.execute('update tags set quotation = 0;')
            # preload
            self.cur.execute('select id from datapacks')
            res = self.cur.fetchall()
            self._datapack_removal = [j for i in res for j in i] if not res == None else None
            assert not self._datapack_removal == None
            print('preloaded successfully')
            self.db.commit()
        except Exception as e:
            print('connect error:', e)
    def _author_insert(self, info: dict):
        aid = uuid.uuid3(uuid.NAMESPACE_DNS, info['author_uid'])
        info['author_name'] = pymysql.escape_string(info['author_name'])
        author_insert = f'''insert into authors (id, author_uid, author_name, avatar) 
        values ('{aid}', '{info['author_uid']}', '{info['author_name']}', '{info['author_avatar']}') 
        on duplicate key update 
        author_uid = '{info['author_uid']}',
        author_name = '{info['author_name']}',
        avatar = '{info['author_avatar']}';'''
        self.cur.execute(author_insert)
        return str(aid)
    def _tag_translate(self, tid, tag: str, type: int, default_lang: str):
        self.cur.execute("select " + ','.join(["tag_" + k.replace('-', '_') for k, _ in self.languages.items()]) + f" from tags where id = '{tid}'")
        res = self.cur.fetchall()
        exists = [j for i in res for j in i] if not res == None else []
        # not translated or updated
        i = 0
        translated = {}
        for k, v in self.languages.items():
            if not k == default_lang and exists.__len__() > 0 and i < exists.__len__() and not exists[i] == '':
                translated[k] = exists[i]
                print(k, ':had translated', '"', tag, '"')
            else:
                try:
                    translated[k] = tag if k == default_lang or type <= 1 else self.trans.translate(tag, k).lower()
                    if not (k == default_lang or type <= 1):
                        print(k, ':translated', '"', tag, '"', 'to', '"', translated[k], '"')
                except:
                    print("translation error.")
            i += 1
        return translated
    def _tag_insert(self, info: dict):
        tag_sort = [info['source'], info['game_version'], info['tag'], info['keywords']]
        info["default_tags_strs"] = []
        for k, _ in self.languages.items():
            info["tags_strs_" + k] = []
        def __exe(_tag: str, _type: int):
            tid = uuid.uuid3(uuid.NAMESPACE_DNS, _tag)
            _tag = pymysql.escape_string(_tag)
            info["default_tags_strs"].append(f'{_type}:{_tag},')
            if str(tid) in self.translated_tags:
                translated = self.translated_tags[str(tid)]
                for k, _ in translated.items():
                    info["tags_strs_" + k].append(f'{_type}:{translated[k]},')
                quotation = f"update tags set quotation = quotation + 1 where id = '{tid}';"
                self.cur.execute(quotation)
                return str(tid)
            translated = self._tag_translate(str(tid), _tag, _type, info['default_lang'])
            for k, _ in translated.items():
                translated[k] = pymysql.escape_string(translated[k])
                info["tags_strs_" + k].append(f'{_type}:{translated[k]},')
            tag_insert = f'''insert into tags (id, default_tag, default_lang, default_lang_id, {' '.join([f"tag_{k.replace('-','_')}," for k, _ in self.languages.items()])} type) 
            values ('{tid}', '{_tag}', '{self.languages[info['default_lang']]['name']}', '{info['default_lang']}', {' '.join([f"'{translated[k]}'," for k, _ in self.languages.items()])} {_type}) 
            on duplicate key update 
            quotation = quotation + 1,
            default_lang = '{self.languages[info['default_lang']]['name']}',
            default_lang_id = '{info['default_lang']}',
            default_tag = '{_tag}',
            {' '.join([f"tag_{k.replace('-','_')} = '{translated[k]}'," for k, _ in self.languages.items()])}
            type = 
            case 
            when type > {_type} then {_type}
            else type
            end;'''
            self.cur.execute(tag_insert)
            self.translated_tags[str(tid)] = translated
            return str(tid)
        result = []
        for i in range(0, 4):
            if type(tag_sort[i]) == list:
                result += [__exe(j, i) for j in tag_sort[i]]
            else:
                result.append(__exe(tag_sort[i], i))
        return result
    def _img_save(self, url: str, _dir: str, id):
        img_dir = os.path.dirname(BASE_DIR) + '/bin/img/' + _dir
        if not os.path.exists(img_dir):
            os.mkdir(img_dir)
        try:
            opener = urllib.request.build_opener()
            opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1941.0 Safari/537.36')]
            urllib.request.install_opener(opener)
            urllib.request.urlretrieve(url, filename=img_dir + f'/{str(id)}.png')
        except Exception as e:
            count = 1
            print(f'- download img ({url}) error:', e)
            while count <= 5:
                time.sleep(self.timeout)
                try:
                    opener = urllib.request.build_opener()
                    opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1941.0 Safari/537.36')]
                    urllib.request.install_opener(opener)
                    urllib.request.urlretrieve(url, filename=img_dir + f'/{str(id)}.png')
                    break
                except Exception as e:
                    print(f'- download img ({url}) error:', e)
                    print('- reloading for %d time' % count if count == 1 else '- reloading for %d times' % count)
                    count += 1
            if count > 5:
                print("- downloading failed!")
        print(f'- saved img {url}.')
        return f'/{_dir}/{str(id)}.png'
    def _img_remove(self, _dir: str, id):
        img = os.path.dirname(BASE_DIR) + f"/bin/img/'{_dir}'/'{id}'.png"
        if os.path.exists(img):
            os.remove(img)
    def _name_translate(self, info: dict, pre_default_name = None, pre_names: dict = None):
        # not translated or updated
        translate_all = pre_default_name == None or pre_names == None or not pre_default_name == info['default_name']
        i = 0
        for k, v in self.languages.items():
            if k == info['default_lang']: # default language
                continue
            if translate_all or pre_names[i] == None or pre_names[i] == '':
                if 'name_' + k in info and info['name_' + k] not in ['', 'auto']:
                    continue
                try:
                    info['name_' + k] = self.trans.translate(info['default_name'], k).upper()
                except:
                    print("translation error.")
                print(k, ':translated', '"', info['default_name'], '"', 'to', '"', info['name_' + k], '"')
            else:
                info['name_' + k] = pre_names[i]
            i += 1
    def _incremental_update(self, info: dict, previous: list):
        if info['post_time'] == info['update_time']:
            info['post_time'] = info['update_time'] = previous[0]
        self._name_translate(info, previous[1], previous[2:])
    def _datapack_insert(self, info: dict):
        aid = self._author_insert(info)
        assert not aid == None
        tids = self._tag_insert(info)
        assert not tids == None
        did = uuid.uuid3(uuid.NAMESPACE_DNS, info['link'])
        self.cur.execute("select post_time, default_name, " + ','.join(["name_" + k.replace(
            '-', '_') for k, _ in self.languages.items()]) + f" from datapacks where id = '{did}'")
        res = self.cur.fetchall()
        exists = [j for i in res for j in i] if not res == None else []
        if not exists.__len__() == 0:
            self._incremental_update(info, exists) #incremental_update
        if exists.__len__() == 0: # new element
            self._name_translate(info)
        intro = pymysql.escape_string('\n'.join(info['summrization'])) #escape summaries
        content_raw = pymysql.escape_string(info['content_raw']) #escape content
        info["default_tags_str"] = ''.join(info["default_tags_strs"])
        info["default_name"] = pymysql.escape_string(info["default_name"])
        for k, _ in self.languages.items():
            info['name_' + k] = pymysql.escape_string(info['name_' + k])
            info["tags_str_" + k] = ''.join(info["tags_strs_" + k])
        datapack_insert = f'''insert into datapacks (id, link, {' '.join([f"name_{k.replace('-','_')}," for k, _ in self.languages.items()])} {' '.join([f"tags_str_{k.replace('-','_')}," for k, _ in self.languages.items()])} default_tags_str, author_id, default_lang, default_lang_id, default_name, intro, full_content, source, post_time, update_time) 
        values ('{did}', '{info['link']}', {",".join(["'" + info["name_" + k] + "'" for k, _ in self.languages.items()])}, {",".join(["'" + info["tags_str_" + k] + "'" for k, _ in self.languages.items()])}, '{info["default_tags_str"]}', '{aid}', '{self.languages[info['default_lang']]['name']}', '{info['default_lang']}', '{info['default_name']}', '{intro}', '{content_raw}', '{info['source']}', '{info['post_time']}', '{info['update_time']}') 
        on duplicate key update 
        link = '{info['link']}',
        {"".join(["name_" + k.replace('-','_') + " = '" + info["name_" + k] + "'," for k, _ in self.languages.items()])}
        author_id = '{aid}',
        default_lang = '{self.languages[info['default_lang']]['name']}',
        default_lang_id = '{info['default_lang']}',
        default_name = '{info['default_name']}',
        intro = '{intro}',
        full_content = '{content_raw}',
        default_tags_str = '{info["default_tags_str"]}',
        {"".join(["tags_str_" + k.replace('-','_') + " = '" + info["tags_str_" + k] + "'," for k, _ in self.languages.items()])}
        source = '{info['source']}',
        update_time = '{info['update_time']}';'''
        self.cur.execute(datapack_insert)
        assert not did == None
        for tid in tids:
            relation_form = f'''insert into datapack_tags (datapack_id, tag_id) 
            values ('{did}', '{tid}');'''
            self.cur.execute(relation_form)
        if not info['author_avatar'] in [None, '']:
            self.img_queue.append((info['author_avatar'], 'author', aid))
        if not info['cover_img'] in [None, '']:
            self.img_queue.append((info['cover_img'], 'cover', did))
        del info
        return str(did)
    def info_import(self, info_list: list):
        for i in range(0, info_list.__len__()):
            print(str(i + 1), '/', str(info_list.__len__()), ':', info_list[i]['link'], '.')
            info = info_list[i]
            did = str(self._datapack_insert(info))
            if did in self._datapack_removal:
                self._datapack_removal.remove(did)
            self.db.commit()
            print(did, ':', info['link'], 'has been imported into database successfully.')
        self.cur.execute('''DELETE FROM datapack_tags
        WHERE id NOT IN (
            SELECT temp.min_id FROM (
                SELECT MIN(id) min_id FROM datapack_tags
                    GROUP BY datapack_id, tag_id
                )AS temp
        );
        ''') # delete duplicated relation
        print('end')
    def download_img(self):
        self.total = 0
        def process(img_target):
            try:
                self._img_save(*img_target)
            except:
                print(img_target, '\n', 'got error.')
            self.total += 1
            print('- img done', self.total, '/', str(self.img_queue.__len__()))
        pool = thread_pool()
        pool.map(process, self.img_queue)
        pool.close()
        pool.join()
        del self.total
        self.img_queue.clear()
    def info_delete_nonexistent(self):
        print('checking and deleting...')
        for i in range(0, self._datapack_removal.__len__()):
            print(str(i + 1), '/', str(self._datapack_removal.__len__()))
            rem = self._datapack_removal[i]
            datapack_delete = f"delete from datapacks where id = '{rem}';"
            self.cur.execute(datapack_delete)
            self._img_remove('cover', rem)
            print(rem, 'has been deleted.')
    def reset(self):
        self.cur.execute('drop table if exists datapacks, tags, authors, datapack_tags;')
        print('reseted')
    def __del__(self):
        self.db.commit()
        self.db.close()
        print('committed and closed')
