import os, json, pymysql, math
from PIL import Image, ImageDraw, ImageFont
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

info = {}

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
    _img = Image.open(_img).resize(size)
    img.paste(_img, pos)

def get_info(info: dict):
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
    cur.execute(f"select default_name from datapacks order by post_time desc limit 1;")
    res = cur.fetchall()
    info['post'] = res[0][0]

def text_api(info: dict):
    for k, v in info.items():
        with open(BASE_DIR + '/bin/stats/' + k, 'w+', encoding='utf-8') as f:
            f.write(str(v))

def banner(info: dict):
    font = ImageFont.truetype(BASE_DIR + '/bin/font/Minecraft.ttf', 12)
    small_font = ImageFont.truetype(BASE_DIR + '/bin/font/Minecraft.ttf', 8)
    text_font = ImageFont.truetype(BASE_DIR + '/bin/font/unifont.ttf', 14)
    num_color = (185, 62, 174, 196)
    website_color = (144, 101, 144, 196)
    img = Image.new('RGBA', (800, 24 + 8))
    add_text(img, (0, 20), 'datapacks.space', website_color, small_font)
    add_text(img, (100, 0), 'Latest:', website_color, small_font)
    add_text(img, (120, 12), info['post'], (185, 62, 174, 216), text_font, max_width=400)
    add_img(img, (800 - 200 - 32, 0), (32, 32), BASE_DIR + '/bin/img/css/datapack_default.png')
    add_text(img, (800 - 200 - 32, 0), info['datapacks'], num_color, font, align='right')
    add_img(img, (800 - 100 - 32 - 4, 0 - 4), (40, 40), BASE_DIR + '/bin/img/css/stats_author.png')
    add_text(img, (800 - 100 - 32, 0), info['authors'], num_color, font, align='right')
    add_img(img, (800 - 0 - 32 + 2, 0 + 2), (28, 28), BASE_DIR + '/bin/img/css/stats_tag.png')
    add_text(img, (800 - 0 - 32, 0), info['tags'], num_color, font, align='right')
    img.save(BASE_DIR + '/bin/stats/banner.png', 'png')

get_info(info)
text_api(info)
banner(info)
