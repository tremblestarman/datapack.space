import os, json, pymysql, math, requests, io, urllib
from PIL import Image, ImageDraw, ImageFont
from urllib.parse import urljoin
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

if not os.path.exists(BASE_DIR + '/bin/stats'):  # create stats folder
    os.mkdir(BASE_DIR + '/bin/stats')

def add_text(img, pos, text, color, font, align='left', max_width=None):
    draw = ImageDraw.Draw(img)
    text = '' if text == None else str(text)
    def get_width(t):
        return draw.textsize(t, font=font)[0] + font.getoffset(t)[0] if font != None else 0
    w = get_width(text)
    if max_width != None and w > max_width:
        l = 0
        r = len(text)
        while l <= r:
            mid = math.floor((l + r) / 2)
            if get_width(text[:mid] + '...') > max_width:
                r = mid - 1
            else:
                l = mid + 1
        text = text[:r] + '...'
    if align == 'right':
        pos = (pos[0] - w, pos[1])
    elif align == 'center':
        pos = (pos[0] - w / 2, pos[1])
    draw.text(pos, text, fill=color, font=font)
def add_img(img, pos, size, _img):
    _img = Image.open(_img) if type(_img) == str else _img
    _img = _img.resize(size)
    img.paste(_img, pos)

def text_api(info: dict):
    for k, v in info.items():
        with open(BASE_DIR + '/bin/stats/' + k, 'w+', encoding='utf-8') as f:
            f.write(str(v))
# general info
def get_gen_info(info: dict):
    with open(BASE_DIR + '/util/auth.json', 'r', encoding='utf-8') as f:
        auth = json.loads(f.read())
        auth['charset'] = 'UTF8MB4'
        connection = pymysql.connect(**auth)
    cur = connection.cursor()
    cur.execute('use datapack_collection;')
    print('connected database successfully.')
    cur.execute(f"select count(id) from datapacks;")
    res = cur.fetchall()
    info['datapacks'] = res[0][0]
    cur.execute(f"select count(id) from authors;")
    res = cur.fetchall()
    info['authors'] = res[0][0]
    cur.execute(f"select count(id) from tags;")
    res = cur.fetchall()
    info['tags'] = res[0][0]
    cur.execute(f"select default_name, id from datapacks order by post_time desc limit 1;")
    res = cur.fetchall()
    info['post'] = res[0][0]
    info['id'] = res[0][1]
def banner_gen(info: dict):
    font = ImageFont.truetype(BASE_DIR + '/bin/font/Minecraft.ttf', 12)
    small_font = ImageFont.truetype(BASE_DIR + '/bin/font/Minecraft.ttf', 8)
    text_font = ImageFont.truetype(BASE_DIR + '/bin/font/NotoSansCJK-Medium.ttc', 14)
    num_color = (185, 62, 174, 196)
    website_color = (144, 101, 144, 196)
    img = Image.new('RGBA', (700, 24 + 8))
    add_img(img, (3, 3), (16, 16), BASE_DIR + '/bin/icon/datapackspace.ico')
    add_text(img, (1, 14), 'datapack', website_color, small_font)
    add_text(img, (14, 21), '.space', website_color, small_font)
    add_text(img, (50, 0), 'Latest:', website_color, small_font)
    tmp = Image.open(BASE_DIR + '/bin/img/css/datapack_default.png')
    if os.path.exists(BASE_DIR + '/bin/img/cover/' + info['id'] + '.png'):
        tmp = Image.open(BASE_DIR + '/bin/img/cover/' + info['id'] + '.png')
        w, h = tmp.size
        tmp = tmp.crop((w / 2 - h / 2, 0, w / 2 + h / 2, h))
    add_img(img, (68, 12), (20, 20), tmp)
    add_text(img, (94, 9), info['post'], (144, 101, 144, 216), text_font, max_width=336)
    add_img(img, (700 - 200 - 32, 0), (32, 32), BASE_DIR + '/bin/img/css/datapack_default.png')
    add_text(img, (700 - 200 - 32, 0), info['datapacks'], num_color, font, align='right')
    add_img(img, (700 - 100 - 32 - 4, 0 - 4), (40, 40), BASE_DIR + '/bin/img/css/stats_author.png')
    add_text(img, (700 - 100 - 32, 0), info['authors'], num_color, font, align='right')
    add_img(img, (700 - 0 - 32 + 2, 0 + 2), (28, 28), BASE_DIR + '/bin/img/css/stats_tag.png')
    add_text(img, (700 - 0 - 32, 0), info['tags'], num_color, font, align='right')
    img.save(BASE_DIR + '/bin/stats/banner.png', 'png')
gen_info = {}
get_gen_info(gen_info)
text_api(gen_info)
banner_gen(gen_info)

