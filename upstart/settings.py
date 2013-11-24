import logging
import signal

DEBUG = False

SETTINGS_MANAGER = {
    'log': {
        'dir': '/var/log/daemon-manager/',
        'filename': 'daemon-runtime.log',
        'level': logging.DEBUG
    },
    'configs': '/etc/daemon-manager',
    'pid': '/var/run/daemon-manager.pid',
    'sleep': 5,
    'defaults': {
        'timeouts': {
            'start': 2,
            'stop': 5
        },
        'respawn': {
            'limit': 0,
            'interval': 5
        },
        'expect': False,
        'signals': {
            'terminate': signal.SIGTERM,
            'kill': signal.SIGKILL,
            'reload': signal.SIGHUP
        }
    }
}

SETTINGS_TOOLS = {
    'log': {
        'dir': '/var/log/daemon-manager/',
        'filename': 'daemon-tools.log',
        'level': logging.DEBUG
    },
}

if DEBUG:
    SETTINGS_MANAGER['log']['dir'] = '/vagrant/Python/ProcessMaster/tests/daemons/logs/'
    SETTINGS_MANAGER['configs'] = '/vagrant/Python/ProcessMaster/tests/configs'
    SETTINGS_MANAGER['pid'] = '/vagrant/Python/ProcessMaster/tests/daemons/run/daemon-manager.pid'

    SETTINGS_TOOLS['log']['dir'] = '/vagrant/Python/ProcessMaster/tests/daemons/logs/'
