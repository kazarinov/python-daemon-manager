#! /usr/bin/python
from upstart.daemon import Daemon
import time
import logging
import os

log = logging.getLogger('test')
handler = logging.FileHandler(os.path.abspath('tests/daemons/logs/test.log'))
handler.setFormatter(logging.Formatter('%(asctime)s %(process)d/%(thread)d %(levelname)s %(message)s'))
handler.setLevel(logging.DEBUG)
log.addHandler(handler)
logging.root.setLevel(logging.DEBUG)



class MyDaemon(Daemon):
    def run(self, param=True):
        while True:
            print "running"
            log.debug('running')
            time.sleep(1)


if __name__ == '__main__':
    MyDaemon(log, os.path.abspath('tests/daemons/run/test.pid'), stop_timeout=1).execute()