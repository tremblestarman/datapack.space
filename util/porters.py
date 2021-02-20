import threading, pymysql, os, urllib, re, json, traceback, socket
from datetime import datetime
from pymysql.converters import escape_string
from urllib.parse import urlparse
from time import sleep
from util.translate import translate
from util.err import logger
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
socket.setdefaulttimeout(30)
class porter(threading.Thread): # porter base structure
    # when cache of 'cache_table' is not empty, call 'port' function
    LOG = logger() # logger
    def __init__(self, cache_table: str, sleep_time=60, log=True, interrupt=False, callback=None):
        '''
        Basic parameters for porter
        cache_table: table storing caches.
        sleep_time: after dealing with all cache, time to sleep waiting for next turn.
        log: whether stores log into '.err'.
        interrupt: whether quit immediately when error occurs.
        callback: callback function with a input of cache dict. called when port function ends.
        '''
        self.cache_table = cache_table
        self.sleep_time = sleep_time
        self.log = log
        self.interrupt = interrupt
        self.callback = callback
        '''
        Connect and get cursor.
        '''
        with open(BASE_DIR + '/languages.json', 'r', encoding="utf-8") as f:
            self.languages = json.loads(f.read())
        with open(BASE_DIR + '/auth.json', 'r', encoding='utf-8') as f:
            auth = json.loads(f.read())
            auth['charset'] = 'UTF8MB4'
            self.connection = pymysql.connect(**auth)
        self.cur = self.connection.cursor(pymysql.cursors.DictCursor)
        self.cur.execute('use datapack_collection;')
        print('connected database successfully.')
        threading.Thread.__init__(self)
    def run(self):
        def port_process(cache: dict):
            # delete all columns where value is NULL or empty
            for k in list(cache.keys()):
                if cache[k] == None or cache[k] == '':
                    del cache[k]
            if self.interrupt: # the process will quit immediately when error occurs
                self.port(cache)
                self.connection.commit()
            else: # the process won't quit when error occurs, but retry or log the error.
                try:
                    self.port(cache)
                    self.connection.commit()
                except Exception as e:  # unfixable problem
                    if self.log:
                        print(f"cannot handle this problem. please check \'/util/err/port_{self.cache_table}.err\'")
                        self.LOG.log(f'port_{self.cache_table}', traceback.format_exc(), process='port')
        self.cur.execute(f"select count(*) as cnt from {self.cache_table};")
        cnt = self.cur.fetchall()[0]['cnt']
        if cnt > 0: # cache table is not empty
            self.cur.execute(f"select * from {self.cache_table};")
            cache_list = self.cur.fetchall()                
            print('totally got', len(cache_list), 'caches in', self.cache_table)
            for i in range(0, len(cache_list)): # port each cache
                print('porting', i + 1, '/', len(cache_list), 'caches in', self.cache_table)
                port_process(cache_list[i])
    def __set_right_exp__(self, value):
        if type(value) == int or type(value) == float:
            return str(value)
        elif type(value) == datetime:
            return f"'{escape_string(value.strftime('%Y-%m-%d %H:%M:%S'))}'"
        else:
            return f"'{escape_string(str(value))}'"
    def cache_pop(self, cache_dict: dict):
        self.cur.execute(f'''delete from {self.cache_table} where {' and '.join([f"{k}={self.__set_right_exp__(v)}" for k, v in cache_dict.items()])};''')
    def port(self, cache_dict: dict):
        # callback function
        if not self.callback == None:
            self.callback(self, cache_dict)

class resource_porter(porter): # resources porter
    '''
    Download cache to local file system.
    '''
    def __init__(self, cache_table: str, sleep_time=60, log=True, interrupt=False, callback=None, resource_dir='', domain_block=[], ignoreFailed=False):
        self.resource_dir = os.path.dirname(BASE_DIR) + f"/bin" if resource_dir == None else resource_dir # set resource directory
        self.domain_block = domain_block # set blocked domain list
        self.ignoreFailed = ignoreFailed # ignore failed record
        porter.__init__(self, cache_table, sleep_time, log, interrupt, callback)
    @func_set_timeout(600) # set timeout for 10 minutes
    def resource_save(self, local_url: str, web_url: str):
        if urlparse(web_url).netloc in self.domain_block: # domain blocked, skip
            print('- porter: \'' + web_url + '\' is in a blocked domain. skipped.')
            return True
        if not os.path.exists(self.resource_dir + '/cover'): # create cover folder
            os.mkdir(self.resource_dir + '/cover')
        if not os.path.exists(self.resource_dir + '/author'): # create avatar folder
            os.mkdir(self.resource_dir + '/author')
        # download process
        def download_img():
            opener = urllib.request.build_opener()
            opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3100.0 Safari/537.36')]
            urllib.request.install_opener(opener)
            urllib.request.urlretrieve(web_url, filename=self.resource_dir + f'/{local_url}')
            print(f'- porter: saved resource: {local_url}.')
        if self.interrupt: # the process will quit immediately when error occurs
            download_img()
            return True
        else: # the process won't quit when error occurs, but retry or log the error.
            try:
                download_img()
                return True
            except Exception as e:
                print(
                      f"- porter: resource download failed! please check \'/util/err/port_{self.cache_table}.err\'")
                if self.log:
                    self.LOG.log(f'port_{self.cache_table}', traceback.format_exc(), process='resource_save', local_url=local_url, web_url=web_url)
        if self.ignoreFailed:
            return True
        return False
    def resource_delete(self, local_url: str):
        # delete process
        def delete_img():
            img = self.resource_dir + f'/{local_url}'
            if os.path.exists(img):
                os.remove(img)
            print(f'- porter: deleted resource: {local_url}.')
        if self.interrupt:
            delete_img()
            return True
        else:
            try:
                delete_img()
                return True
            except Exception as e:
                print(f"- porter: resource delete failed! please check \'/util/err/port_{self.cache_table}.err\'")
                if self.log:
                    self.LOG.log(f'port_{self.cache_table}', traceback.format_exc(
            ), process='resource_delete', local_url=local_url)
        return False
    def port(self, cache_dict: dict):
        # do port operation
        success = False
        if cache_dict['status'] == '+': # save a resource
            success = self.resource_save(cache_dict['local_url'], cache_dict['web_url'])
        elif cache_dict['status'] == '-': # delete a resource
            success = self.resource_delete(cache_dict['local_url'])
        if success: # if operation succeed, then pop it from cache queue
            self.cache_pop(cache_dict)
        # callback function
        if not self.callback == None:
            self.callback(self, cache_dict)

