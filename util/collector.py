#!/usr/bin/python3
'''
Datapack Info Collector.
'''
import os, json, requests, lxml, re, bs4, random, time, math, datetime
from bs4 import BeautifulSoup, element
from urllib import parse as urlparse
from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver import ActionChains
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from textrank4zh import TextRank4Keyword, TextRank4Sentence
from multiprocessing.dummy import Pool as thread_pool
from util.err import logger
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
headers = [
    "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.153 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:30.0) Gecko/20100101 Firefox/30.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.75.14 (KHTML, like Gecko) Version/7.0.3 Safari/537.75.14",
    "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.2; Win64; x64; Trident/6.0)",
    'Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.8.1.11) Gecko/20071127 Firefox/2.0.0.11',
    'Opera/9.25 (Windows NT 5.1; U; en)',
    'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)',
    'Mozilla/5.0 (compatible; Konqueror/3.5; Linux) KHTML/3.5.5 (like Gecko) (Kubuntu)',
    'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.0.12) Gecko/20070731 Ubuntu/dapper-security Firefox/1.5.0.12',
    'Lynx/2.8.5rel.1 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/1.2.9',
    "Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.7 (KHTML, like Gecko) Ubuntu/11.04 Chromium/16.0.912.77 Chrome/16.0.912.77 Safari/535.7",
    "Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:10.0) Gecko/20100101 Firefox/10.0 "
]
class UrlChangeTimeOut(Exception):
    def __init__(self, *args):
        self.args = args
