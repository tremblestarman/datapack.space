import os, datetime
BASE_DIR = os.path.dirname(__file__)
ERR_DIR = BASE_DIR + '/err'
if not os.path.exists(ERR_DIR):
    os.mkdir(ERR_DIR)

class logger:
    '''
    Output error to .err file in '/util/err'
    '''
    def log(self, type: str, err: Exception, **kwargs):
        with open(ERR_DIR + '/' + type + '.err', 'a+', encoding='utf-8') as f:
            f.write('--------\n')
            f.write('At ' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ';\n')
            for k, v in kwargs.items():
                f.write(k + '=' + str(v) + ';\n')
            f.write('error=' + str(err))
