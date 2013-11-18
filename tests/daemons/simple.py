#! /usr/bin/python
import sys
import time
import logging
import os

sys.path.append('/vagrant/Python/ProcessMaster')

from upstart.daemon import Daemon


log = logging.getLogger('test')
handler = logging.FileHandler('/vagrant/Python/ProcessMaster/tests/daemons/logs/daemon-test.log')
handler.setFormatter(logging.Formatter('%(asctime)s %(process)d/%(thread)d %(levelname)s %(message)s'))
handler.setLevel(logging.DEBUG)
log.addHandler(handler)
logging.root.setLevel(logging.DEBUG)



class MyDaemon(Daemon):
    def run(self, param='default'):
        while True:
            print "running"
            log.debug("param=%s", param)
            log.debug('running')
            time.sleep(1)


if __name__ == '__main__':
    MyDaemon(
        log=log,
        pidfile=os.path.abspath('/vagrant/Python/ProcessMaster/tests/daemons/run/daemon-test.pid'),
        stop_timeout=1
    ).execute()