class record_porter(porter):
    '''
    Import cache to database to be used by Web.
    '''
    def __init__(self, cache_table: str, target_table: str, sleep_time=60, log=True, interrupt=False, callback=None, translate_when_insert=True, translate_when_update=True):
        self.target_table = target_table # target table
        self.translate_when_insert = translate_when_insert # whether enable translation when insert
        self.translate_when_update = translate_when_update # whether enable translation when update
        porter.__init__(self, cache_table, sleep_time, log, interrupt, callback)
    def __translated_cache_dict__(self, cache_dict: dict, translate_cols: list):
        for col in translate_cols:
            for lang, _ in self.languages.items():
                try:
                    cache_dict[f"{col}_{lang.replace('-', '_')}"] = translate(cache_dict[f"default_{col}"], lang)
                except Exception as e: # unfixable error (network error or permission error to translation API)
                    print('- unfixable error occurs when translating. see \'translate.err\'')
                    if self.log:
                        self.LOG.log(f'translate', traceback.format_exc(), text=cache_dict[f"default_{col}"], language=lang)
                    return False
        return True
    def record_insert(self, cache_dict: dict, translate_cols: list):
        # translate value of columns in 'translate_cols' into every language
        if not self.__translated_cache_dict__(cache_dict, translate_cols): # translate unsuccessfully
            return False
        # insert
        self.cur.execute(f'''
        insert into {self.target_table}({','.join([i for i, _ in cache_dict.items()])}) values({','.join([f"{self.__set_right_exp__(i)}" for _, i in cache_dict.items()])}) 
        on duplicate key 
        update {','.join([f"{k} = {self.__set_right_exp__(v)}" for k, v in cache_dict.items()])};
        ''')
        return True
    def record_update(self, cache_dict: dict, translate_cols: list):
        # translate value of columns in 'translate_cols' into every language
        if not self.__translated_cache_dict__(cache_dict, translate_cols): # translate unsuccessfully
            return False
        # update
        if not 'id' in cache_dict:
            return False
        self.cur.execute(f'''update {self.target_table} set {','.join([f"{k}={self.__set_right_exp__(v)}" for k, v in cache_dict.items()])} where id = '{cache_dict['id']}';''')
        return True
    def record_delete(self, cache_dict: dict):
        self.cur.execute(f'''delete from {self.target_table} where {' and '.join([f"{k}={self.__set_right_exp__(v)}" for k, v in cache_dict.items()])};''')
        return True
    def port(self, cache_dict: dict):
        # get columns that need to be translated
        translate_cols = []
        for k in cache_dict.keys():
            reg = re.search('^default_(.*)$', k)
            if not reg == None and not reg.groups()[0] in ['lang', 'lang_id']:
                translate_cols.append(reg.groups()[0])
        # do port operation
        tmp_dict = cache_dict.copy() # to remove from cache
        status = cache_dict['status']
        del cache_dict['status']
        success = False
        if status == '+': # insert a record
            success = self.record_insert(cache_dict, translate_cols if self.translate_when_insert else [])
        elif status == '*': # update a record
            success = self.record_update(cache_dict, translate_cols if self.translate_when_update else [])
        elif status == '-': # delete a record
            success = self.record_delete(cache_dict)
        if success: # if operation succeed, then pop it from cache queue
            self.cache_pop(tmp_dict)
        cache_dict['status'] = status # for callback function, recover status
        # callback function
        if not self.callback == None:
            self.callback(self, tmp_dict)
        del tmp_dict
        del cache_dict
