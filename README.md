python-daemon-manager
====================

python-daemon-manager is a daemon manager and framework that allows you to easily implement daemon managing
functions in dozens lines of code.

It provides easy and flexible API for Python and simplest configuration file you ever seen


Installation
============

At this time installation from debian repository is unavailable, so you need firstly build a package

```bash
sudo apt-get install devscripts debhelper cdbs
git clone git@github.com:kazarinov/python-daemon-manager.git
cd python-daemon-manager
debuild
sudo debi
```

Debian package will be installed and two command line tools will be available:
```bash
sudo daemon-tools list
> No enabled daemons

sudo daemon-runtime status
> running (22693)
```

A motivating example
====================

Here's some extremely simple daemon that was written with the use of Python daemon framework

```python
#!/usr/bin/env python

import time
import logging

from upstart.daemon import Daemon

log = logging.getLogger('test')

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
        pidfile='daemon-test.pid',
        stop_timeout=1
    ).execute()
```

Another motivating example with master-workers paradigm

```python
#!/usr/bin/env python

import time
import logging

from upstart.daemon import DaemonMaster, DaemonWorker

log = logging.getLogger('test')

class MyDaemonWorker(DaemonWorker):
    def __init__(self, i):
        super(MyDaemonWorker, self).__init__()
        self.i = i

    def run(self):
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
        pidfile='workers-test.pid',
        stop_timeout=1
    ).execute()
```

Writing configuration file
==========================

A simpliest example of config 

```yaml
pid: daemon-test.pid 
expect: daemon
run: simple.py start
```

* pid - path to pid file
* expect - (None, fork, daemon) - expecting daemonization mechanizm of running script
* run - path to running script

Put this file to /etc/daemon-manager/conf-enabled/simple-daemon and run

```bash
daemon-tools list
> Following daemons are enabled:
> * simple-daemon
```


```bash
daemon-tools status
> * simple-daemon is stopped
```
 

```bash
daemon-tools start simple-daemon
> starting simple-daemon ... started (22921)
```


```bash
daemon-tools status
> * simple-daemon is running (22921)
```
 