# source info
def get_source_info(info: dict):
    def get_dict_of(source: str):
        info[source] = {}
        cur.execute(f"select count(id) from datapacks where source = '{source}';")
        res = cur.fetchall()
        info[source]['datapacks'] = res[0][0]
        cur.execute(f"select default_name, update_time, id from datapacks where source = '{source}' order by update_time desc limit 1;")
        res = cur.fetchall()
        info[source]['last_update'] = res[0][0]
        info[source]['last_update_time'] = res[0][1]
        info[source]['last_update_id'] = res[0][2]
        cur.execute(f"select default_name, post_time, id from datapacks where source = '{source}' order by post_time desc limit 1;")
        res = cur.fetchall()
        info[source]['last_post'] = res[0][0]
        info[source]['last_post_time'] = res[0][1]
        info[source]['last_post_id'] = res[0][2]
    with open(BASE_DIR + '/util/auth.json', 'r', encoding='utf-8') as f:
        auth = json.loads(f.read())
        auth['charset'] = 'UTF8MB4'
        connection = pymysql.connect(**auth)
    cur = connection.cursor()
    cur.execute('use datapack_collection;')
    print('connected database successfully.')
    for schema in os.listdir(BASE_DIR + '/util/schema'):
        with open(BASE_DIR + '/util/schema/' + schema, 'r', encoding='utf-8') as f:
            obj = json.loads(f.read())
            _id = obj['id']
            info[_id] = {'id': _id}
            get_dict_of(_id)
            info[_id]['name'] = obj['name']
            local = BASE_DIR + '/bin/icon/' + _id + '.ico'
            if os.path.exists(local):
                info[_id]['ico'] = Image.open(local).convert('RGBA')
def banner_source(info: dict):
    font = ImageFont.truetype(BASE_DIR + '/bin/font/Minecraft.ttf', 12)
    small_font = ImageFont.truetype(BASE_DIR + '/bin/font/Minecraft.ttf', 8)
    wb_font = ImageFont.truetype(
        BASE_DIR + '/bin/font/NotoSansCJK-Medium.ttc', 12)
    text_font = ImageFont.truetype(BASE_DIR + '/bin/font/NotoSansCJK-Medium.ttc', 14)
    num_color = (185, 62, 174, 196)
    website_color = (144, 101, 144, 196)
    img = Image.new('RGBA', (700, len(info.items()) * 64))
    add_img(img, (3, len(info.items()) * 64 - 32 + 3), (16, 16), BASE_DIR + '/bin/icon/datapackspace.ico')
    add_text(img, (1, len(info.items()) * 64 - 32 + 14), 'datapack', website_color, small_font)
    add_text(img, (14, len(info.items()) * 64 - 32 + 21), '.space', website_color, small_font)
    def website(wb: dict):
        cols = wb['ico'].getcolors()
        wb_color = cols[1][1] if len(wb['ico'].getcolors()) else cols[0][1]
        add_img(img, (50, y + 4), (24, 24), wb['ico'])
        add_text(img, (76, y + 6), wb['name'], wb_color, wb_font)
        add_img(img, (700 - 0 - 32 + 2, y + 2), (28, 28), BASE_DIR + '/bin/img/css/datapack_default.png')
        add_text(img, (700 - 0 - 32, y), wb['datapacks'], num_color, font, align='right')
        add_text(img, (64, y + 28), 'Latest:', website_color, small_font)
        add_text(img, (110, y + 28), wb['last_post_time'].strftime("%Y-%m-%d %H:%M:%S"), website_color, small_font)
        add_text(img, (384, y + 28), 'Updated:', website_color, small_font)
        add_text(img, (430, y + 28), wb['last_update_time'].strftime("%Y-%m-%d %H:%M:%S"), website_color, small_font)
        def set_cover(pos, size, key):
            tmp = Image.open(BASE_DIR + '/bin/img/css/datapack_default.png')
            if os.path.exists(BASE_DIR + '/bin/img/cover/' + wb[key] + '.png'):
                tmp = Image.open(BASE_DIR + '/bin/img/cover/' + wb[key] + '.png')
                w, h = tmp.size
                tmp = tmp.crop((w / 2 - h / 2, 0, w / 2 + h / 2, h))
            add_img(img, pos, size, tmp)
        add_text(img, (110, y + 28 + 9), wb['last_post'], (144, 101, 144, 216), text_font, max_width=270)
        set_cover((84, y + 28 + 12), (20, 20), 'last_post_id')
        add_text(img, (430, y + 28 + 9), wb['last_update'], (144, 101, 144, 216), text_font, max_width=270)
        set_cover((404, y + 28 + 12), (20, 20), 'last_update_id')
    y = 0
    for k, v in info.items():
        website(v)
        y += 64
    img.save(BASE_DIR + '/bin/stats/website.png', 'png')

source_info = {}
get_source_info(source_info)
banner_source(source_info)
