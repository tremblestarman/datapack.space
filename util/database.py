import pymysql, json, os, uuid, urllib, socket
from warnings import filterwarnings
from util.translate import youdao_translate
from multiprocessing.dummy import Pool as thread_pool
filterwarnings('ignore',category=pymysql.Warning)
BASE_DIR = os.path.dirname(__file__)
socket.setdefaulttimeout(30)
class datapack_db:
    img_queue = []
    def __init__(self):
        try:
            with open(BASE_DIR + '/auth.json', 'r', encoding='utf-8') as f:
                auth = json.loads(f.read())
                auth['charset'] = 'UTF8MB4'
                self.db = pymysql.connect(**auth)
            with open(BASE_DIR + '/languages.json', 'r', encoding="utf-8") as f:
                self.lang = json.loads(f.read())
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
                {' '.join([f"name_{k} TINYTEXT," for k, _ in self.lang.items()])}
                author_id VARCHAR(36) NOT NULL,
                intro TEXT NOT NULL,
                full_content MEDIUMTEXT NOT NULL,
                default_lang TINYTEXT,
                default_name TINYTEXT,
                source TEXT NOT NULL,
                post_time DATETIME,
                update_time DATETIME,
                thumb INT DEFAULT 0,
                PRIMARY KEY (id),
                FOREIGN KEY (author_id) REFERENCES authors(id),
                UNIQUE (link)
            );'''
            tag_info = '''create table if not exists tags
            (
                id VARCHAR(36) NOT NULL,
                tag VARCHAR(16) NOT NULL,
                type INT NOT NULL,
                thumb INT DEFAULT 0,
                PRIMARY KEY (id),
                UNIQUE (tag)
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
            for k, _ in self.lang.items():
                operated = True
                try:
                    add_col = f'''ALTER TABLE datapacks ADD name_{k} TINYTEXT;'''
                    self.cur.execute(add_col)
                except:
                    operated = False
                if operated:
                    print('added "', k, '" colum')
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
    def _tag_insert(self, info: dict):
        tag_sort = [info['source'], info['game_version'], info['tag'], info['keywords']]
        def __exe(_tag: str, _type: int):
            _tag = pymysql.escape_string(_tag)
            tid = uuid.uuid3(uuid.NAMESPACE_DNS, _tag)
            tag_insert = f'''insert into tags (id, tag, type) 
            values ('{tid}', '{_tag}', {_type}) 
            on duplicate key update 
            tag = '{_tag}',
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
    def _title_translate(self, info: dict, default_name = None, pre_title: dict = None):
        # not translated or updated
        updated = pre_title == None or not default_name == info['default_name']
        translator = self.lang[info['default_lang']]['translator']
        i = 0
        for k, v in self.lang.items():
            if k == info['default_lang']: # default language
                continue
            if (updated or pre_title[i] == None or pre_title[i] == '') and ('title_' + k not in info or info['title_' + k] in [None, '', 'auto']):
                # (haven't translated or title updated) and (haven't got title or need to be translated)
                if 'youdao' in translator and k in translator['youdao']['to']:
                    info['title_' + k] = youdao_translate(info['title_' + info['default_lang']], translator['youdao']['from'], translator['youdao']['to'][k])
                elif 'google' in translator and k in translator['google']['to']:
                    print(1)
            i += 1
    def _incremental_update(self, info: dict, previous: list):
        if info['post_time'] == info['update_time']:
            info['post_time'] = info['update_time'] = previous[0]
        self._title_translate(info, previous[1], previous[2:])
    def _datapack_insert(self, info: dict):
        aid = self._author_insert(info)
        assert not aid == None
        did = uuid.uuid3(uuid.NAMESPACE_DNS, info['link'])
        self.cur.execute("select post_time, default_name, " + ','.join(["name_" + k for k, _ in self.lang.items()]) + f" from datapacks where id = '{did}'")
        res = self.cur.fetchall()
        exists = [j for i in res for j in i] if not res == None else []
        if not exists.__len__() == 0:
            self._incremental_update(info, exists) #incremental_update
        if exists.__len__() == 0: # new element
            self._title_translate(info)
        intro = pymysql.escape_string('\n'.join(info['summrization'])) #escape summaries
        content_raw = pymysql.escape_string(info['content_raw']) #escape content
        for k, _ in self.lang.items():
            info['title_' + k] = pymysql.escape_string(info['title_' + k])
        datapack_insert = f'''insert into datapacks (id, link, {' '.join([f"name_{k}," for k, _ in self.lang.items()])} author_id, default_lang, default_name, intro, full_content, source, post_time, update_time) 
        values ('{did}', '{info['link']}', {",".join(["'" + info["title_" + k] + "'" for k, _ in self.lang.items()])}, '{aid}', '{info['default_lang']}', '{info['default_name']}', '{intro}', '{content_raw}', '{info['source']}', '{info['post_time']}', '{info['update_time']}') 
        on duplicate key update 
        link = '{info['link']}',
        {"".join(["name_" + k + " = '" + info["title_" + k] + "'," for k, _ in self.lang.items()])}
        author_id = '{aid}',
        default_lang = '{info['default_lang']}',
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
