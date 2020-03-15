import urllib.request
import urllib.parse
import json

def youdao_translate(content: str, fr: str, to: str):
    youdao_url = 'http://fanyi.youdao.com/translate?smartresult=dict&smartresult=rule'
    data = {}
    data['i'] = content
    data['from'] = fr
    data['to'] = to
    data['smartresult'] = 'dict'
    data['client'] = 'fanyideskweb'
    data['salt'] = '15821192574364'
    data['sign'] = '1c9ccf293aab785a5da3a06afd190eda'
    data['doctype'] = 'json'
    data['version'] = '2.1'
    data['keyfrom'] = 'fanyi.web'
    data['action'] = 'FY_BY_CLICKBUTTION'
    data['typoResult'] = 'false'
    try:
        data = urllib.parse.urlencode(data).encode('utf-8')
        youdao_response = urllib.request.urlopen(youdao_url, data)
        youdao_html = youdao_response.read().decode('utf-8')
        target = json.loads(youdao_html)
    except:
        print('error')
        return ''
    trans = target['translateResult']
    lines = []
    for i in range(len(trans)):
        for j in range(len(trans[i])):
            line = trans[i][j]['tgt']
        lines.append(line)
    print('translated title "', content, '"')
    return '\n'.join(lines)