class datapack_collector:
    '''
    Info Collector following a certain schema.

    Initialization Args:
        schema:
            The schema to be followed. (dict or .json file path)
        refill:
            refill 'post_pool'.
    Attributes:
        post_pool:
            Post links. (urls)
        retry_pool:
            Post links which got error. (urls)
        info_list:
            Infomation collected via the given schema.
            each element is an info_dict.
            STRUCT:
            {
                "link":         # url or domain#xx if embedded in the webpage,
                "source":       # id of the source website,
                "name":         # name of the datapack in default lang
                "name_xx":      # name in xx language,
                "author_uid"    # uid of the author (equals author_name if auto),
                "author_name"   # name of the author,
                "author_avatar" # avator (can be none or auto) (stored locally),
                "version"       # version of the datapack,
                "game_version"  # versions the datapack supports (list),
                "tag"           # tags in the raw post (list),
                "content_raw"   # raw content but adapted,
                "content_filtered"       # content filtered to make summary,
                "cover_img"     # datapack cover (can be none),
                "post_time"     # the post time, (can be auto),
                "update_time"   # the last update time, (can be auto),
                "keywords"      # keywords in content,
                "summarization" # summary of content
            }
        versions:
            All game versions detected.
        schema:
            The schema. (dict)
        sleep:
            Seconds. Sleep to avoid being banned.
        timeout:
            Seconds. Time for waiting sever call.
        async_count:
            Max count of posts to be processed at the same time.
        retry:
            Times of attempt to reconnect and reprocess posts in 'retry_list'.
    '''
    post_pool = []
    retry_list = []
    info_list = []
    versions = set()
    schema = {}
    sleep = 0.5
    timeout = 5
    async_count = 32
    retry = 2
    LOG = logger()
    schema_err = False
    def __init__(self, schema, refill = False):
        '''
        Args:
            schema: The schema to be followed. Dict or .json file Path.
        '''
        if type(schema) == str:
            with open(schema, 'r', encoding='utf-8') as f:
                self.schema = json.loads(f.read())
        elif type(schema) == dict:
            self.schema = schema
        else:
            return
        if 'sleep' in self.schema:
            self.sleep = self.schema['sleep']
        if 'timeout' in self.schema:
            self.timeout = self.schema['timeout']
        if 'async_count' in self.schema:
            self.async_count = self.schema['async_count']
        if 'retry' in self.schema:
            self.retry = self.schema['retry']
        pool_dir = os.path.dirname(BASE_DIR) + '/util/post_pool'
        if not os.path.exists(pool_dir):
            os.mkdir(pool_dir)
        def post_fill():
            self.__pool_fill()
            with open(BASE_DIR + '/post_pool/' + self.schema['id'] + '.pool', 'w+', encoding='utf-8') as f:
                f.write('\n'.join([i for i in self.post_pool if not i in ['', None]]))
        if refill:
            post_fill()
        else:
            with open(BASE_DIR + '/post_pool/' + self.schema['id'] + '.pool', 'r', encoding='utf-8') as f:
                self.post_pool = [p.strip() for p in f.readlines()]
            if self.post_pool.__len__() == 0:
                post_fill()
        print('totally got', self.post_pool.__len__(), 'from', self.schema['id'] + '.')
    def analyze_all(self, interrupt = False):
        '''
        Analyze posts in 'post_pool'. Only analyze first few posts not exceeding 'async_count'.

        Args:
            interrupt: 
                for Debug, which means halt when error occurs.
        '''
        # first analyze
        print(self.schema['id'], ': start analyze.')
        self.__async_analyze(self.post_pool[:self.async_count], interrupt)
        del self.post_pool[:self.async_count]
        print(self.schema['id'], ': got ', self.info_list.__len__(), '.')
        # pause
        if self.post_pool.__len__() > 0:
            print(self.schema['id'], ': reach max async count, paused.\nnot finish yet. still have',
                  self.post_pool.__len__(), '.')
        else:
            print(self.schema['id'], ': collect finished.')
        # retry
        if self.retry_list.__len__() > 0:
            for retry_count in range(1, self.retry + 1):
                current_retry = self.retry_list.__len__()
                print(self.schema['id'], ':', str(retry_count), 'retry. still have', current_retry, 'posts with error.')
                self.__async_analyze(self.retry_list, interrupt)
                del self.retry_list[:current_retry]
                if self.retry_list.__len__() == 0:
                    print(self.schema['id'], ': retry finished and analyzed successfully.')
                    break
            if self.retry_list.__len__() > 0:
                self.__retry_failed()
    def __async_analyze(self, target_list: list, interrupt = False):
        def analyze(post):
            def _anl_():
                post_i = {}
                if self.schema['post_type'] == 'url':
                    post_i = self.__post_analyze(post, self.schema['domain'])
                else:
                    post_i = self.__post_analyze(post)
                if not 'name' in post_i or post_i['name'] in [None, '']:  # invalid datapack
                    print('error: datapack name cannot be null (may be 404)')
                    return
                self.info_list.append(post_i)
            if interrupt:
                _anl_()
            else:
                try:
                    _anl_()
                except Exception as e:
                    print(post, ':', 'got error :', e)
                    self.retry_list.append(post)
            self.current += 1
            print('done', self.current, '/', str(self.total))
        self.current = 0
        self.total = target_list.__len__()
        pool = thread_pool()
        pool.map(analyze, target_list)
        pool.close()
        pool.join()
        del self.current
        del self.total
    def __retry_failed(self):
        print(self.schema['id'], ': retry finished but', self.retry_list.__len__(), 'failed.')
        print('please check \'/util/err/post.err\'')
        for p in self.retry_list: # out put to log
            self.LOG.log('post', Exception('Retry error'), link=p, domain=self.schema['domain'])
        self.retry_list.clear()
    def __get_header(self):
        global headers
        return {'user-agent': random.choice(headers)}
    def __setnext__(self, k: str, v):
        n, i = k, 0
        if '.' in k:
            p = re.findall('^(.*)\.(.*)$', k)
            if (p.__len__() > 0):
                n = p[0][0]
                i = int(p[0][1]) if p[0].__len__() > 1 and not p[0][1] == '' else -1
        _next = (n, v, i)
        return _next
    def __search(self, target, next: tuple):
        '''
        Use schema to find the target.

        Args:
            target:
                A BeatifulSoup object.
            next:
                A tuple with 2 or 3 elements. (str, dict, [int])
                - str is the html element name.
                - dict is the schema to be followed. (html-structure-like dict)
                - int is the index to be selected.
        '''
        if target is None:
            return None
        _attrs = {}
        _loc = ''
        for k, v in next[1].items():
            if type(v) == dict:
                _next = self.__setnext__(k, v)
            elif re.findall('^__.*__$', k).__len__() == 1:
                _loc = v
            else:
                _attrs[k] = re.compile(str(v))
        if _loc != '': # found
            def result(t):
                if t is None:
                    return ''
                elif _loc == '.':
                    if t.string is None:
                        return str(t)
                    else:
                        return str(t.string)
                else:
                    return t.get(_loc)
            t = target.find(next[0], attrs=_attrs)
            if next.__len__() > 2 and not next[2] == 0:
                pool = list(target.find_all(next[0], attrs=_attrs))
                if pool.__len__() > next[2] and next[2] > 0:  # certain index
                    t = pool[next[2]]
                elif next[2] < 0: # all
                    t = pool
            if type(t) == list:
                res = []
                for _t in t:
                    res.append(result(_t))
                return res
            else:
                return result(t)
        if next.__len__() == 2 or next[2] == 0: # first
            return self.__search(target.find(next[0], attrs=_attrs), _next)
        else:
            pool = target.find_all(next[0], attrs=_attrs)
            if pool.__len__() > next[2] and next[2] > 0: # certain index
                return self.__search(pool[next[2]], _next)
            elif next[2] < 0: # all
                back = []
                for p in pool:
                    _ = self.__search(p, _next)
                    if type(_) == str:
                        back.append(_)
                    elif type(_) == list:
                        back += _
                return back
        return []
    def __trim(self, post: dict):
        '''
        Use schema to trim results.

        Args:
            post:
                The dict as a collection of all desired information in a post.
        '''
        if not 'info_refine' in self.schema:
            return
        for k, v in self.schema['info_refine'].items():
            if not k in post:
                continue
            if not type(v) == dict:
                continue
            if post[k] is None:
                post[k] = ''
            for n, p in v.items():
                if 'replace' in n: # replace fields
                    def rep(p):
                        post[k] = re.sub(p['from'], p['to'], post[k])
                    if p == list:
                        for i in p:
                            rep(i)
                    else:
                        rep(p)
                elif 'regex' in n: # regex match and output using defined form
                    r = re.compile(p['from'])
                    if type(post[k]) == list:
                        post[k] = ' '.join(post[k])
                    _m = r.findall(post[k])
                    m = []
                    for _ in _m:
                        if type(_) == tuple:
                            m += list(_)
                        else:
                            m.append(_)
                    _n = int((len(p['to']) - len(p['to'].replace(r'%s',''))) / len(r'%s'))
                    if _n > 1:
                        post[k] = [p['to'] % tuple(m[i * _n: _n]) for i in range(math.floor(m.__len__() / _n))]
                    else:
                        post[k] = [p['to'] % m[i] for i in range(math.floor(m.__len__()))]
                    if 'regexs' in n:
                        post[k] = post[k][0] if post[k].__len__() > 0 else ''
                elif 'remove' in n: # remove fields
                    def rem(p):
                        if type(p) == dict:
                            bs = BeautifulSoup(post[k], "lxml")
                            k1, v1 = tuple(p.items())[0]
                            for k2 in v1:
                                v1[k2] = re.compile(v1[k2])
                            if v1.__len__() == 0:
                                [s.extract() for s in bs.find_all(k1)]
                            else:    
                                [s.extract() for s in bs.find_all(k1, v1)]
                            post[k] = str(bs)
                        elif type(p) == str:
                            post[k] = re.sub(p, '', post[k])
                    if type(p) == list:
                        for t in p:
                            rem(t)
                    else:
                        rem(p)
    def __pool_fill(self):
        '''
        Fill the info_pool.
        '''
        def __pool_fill_one(html, page):
            bs = BeautifulSoup(html, 'lxml')
            for k, v in self.schema['post_path'].items():
                _schem = (k, v)
                break
            _next = self.__setnext__(_schem[0], _schem[1])
            target_pool = [i for i in self.__search(bs, _next) if not i in ['', None]]
            if not target_pool is None and not target_pool.__len__() == 0 and not (self.post_pool.__len__() > 0 and set(target_pool) <= set(self.post_pool)):
                self.post_pool = list(set(self.post_pool) | set(target_pool))
                print(page, ':', 'done.', 'got', target_pool.__len__(), 'elements.')
                return True
            return False
        if 'type' not in self.schema['scan'] or self.schema['scan']['type'] == 'normal':
            def normal_start():
                page = 0 if 'page_start' not in self.schema['scan'] else self.schema['scan']['page_start']
                page_inc = 1 if 'page_increment' not in self.schema['scan'] else self.schema['scan']['page_increment']
                page_max = -1 if 'page_max' not in self.schema['scan'] else self.schema['scan']['page_max']
                while True:
                    url = self.schema['scan']['entrance'].replace(r'$p', str(page))
                    print(page, ':', url, 'start..')
                    to_continue = __pool_fill_one(requests.get(url, headers=self.__get_header(), timeout=self.timeout).text, page)
                    if to_continue:
                        if page_max == -1 or page < page_max:
                            page += page_inc
                        time.sleep(self.sleep)
                    else:
                        break
            try:
                normal_start()
            except Exception as e:
                print('post find error :', e)
                for i in range(1, 6):
                    print('attempt: ', i, ' start.')
                    try:
                        normal_start()
                        break
                    except Exception as _e:
                        print('post find error :', _e)
                        if i == 5:
                            print('attempted but still have error. please check \'/util/err/schema.err\'')
                            self.LOG.log('schema', _e, schema=self.schema['id'])
                            self.schema_err = True
        elif self.schema['scan']['type'] == 'selenium':
            def selenium_start(driver):
                page = 1
                driver.set_page_load_timeout(90)
                driver.set_script_timeout(90)
                driver.get(self.schema['scan']['entrance'])
                print(page, ':', driver.current_url, 'start..')
                to_continue = __pool_fill_one(driver.page_source, page)
                if not to_continue: # no content then retry
                    raise Exception('no content')
                next_xpath = self.schema['scan']['next_xpath']
                try:
                    while True:
                        last_url = driver.current_url
                        actions = ActionChains(driver)
                        WebDriverWait(driver, 1).until(EC.visibility_of_element_located((By.XPATH, next_xpath)))
                        element = driver.find_element_by_xpath(next_xpath)
                        actions.click(element)
                        actions.perform() # click the next button
                        print('clicked', element)
                        del actions
                        try:
                            WebDriverWait(driver, 1).until_not(lambda driver: driver.current_url == last_url)
                            last_url = driver.current_url
                        except Exception as e: # url change time out
                            print(e)
                            raise UrlChangeTimeOut()
                        page += 1
                        print(page, ':', driver.current_url, 'start..')
                        to_continue = __pool_fill_one(driver.page_source, page)
                        if not to_continue:
                            driver.quit()
                            return
                except UrlChangeTimeOut: # if url change time out, then retry
                    print('time out and prepare to retry')
                    self.post_pool.clear() # clear
                    raise Exception('url change time out')
                except Exception as e: # if cannot find the next button, then end
                    print('selenium found end.')
                driver.quit()
            options = webdriver.ChromeOptions()
            prefs = {'profile.default_content_setting_values': { 'images': 2, 'javascript': 2}}
            options.add_experimental_option('prefs', prefs)
            if not 'display' in self.schema['scan'] or self.schema['scan']['display'] == 'headless':
                options.add_experimental_option('excludeSwitches', ['enable-automation'])
                options.add_argument('--headless')
                options.add_argument('--start-maximized')
                options.add_argument('--incognito')
                options.add_argument('--log-level=3')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36")
            elif self.schema['scan']['display'] == 'virtual':
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-gpu')
                display = Display(visible=0, size=(800, 800))
                display.start()
            capabilities = DesiredCapabilities.CHROME.copy()
            capabilities['acceptSslCerts'] = True
            capabilities['acceptInsecureCerts'] = True
            driver = webdriver.Chrome(chrome_options=options, desired_capabilities=capabilities)
            try:
                selenium_start(driver)
            except Exception as e:
                driver.quit()
                print('selenium error :', e)
                for i in range(1, 6):
                    print('attempt: ', i, ' start.')
                    driver = webdriver.Chrome(chrome_options=options, desired_capabilities=capabilities)
                    try:
                        selenium_start(driver)
                        break
                    except Exception as _e:
                        driver.quit()
                        print('selenium error :', _e)
                        if i == 5:
                            print('attempted but still have error. please check \'/util/err/schema.err\'')
                            self.LOG.log('schema', _e, schema=self.schema['id'])
                            self.schema_err = True
            driver.quit()
            if self.schema['scan']['display'] == 'virtual':
                display.stop()
            print('selenium closed.')
    def __post_analyze(self, content: str, domain: str = None):
        '''
        Analyze a post.

        Args:
            content:
                url or html string.
            domain:
                domain url. None if content is a html string.
        '''
        post = {}
        if domain is None:
            post['link'] = domain + '#' + post['name'].replace(' ', '_')
            bs = BeautifulSoup(content, 'lxml')
        else:
            _url = urlparse.urljoin(domain, content)
            bs = BeautifulSoup(requests.get(_url, headers=self.__get_header(), timeout=self.timeout).text, 'lxml')
            post['link'] = _url
        time.sleep(self.sleep)
        print(post['link'], 'scanning..')
        for k, v in self.schema['info_collect'].items():
            if type(v) == dict:
                for _k, _v in v.items():
                    _schem = (_k, _v)
                    break
                if _k == 'selector':
                    el = bs.select(_v)
                    if self.schema['info_collect'][k]['content'] == '.':
                        post[l] = el.string
                    else:
                        post[l] = el.get(self.schema['info_collect'][k]['content'])
                else:    
                    _next = self.__setnext__(_schem[0], _schem[1])
                    post[k] = self.__search(bs, _next)
            else:
                post[k] = v
        self.__post_refine(post)
        return post
    def __summary(self, post: dict):
        '''
        Summarize the post's filtered content.

        Args:
            post:
                The dict as a collection of all desired information in a post.
        '''
        print(post['link'], 'nlp and takes time...')
        trw = TextRank4Keyword()
        trw.analyze(post['content_filtered'], lower=True)
        post['keywords'] = [i.word for i in trw.get_keywords(3)]
        trs = TextRank4Sentence()
        trs.analyze(post['content_filtered'], lower=True)
        post['summary'] = [i.sentence for i in trs.get_key_sentences(2)]
    def __connect_url(self, post:dict):
        '''
        Connect local url.

        Args:
            post:
                The dict as a collection of all desired information in a post.
        '''
        def __connect(t: str):
            html = post[t]
            bs = BeautifulSoup(html, 'lxml')
            for tag in ['href', 'src', 'file']:
                for i in bs.find_all(attrs={tag: re.compile(r'''^(?!www\.|(?:http|ftp)s?://|[A-Za-z]:\\|//).*''')}):
                    i[tag] = urlparse.urljoin(self.schema['domain'], i[tag])
            for img in bs.find_all('img'): # edit img
                if 'file' in img.attrs:
                    img['src'] = img['file']
            post[t] = str(bs)
        __connect('content_raw')
        __connect('content_full')
    def __content_hide(self, post:dict):
        '''
        Hide some information.

        Args:
            post:
                The dict as a collection of all desired information in a post.
        '''
        if 'info_refine' in self.schema and 'content_raw' in self.schema['info_refine'] and 'hide' in self.schema['info_refine']['content_raw']:
            p = self.schema['info_refine']['content_raw']['hide']
            def hide(p): # hide fields (replace with <hide>)
                if type(p) == dict:
                    bs = BeautifulSoup(post['content_raw'], "lxml")
                    _hide = bs.new_tag("hide")
                    k1, v1 = tuple(p.items())[0]
                    for k2 in v1:
                        v1[k2] = re.compile(v1[k2])
                    if v1.__len__() == 0:
                        [s.replace_with(_hide) for s in bs.find_all(k1)]
                    else:
                        [s.replace_with(_hide) for s in bs.find_all(k1, v1)]
                    post['content_raw'] = str(bs)
                elif type(p) == str:
                    post['content_raw'] = re.sub(p, '<hide></hide>', post[k])
            if type(p) == list:
                for t in p:
                    hide(t)
            else:
                hide(p)
        html = post['content_raw']
        bs = BeautifulSoup(html, 'lxml')
        for a in bs.find_all('a'): # hide a
            a.name = 'hide_a'
            if 'href' in a and a.text == a['href']:
                a.string = re.sub('[^\*]', '*', a.text)
            a['href'] = ''
        html = str(bs)
        post['content_raw'] = html
    def __post_adapt(self, post:dict):
        # custome adapater
        '''
        Use schema to adapt results via python code string.
        (variable name is property name, the property is updated with the variable)

        Args:
            post:
                The dict as a collection of all desired information in a post.
        '''
        g = {'bs': BeautifulSoup}
        for k, v in post.items():
            if len(k) > 1 and k[0] == '$':
                var = k.replace('$','').replace('.','')
                if var == '':
                    continue
                g[var] = v
        for k, v in self.schema['info_adapt'].items():
            if not k in post:
                continue
            g[k] = post[k]
            if not type(v) == str:
                continue
            exec(self.schema['info_adapt'][k], g)
            post[k] = g[k]
            del g[k]
    def __post_refine(self, post: dict):
        '''
        Refine the post.

        Args:
            post:
                The dict as a collection of all desired information in a post.
        '''
        ### first refine
        #   - auto image select (the first image in 'content_raw')
        #   - auto content_filtered select (equals 'content_raw')
        #   - using "info_refine" to trim all info
        #   - make 'game_version' and 'tag' and list be standard (to be list with no empty string, if empty then ['other'])
        if not 'cover_img' in self.schema['info_collect'] or self.schema['info_collect']['cover_img'] == 'auto': # auto select cover
            post['cover_img'] = self.__search(BeautifulSoup(post['content_raw'], "lxml"), ('img', { '__img__': 'src' }))
        if not 'content_filtered' in self.schema['info_collect'] or self.schema['info_collect']['content_filtered'] == 'auto': # auto fill content_filtered
            post['content_filtered'] = post['content_raw']
        self.__trim(post)
        post['content_full'] = post['content_raw']
        li = ['game_version', 'tag']
        for k, v in post.items():
            if len(k) > 2 and k[:2] == '$.':
                li.append(k)
        for k, v in post.items():
            if v is None:
                pass
            elif type(v) == str:
                post[k] = v.strip()
            elif k in li and not type(v) == list:
                post[k] = [v]
            elif not k in li and type(v) == list and v.__len__() > 0:
                post[k] = v[0]
            elif not k in li and type(v) == list and v.__len__() == 0:
                post[k] = ''
        for k in li:
            if not k in post or not type(post[k]) == list:
                post[k] = []
            post[k] = [i.lower() for i in post[k] if not i == '']
            post[k] = list(set(post[k]))
        if post['game_version'].__len__() == 0:
            post['game_version'] = ['other']
        ### adapt
        #   - using "info_adapt" to adapt all info
        self.__connect_url(post) # connect relative url in content_raw
        self.__post_adapt(post) # adapt
        self.__content_hide(post) # hide some information
        ### second refine
        #   - make 'content_filtered' be pure text
        #   - get summary of 'content_filtered'
        #   - hide link, resources, video etc. in 'content_raw'
        #   - adjust 'post_time and 'update_time' (if one is empty then equals the other, both empty then equals NOW)
        #   - make 'game_version' and 'tag' be standard (to be list, if empty then ['other'])
        #   - set other property such as 'source', 'default_lang', series of 'default_name' and 'default_tag'
        #   - prevent duplicated post
        if 'content_filtered' in post:
            post['content_filtered'] = BeautifulSoup(post['content_filtered'], "lxml").get_text()
        self.__summary(post)
        del post['content_filtered']
        if post['summary'].__len__() == 0:
            post['summary'] = ['']
        if post['author_uid'] in [None, 'auto', 'none', '']:
            post['author_uid'] = post['author_name']
        if post['post_time'] in [None, 'auto', 'none', '']:
            if post['update_time'] in [None, 'auto', 'none', '']:
                post['post_time'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            else:
                post['post_time'] = post['update_time']
        if post['update_time'] in [None, 'auto', 'none', '']:
            post['update_time'] = post['post_time']      
        post['source'] = self.schema['id'] # set source
        post['default_lang'] = self.schema['lang'] # lang
        post['default_name'] = post['name']
        post['default_tag'] = post['tag']
        post['name_' + self.schema['lang']] = post['name']
        self.versions = self.versions | set(post['game_version'])
    def peek(self):
        '''
        Test tool.

        Return:
            The first info_dict in 'info_list'.
        '''
        if self.info_list.__len__() > 0:
            return self.info_list[0]
        return {}
    def __del__(self):
        if self.retry_list.__len__() > 0:
            self.__retry_failed()
