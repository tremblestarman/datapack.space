import time
from emoji import demojize
from util.err import logger
from translators import GoogleV2
from unicodedata import normalize
DISABLE_TRANSLATE = False
LIMIT = 25
def __trans__(text: str, lang: str):
    # source code of '__init__.py' in 'translators' is modified which exposes inner class 'GoogleV2', to fix a bug caused by long time use
    ggt = GoogleV2()
    return ggt.google_api(text, from_language='auto', to_language=lang, sleep_seconds=1, if_use_cn_host=True)

current_time = 0
timeout = 60
def translate(text: str, lang: str):
    # with no translation
    global DISABLE_TRANSLATE
    if DISABLE_TRANSLATE:
        return text
    # translate and update counter
    def __check_limit():
        global current_time
        global timeout
        if current_time >= LIMIT:
            print('- translate: sleep to prevent being banned. (wait ' + str(timeout) + 's)')
            time.sleep(timeout)
            current_time = 0
        current_time += 1  # times add 1
    try: # first try: raw translation
        result = __trans__(text[0:5000], lang) # limit of google translate is 5,000
        __check_limit()
        return result
    except Exception as e: # second try: convert format of encoding (try to dump uft8mb4)
        print(f"- translate: translate '{text}' to '{lang}' error:", e)
        text = demojize(text[0:5000])
        text = normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
        __check_limit()
        # if there is still error, then it would be network connection problem, or being banned from third party API
