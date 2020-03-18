import pymysql, json, os, uuid, urllib, socket, time
from warnings import filterwarnings
from googletrans import Translator
from multiprocessing.dummy import Pool as thread_pool
filterwarnings('ignore',category=pymysql.Warning)
BASE_DIR = os.path.dirname(__file__)
socket.setdefaulttimeout(30)
class translator:
    limit = 100
    current_time = 0
    timeout = 60
    trans = Translator()
    def translate(self, text: str, lang: str):
        if self.current_time >= self.limit:
            print('sleep to avoid banned. (wait 1 minute')
            time.sleep(self.timeout)
            self.current_time = 0
        self.current_time += 1
        return self.trans.translate(text, dest=lang).text
class datapack_db:
    img_queue = []
    tags = set()
    trans = translator()
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
                {' '.join([f"name_{k.replace('-','_')} TINYTEXT," for k, _ in self.languages.items()])}
                default_name TINYTEXT,
                source TEXT NOT NULL,
                post_time DATETIME,
                update_time DATETIME,
                thumb INT DEFAULT 0,
                PRIMARY KEY (id),
                FOREIGN KEY (author_id) REFERENCES authors(id),
                UNIQUE (link)
            );'''
            tag_info = f'''create table if not exists tags
            (
                id VARCHAR(36) NOT NULL,
                default_lang TINYTEXT,
                {' '.join([f"tag_{k.replace('-','_')} TINYTEXT," for k, _ in self.languages.items()])}
                default_tag TINYTEXT NOT NULL,
                type INT NOT NULL,
                thumb INT DEFAULT 0,
                PRIMARY KEY (id),
                UNIQUE (id)
            );'''
            author_info = '''create table if not exists authors
            (
                id VARCHAR(36) NOT NULL,
                author_uid VARCHAR(32) NOT NULL,
                author_name TINYTEXT NOT NULL,
                avatar TEXT,
                thumb INT DEFAULT 0,
                PRIMARY KEY (id),
                UNIQUE (author_uid)
            );'''
            datapack_tag = '''create table if not exists datapack_tags
            (
                id INT NOT NULL AUTO_INCREMENT,
                datapack_id VARCHAR(36) NOT NULL,
                tag_id VARCHAR(36) NOT NULL,
                PRIMARY KEY (id)
            );'''
            self.cur.execute(tag_info)
            self.cur.execute(author_info)
            self.cur.execute(datapack_info)
            self.cur.execute(datapack_tag)
            print('connect successfully')
            # add colums
            for k, _ in self.languages.items():
                operated = True
                try:
                    add_col = f'''ALTER TABLE datapacks ADD name_{k.replace('-','_')} TINYTEXT;'''
                    self.cur.execute(add_col)
                except:
                    operated = False
                if operated:
                    print('datapacks added "', k.replace('-', '_'), '" colum')
            for k, _ in self.languages.items():
                operated = True
                try:
                    add_col = f'''ALTER TABLE tags ADD tag_{k.replace('-','_')} TINYTEXT;'''
                    self.cur.execute(add_col)
                except:
                    operated = False
                if operated:
                    print('tags added "', k.replace('-', '_'), '" colum')
            # preload
            self.cur.execute('select id from datapacks')
            res = self.cur.fetchall()
            self._datapack_removal = [j for i in res for j in i] if not res == None else None
            assert not self._datapack_removal == None
            print('preloaded successfully')
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
    def _tag_translate(self, tag: str, type: int, default_lang: str):
        # not translated or updated
        translated = {}
        for k, v in self.languages.items():
            try:
                translated[k] = tag if k == default_lang or type <= 1 else self.trans.translate(tag, k).lower()
                if not (k == default_lang or type <= 1):
                    print(k, ':translated', '"', tag, '"', 'to', '"', translated[k], '"')
            except:
                print("translation error.")
        return translated
    def _tag_insert(self, info: dict):
        tag_sort = [info['source'], info['game_version'], info['tag'], info['keywords']]
        def __exe(_tag: str, _type: int):
            tid = uuid.uuid3(uuid.NAMESPACE_DNS, _tag)
            if str(tid) in self.tags:
                return str(tid)
            else:
                self.tags.add(str(tid))
            translated = self._tag_translate(_tag, _type, info['default_lang'])
            for k, _ in translated.items():
                translated[k] = pymysql.escape_string(translated[k])
            tag_insert = f'''insert into tags (id, default_tag, default_lang, {' '.join([f"tag_{k.replace('-','_')}," for k, _ in self.languages.items()])} type) 
            values ('{tid}', '{_tag}', '{self.languages[info['default_lang']]['name']}', {' '.join([f"'{translated[k]}'," for k, _ in self.languages.items()])} {_type}) 
            on duplicate key update 
            default_lang = '{self.languages[info['default_lang']]['name']}',
            default_tag = '{_tag}',
            {' '.join([f"tag_{k.replace('-','_')} = '{translated[k]}'," for k, _ in self.languages.items()])}
            type = 
            case 
            when type > {_type} then {_type}
            else type
            end;'''
            self.cur.execute(tag_insert)
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
            opener.addheaders = [
                ('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1941.0 Safari/537.36')]
            urllib.request.install_opener(opener)
            urllib.request.urlretrieve(
                url, filename=img_dir + f'/{str(id)}.png')
        except socket.timeout:
            count = 1
            while count <= 5:
                try:
                    opener = urllib.request.build_opener()
                    opener.addheaders = [
                        ('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1941.0 Safari/537.36')]
                    urllib.request.install_opener(opener)
                    urllib.request.urlretrieve(
                        url, filename=img_dir + f'/{str(id)}.png')
                    break
                except socket.timeout:
                    print('- reloading for %d time' % count if count ==
                        1 else '- reloading for %d times' % count)
                    count += 1
            if count > 5:
                print("- downloading failed!")
        except Exception as e:
            print(f'- download img ({url}) error:', e)
            return ''
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
            i += 1
    def _incremental_update(self, info: dict, previous: list):
        if info['post_time'] == info['update_time']:
            info['post_time'] = info['update_time'] = previous[0]
        self._name_translate(info, previous[1], previous[2:])
    def _datapack_insert(self, info: dict):
        aid = self._author_insert(info)
        assert not aid == None
        did = uuid.uuid3(uuid.NAMESPACE_DNS, info['link'])
        self.cur.execute("select post_time, default_name, " + ','.join(["name_" + k.replace('-', '_') for k, _ in self.languages.items()]) + f" from datapacks where id = '{did}'")
        res = self.cur.fetchall()
        exists = [j for i in res for j in i] if not res == None else []
        if not exists.__len__() == 0:
            self._incremental_update(info, exists) #incremental_update
        if exists.__len__() == 0: # new element
            self._name_translate(info)
        intro = pymysql.escape_string('\n'.join(info['summrization'])) #escape summaries
        content_raw = pymysql.escape_string(info['content_raw']) #escape content
        for k, _ in self.languages.items():
            info['name_' + k] = pymysql.escape_string(info['name_' + k])
        datapack_insert = f'''insert into datapacks (id, link, {' '.join([f"name_{k.replace('-','_')}," for k, _ in self.languages.items()])} author_id, default_lang, default_name, intro, full_content, source, post_time, update_time) 
        values ('{did}', '{info['link']}', {",".join(["'" + info["name_" + k] + "'" for k, _ in self.languages.items()])}, '{aid}', '{self.languages[info['default_lang']]['name']}', '{info['default_name']}', '{intro}', '{content_raw}', '{info['source']}', '{info['post_time']}', '{info['update_time']}') 
        on duplicate key update 
        link = '{info['link']}',
        {"".join(["name_" + k.replace('-','_') + " = '" + info["name_" + k] + "'," for k, _ in self.languages.items()])}
        author_id = '{aid}',
        default_lang = '{self.languages[info['default_lang']]['name']}',
        default_name = '{info['default_name']}',
        intro = '{intro}',
        full_content = '{content_raw}',
        source = '{info['source']}',
        update_time = '{info['update_time']}';'''
        self.cur.execute(datapack_insert)
        assert not did == None
        tids = self._tag_insert(info)
        assert not tids == None
        for tid in tids:
            relation_form = f'''insert into datapack_tags (datapack_id, tag_id) 
            values ('{did}', '{tid}');'''
            self.cur.execute(relation_form)
        if not info['author_avatar'] in [None, '']:
            self.img_queue.append((info['author_avatar'], 'author', aid))
        if not info['cover_img'] in [None, '']:
            self.img_queue.append((info['cover_img'], 'cover', did))
        return str(did)
    def info_import(self, info_list: list):
        for i in range(0, info_list.__len__()):
            print(str(i + 1), '/', str(info_list.__len__()), ':', info_list[i]['link'], '.')
            info = info_list[i]
            did = str(self._datapack_insert(info))
            if did in self._datapack_removal:
                self._datapack_removal.remove(did)
            print(did, ':', info['link'], 'has been imported into database successfully.')
        print('checking and deleting...')
        for i in range(0, self._datapack_removal.__len__()):
            print(str(i + 1), '/', str(self._datapack_removal.__len__()))
            rem = self._datapack_removal[i]
            datapack_delete = f"delete from datapacks where id = '{rem}';"
            self.cur.execute(datapack_delete)
            self._img_remove('cover', rem)
            print(rem, 'has been deleted.')
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
    def reset(self):
        self.cur.execute('drop table if exists datapacks, tags, authors, datapack_tags;')
        print('reseted')
    def __del__(self):
        self.db.commit()
        self.db.close()
        print('committed and closed')
