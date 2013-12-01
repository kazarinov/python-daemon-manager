#! /usr/bin/python
import sys
import time
import logging
import os

sys.path.append('/vagrant/Python/ProcessMaster')

from upstart.daemon import Daemon, DaemonMaster, DaemonWorker


log = logging.getLogger('test')
handler = logging.FileHandler('/vagrant/Python/ProcessMaster/tests/daemons/logs/workers-test.log')
handler.setFormatter(logging.Formatter('%(asctime)s %(process)d/%(thread)d %(levelname)s %(message)s'))
handler.setLevel(logging.DEBUG)
log.addHandler(handler)
logging.root.setLevel(logging.DEBUG)


class MyDaemonWorker(DaemonWorker):
    def __init__(self, i):
        super(MyDaemonWorker, self).__init__()
        self.i = i + 1

    def run(self):
        i = 0
        while True:
            log.debug('running worker %s', self.i)
            time.sleep(1)


class MyDaemonMaster(DaemonMaster):
    def get_workers(self):
        workers = []
        for i in xrange(self.workers_number):
            workers.append(MyDaemonWorker(i))
        return workers

    def start_worker(self, worker):
        return MyDaemonWorker(worker.i)

    def run(self, workers=10):
        self.workers_number = workers
        super(MyDaemonMaster, self).run()


if __name__ == '__main__':
    MyDaemonMaster(
        log=log,
        pidfile=os.path.abspath('/vagrant/Python/ProcessMaster/tests/daemons/run/workers-test.pid'),
        stop_timeout=15
    ).execute()