import logging

DEBUG = True

SETTINGS_MANAGER = {
    'log': {
        'dir': '/var/log/',
        'filename': 'daemon-manager.log',
        'level': logging.DEBUG
    },
    'configs': '/etc/daemon-manager',
    'pid': '/var/run/daemon-manager.pid',
    'sleep': 5
}

SETTINGS_TOOLS = {
    'log': {
        'dir': '/var/log/',
        'filename': 'daemon-tools.log',
        'level': logging.DEBUG
    },
}

if DEBUG:
    SETTINGS_MANAGER['log']['dir'] = 'tests/daemons/logs/'
    SETTINGS_MANAGER['configs'] = 'tests/configs'
    SETTINGS_MANAGER['pid'] = 'tests/daemons/run/daemon-manager.pid'

    SETTINGS_TOOLS['log']['dir'] = 'tests/daemons/logs/'
