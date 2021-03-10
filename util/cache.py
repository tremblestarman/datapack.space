import pymysql, json, os, uuid, urllib, socket, time, unicodedata, traceback
from pymysql.converters import escape_string
from datetime import datetime
from urllib.parse import urlparse
from warnings import filterwarnings
from multiprocessing.dummy import Pool as thread_pool
from func_timeout.exceptions import FunctionTimedOut
from func_timeout import func_set_timeout
from util.err import logger
filterwarnings('ignore',category=pymysql.Warning)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
socket.setdefaulttimeout(30)
class datapack_cache:
    '''
    Datapack cache.
    
    Args:
        retrying_list:
            If function timeout, then retry it in the next turn.
    '''
    retrying_list = [] # retrying buffer
    datapack_removal_list = set() # datapack removal buffer
    author_removal_list = set() # author removal buffer
    tag_removal_list = set() # author removal buffer
    LOG = logger() # logger
    def __init__(self):
        '''
        Connect and get cursor.
        '''
        with open(BASE_DIR + '/auth.json', 'r', encoding='utf-8') as f:
            auth = json.loads(f.read())
            auth['charset'] = 'UTF8MB4'
            self.connection = pymysql.connect(**auth)
        with open(BASE_DIR + '/languages.json', 'r', encoding="utf-8") as f: # read language list
            self.languages = json.loads(f.read())
        self.cur = self.connection.cursor()
        self.cur.execute('use datapack_collection;')
        print('connected database successfully.')
        # preload
        self.cur.execute('select id from datapacks;')
        res = self.cur.fetchall()
        self.datapack_removal_list = set([j for i in res for j in i] if not res is None else [])
        self.cur.execute('select id from authors;')
        res = self.cur.fetchall()
        self.author_removal_list = set([j for i in res for j in i] if not res is None else [])
        self.cur.execute('select id from tags;')
        res = self.cur.fetchall()
        self.tag_removal_list = set([j for i in res for j in i] if not res is None else [])
    def _exist_id(self, table: str, id: str):
        self.cur.execute(f"select id from {table} where id = '{id}';")
        res = self.cur.fetchall()
        return not res is None and not res == ()
    def _changed(self, table: str, id: str, column: str, compare):
        self.cur.execute(f"select {column} from {table} where id = '{id}' and {column} = {self.__set_right_exp__(compare)};")
        res = self.cur.fetchall()
        return res is None or res == ()
    def __set_right_exp__(self, value):
        if type(value) == int or type(value) == float:
            return str(value)
        else:
            return f"'{value}'"
    def _cache_insert(self, table: str, id: str, ess: dict, cmp_table: str, opt: dict, callback=None):
        '''
        Generate sql and status, based on id and columns in 'ess' and 'opt'.
        A column in 'ess' will occurs only when it's a new record.
        A column in 'opt' will occurs either when it's a new record, or its value is not equal to value of the same column in 'cmp_table'.
        Return:
            sql of cache operation, status('+' if it's a new record, '*' if the record is updated, '' if neither).

        +: 'id' not exist.
        *: optional columns in 'opt' dict changed.

        table: sql insert target table.
        id: id of element.
        ess: essential columns.
        cmp_table: sql compare target table.
        opt: optional columns;
        callback: the callback function, which has a input of dict of column-value pairs.
        '''
        is_new = not self._exist_id(cmp_table, id)
        is_updated = False
        res_dict = {}
        if is_new:  # then all columns should be recorded
            ess.update(opt)
            res_dict = ess
        else: # then only optional columns that changed will be recorded
            for k, v in opt.items():
                if self._changed(cmp_table, id, k, v):
                    res_dict[k] = v
                    is_updated = True # if updated, then mark
        res_dict['id'] = id # set id
        if is_new: # new element
            res_dict['status'] = '+'
        elif is_updated: # updated element
            res_dict['status'] = '*'
        else:
            return None, '' # no operation
        if not callback is None:
            callback(res_dict)
        if res_dict is None or len(res_dict.items()) == 0: # after callback, becomes empty
            return None, '' # no operation
        return f'''
        insert into {table}({','.join([i for i, _ in res_dict.items()])}) values({','.join([self.__set_right_exp__(i) for _, i in res_dict.items()])})
        on duplicate key
        update {','.join([f"{k} = {self.__set_right_exp__(v)}" for k, v in res_dict.items()])};
        ''', res_dict['status']
    def _check_datapack_auth(self, did: str, aid: str):
        self.cur.execute(f"select id from authorizations where id = '{did}' and type = 'datapack' union select id from authorizations where id = '{aid}' and type = 'author';")
        res = self.cur.fetchall()
        return not res is None and not res == ()

    def cache_author(self, uid: str, name: str, avatar: str):
        '''
        Cache author info.
        '''
        uid = '-' if uid == '' or uid is None else uid
        aid = str(uuid.uuid3(uuid.NAMESPACE_DNS, uid)) # generate id for author
        if aid in self.author_removal_list: # author exists, so remove it from removal_list
            self.author_removal_list.remove(aid)
        sql, _ = self._cache_insert('authors_cache', aid, {
            'author_uid': escape_string(uid)
        }, 'authors', {
            'author_name': escape_string(name),
            'avatar': escape_string(avatar)
        })
        if not sql is None:
            self.cur.execute(sql) # insert into cache
        return aid
    def cache_tag(self, tag: str, lang: str, lang_id: str, tag_type: str):
        '''
        Cache tag info.
        '''
        tid = str(uuid.uuid3(uuid.NAMESPACE_DNS, tag)) # generate id for tag
        if tid in self.tag_removal_list: # tag exists, so remove it from removal_list
            self.tag_removal_list.remove(tid)
        def verify_type(res_dict):
            if not 'type' in res_dict:
                return
            # if type is changed but is greater than the previous, then keep the previous
            self.cur.execute(f"select type from tags where id = '{tid}' and type < {res_dict['type']};")
            res = self.cur.fetchall()
            if not res is None and not res == ():
                del res_dict['type']
        sql, _ = self._cache_insert('tags_cache', tid, {
            'default_tag': escape_string(tag)
        }, 'tags', {
            'default_lang': escape_string(lang),
            'default_lang_id': escape_string(lang_id),
            'type': tag_type
        }, verify_type)
        if not sql is None:
            self.cur.execute(sql) # insert into cache
        return tid
    def cache_img(self, local_url: str, web_url: str, status: str):
        '''
        Cache image info
        '''
        self.cur.execute(f'''
        insert into images_cache(local_url, web_url, status) values('{local_url}', '{web_url}', '{status}')
        on duplicate key
        update local_url = '{local_url}', web_url = '{web_url}', status = '{status}';
        ''')
    @func_set_timeout(600) # set timeout for 10 minutes
    def cache(self, info: dict):
        '''
        Cache datapack info
        '''
        did = str(uuid.uuid3(uuid.NAMESPACE_DNS, info['link'])) # generate id for datapack
        if did in self.datapack_removal_list: # datapack exists, so remove it from removal_list
            self.datapack_removal_list.remove(did)
        # language
        lang = self.languages[info['default_lang']]['name']
        lang_id = info['default_lang']
        # cache author
        aid = self.cache_author(info['author_uid'], info['author_name'], info['author_avatar'])
        # cache tags
        tag_class = [info['source'], info['game_version'], info['tag'], info['keywords']]
        tag_id = []
        for i in range(0, 4): # for each tag type
            if type(tag_class[i]) == list:
                tag_id += [self.cache_tag(_t, lang, lang_id, i) for _t in tag_class[i]]
            else:
                tag_id.append(self.cache_tag(tag_class[i], lang, lang_id, i))
        # insert datapack
        def set_update_time(res_dict):
            if res_dict['status'] == '+':
                res_dict['update_time'] = info['update_time']
            elif res_dict['status'] == '*': # if 'update_time' is included after spider crawling, let final update time be 'update_time'; if not, generate new
                res_dict['update_time'] = info['update_time'] if not info['update_time'] == info['post_time'] else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        intro = escape_string('\n'.join(info['summary'])) # connect all summaries to form introduction
        sql, status = self._cache_insert('datapacks_cache', did, {
            'link': info['link'],
            'source': info['source'],
            'post_time': info['post_time']
        }, 'datapacks', {
            'default_lang': escape_string(lang),
            'default_lang_id': escape_string(lang_id),
            'default_name': escape_string(info['default_name']),
            'default_intro': '-' if intro is None or intro == '' else intro,
            'author_id': aid,
            # content is related to authorization
            'full_content': escape_string(info['content_full'] if self._check_datapack_auth(did, aid) else info['content_raw']),
        }, set_update_time)
        if not sql is None:
            self.cur.execute(sql) # insert into cache
        # cache datapack-tag relation
        self.cur.execute(f"select tag_id from datapack_tags where datapack_id = '{did}';")
        res = self.cur.fetchall()
        tag_id_old = set([i[0] for i in res] if not res is None and len(res) > 0 else [])
        for tid in tag_id:
            if tid not in tag_id_old: # new relation
                self.cur.execute(f'''
                insert into datapack_tag_relations_cache (datapack_id, tag_id, status) values ('{did}', '{tid}', '+')
                on duplicate key
                update status = '+';
                ''')
            else:
                tag_id_old.remove(tid)
        for tid in tag_id_old: # delete relation
            self.cur.execute(f'''
            insert into datapack_tag_relations_cache (datapack_id, tag_id, status) values ('{did}', '{tid}', '-')
            on duplicate key
            update status = '-';
            ''')
        # cache image
        if not info['author_avatar'] in [None, 'auto', 'none', '']:
            self.cache_img(f"author/{aid}.png", info['author_avatar'], '+')
        if not info['cover_img'] in [None, 'auto', 'none', '']:
            self.cache_img(f"cover/{did}.png", info['cover_img'], '+')
        return did

    def insert(self, info: dict, log=True, interrupt=False):
        self.connection.ping(reconnect=True)
        def insert_process(info: dict):
            did = self.cache(info)
            self.connection.commit()
            print(did, ':', info['link'], 'has been imported into cache successfully.')
        if interrupt: # the process will quit immediately when error occurs
            insert_process(info)
        else: # the process won't quit when error occurs, but retry or log the error.
            try:
                insert_process(info)
            except FunctionTimedOut as e: # if timeout , retry
                print('cache operation timeout')
                self.retrying_list.append(info)
                print('skipped :', info['link'], ', then retry in the next turn.')
            except Exception as e:  # unfixable problem
                if (log):
                    print('cannot handle this problem. please check \'/util/err/cache.err\'')
                    self.LOG.log('cache', traceback.format_exc(), process='insert', link=info['link'])
    def delete_unexisted(self, log=True, interrupt=False):
        self.connection.ping(reconnect=True)
        if len(self.retrying_list) > 0: # then there are datapacks to be retried, so we cannot call remove function
            print('there\'s info in retry_list has not been retried. delete function will run only when retrying list is empty.')
        def delete_process():
            # delete tag
            for tid in self.tag_removal_list:
                self.cur.execute(f"insert into tags_cache(id, status) values('{tid}', '-') on duplicate key update status = '-';") # remove tag
                self.cur.execute(f"insert into datapack_tag_relations_cache(tag_id, status) values('{tid}', '-') on duplicate key update status = '-';") # remove tag relation
            # delete author
            for aid in self.author_removal_list:
                self.cur.execute(f"insert into authors_cache(id, status) values('{aid}', '-') on duplicate key update status = '-';")# remove author
                self.cur.execute(f"insert into images_cache(local_url, status) values('{f'author/{aid}.png'}', '-') on duplicate key update status = '-';") # remove author's avatar
            # delete datapack
            for did in self.datapack_removal_list:
                self.cur.execute(f"insert into datapacks_cache(id, status) values('{did}', '-') on duplicate key update status = '-';") # remove datapack
                self.cur.execute(f"insert into datapack_tag_relations_cache(datapack_id, status) values('{did}', '-') on duplicate key update status = '-';") # remove datapack relation
                self.cur.execute(f"insert into images_cache(local_url, status) values('{f'cover/{did}.png'}', '-') on duplicate key update status = '-';") # remove datapack's cover
        if interrupt: # the process will quit immediately when error occurs
            delete_process()
        else: # the process won't quit when error occurs, but retry or log the error.
            try:
                delete_process()
            except Exception as e:  # unfixable problem
                if (log):
                    print('cannot handle this problem. please check \'/util/err/cache.err\'')
                    self.LOG.log('cache', traceback.format_exc(), process='delete')
    def fill(self, info_list: list, log=True, interrupt=False):
        '''
        Import information from 'info_list' to cache.
        '''
        # combine info_list with retrying_list
        info_list = self.retrying_list + info_list
        self.retrying_list.clear()
        # foreach datapack info, and insert it
        for i in range(0, len(info_list)):
            print(str(i + 1), '/', str(len(info_list)), ':', info_list[i]['link'], '.') # output progress
            info = info_list[i]
            self.insert(info, log, interrupt) # insert a datapack
        # output result
        if len(self.retrying_list) > 0:
            print('end. but still have', str(len(self.retrying_list)), 'to be retried.')
        else:
            print('end and done successfully.')
