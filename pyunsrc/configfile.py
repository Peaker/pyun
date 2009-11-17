import os
import paths
import DictAttrAccessor
from util import exec_python_file

def save(modulename, config):
    filename = modulename + '.py'
    items = config.items()
    items.sort()
    config_file = open(filename, 'w')
    config_file.write('config = dict(\n')
    for name, value in items:
        config_file.write('    %s = %r,\n' % (name, value))
    config_file.write(')\n')
    config_file.close()
    return filename

def load(modulename):
    filename = modulename + '.py'
    if os.path.isfile(filename):
        config = exec_python_file(filename)['config']
    else:
        config = __import__('pyunsrc.default%s' % (modulename,), {}, {}, ['']).config
    return config

config_modulename = 'config'
net_config_modulename = 'netconfig'

def save_config(config):
    return save(config_modulename, DictAttrAccessor.dict(config))

def save_net_config(net_config):
    return save(net_config_modulename, net_config)

config = DictAttrAccessor.DictAttrAccessor(load(config_modulename))
default_net_config = load(net_config_modulename)
