# -*- coding: utf-8 -*-
import logging
import optparse
import sys
from .manager import Manager
from .settings import SETTINGS_TOOLS, SETTINGS_MANAGER

log = logging.getLogger('')
handler = logging.FileHandler(SETTINGS_TOOLS['log']['dir'] + SETTINGS_TOOLS['log']['filename'])

handler.setFormatter(logging.Formatter('%(asctime)s %(process)d/%(thread)d %(levelname)s %(message)s'))
handler.setLevel(SETTINGS_TOOLS['log']['level'])
log.addHandler(handler)
logging.root.setLevel(SETTINGS_TOOLS['log']['level'])


class CLI(object):
    def __init__(self):
        self.manager = Manager(SETTINGS_MANAGER.get('configs'))
        self.optparser = optparse.OptionParser()
        self.optparser.set_usage("Usage: daemon-tools (start|stop|restart|reload|list|status) [name]")

    def list(self):
        if not self.manager.daemons:
            print 'No enabled daemons'
        else:
            print 'Following daemons are enabled:'
            for daemon_name in self.manager.daemons.iterkeys():
                print ' * ' + daemon_name

    def start(self, name):
        if name == 'all':
            for daemon_name in self.manager.daemons.iterkeys():
                print ' * starting %s ...' % daemon_name,
                try:
                    pid = self.manager.start(daemon_name)
                    if pid:
                        print 'started (%s)' % pid
                except Exception:
                    print 'not started'
                    sys.exit(1)
        elif name in self.manager.daemons:
            print 'starting %s ...' % name,
            pid = self.manager.start(name)
            print 'started (%s)' % pid
        elif name:
            self.optparser.error('name %s is not found' % name)
        else:
            self.optparser.error('name must be specified')

    def stop(self, name):
        if name == 'all':
            for daemon_name in self.manager.daemons.iterkeys():
                print ' * stopping %s ...' % daemon_name,
                self.manager.stop(daemon_name)
        elif name in self.manager.daemons:
            print 'stopping %s ...' % name,
            self.manager.stop(name)
        elif name:
            self.optparser.error('name %s is not found' % name)
        else:
            self.optparser.error('name must be specified')

    def restart(self, name):
        if name == 'all':
            for daemon_name in self.manager.daemons.iterkeys():
                print ' * restarting %s ...' % daemon_name,
                pid = self.manager.restart(daemon_name)
                print 'restarted (%s)' % pid
        elif name in self.manager.daemons:
            print 'restarting %s ...' % name,
            pid = self.manager.restart(name)
            print 'restarted (%s)' % pid
        elif name:
            self.optparser.error('name %s is not found' % name)
        else:
            self.optparser.error('name must be specified')

    def status(self, name):
        if name in self.manager.daemons:
            print '%s is' % name,
            self.manager.status(name)
        elif name is None or name == 'all':
            for daemon_name in self.manager.daemons.iterkeys():
                print ' * %s is' % (daemon_name,),
                self.manager.status(daemon_name)
        else:
            self.optparser.error('name %s is not found' % name)

    def reload(self, name):
        if name in self.manager.daemons:
            print 'reloading %s ... ' % name,
            pid = self.manager.reload(name)
        elif name:
            self.optparser.error('name %s is not found' % name)
        else:
            self.optparser.error('name must be specified')

    def execute(self):
        if len(sys.argv) < 2:
            self.optparser.print_usage()
            sys.exit(1)

        command = sys.argv.pop(1)
        try:
            name = sys.argv.pop(1)
        except IndexError:
            name = None

        options, _ = self.optparser.parse_args()

        if command=='start':
            self.start(name)
        elif command=='stop':
            self.stop(name)
        elif command=='status':
            self.status(name)
        elif command=='restart':
            self.restart(name)
        elif command=='reload':
            self.reload(name)
        elif command=='list':
            self.list()
        else:
            self.optparser.error('command %s is not found' % name)
