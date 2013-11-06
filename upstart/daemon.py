# -*- coding: utf-8 -*-
import sys, os, atexit
import inspect
import signal
import time
import optparse
import re

from .processes import ProcessManager


class Daemon(object):
    """
    Usage: subclass the Daemon class and override the run() method
    """
    def __init__(self, log, pidfile=None, stop_timeout=5, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
        self.log = log
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.default_pidfile = pidfile is not None
        self.pidfile = pidfile
        self.stop_timeout = stop_timeout
        self._manager = None
        self.DEBUG = False
        signal.signal(signal.SIGHUP, self._sighup_hook)

    def _sighup_hook(self, signum, frame):
        self.reload()

    @property
    def manager(self):
        if not self._manager:
            self._manager = ProcessManager()
        return self._manager

    def daemonize(self):
        try:
            pid = os.fork()
            if pid > 0:
                # exit first parent
                sys.exit(0)
        except OSError, e:
            sys.stderr.write("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

        # decouple from parent environment
        os.chdir("/")
        os.setsid()
        os.umask(0)

        # do second fork
        try:
            pid = os.fork()
            if pid > 0:
                # exit from second parent
                sys.exit(0)
        except OSError, e:
            sys.stderr.write("fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

        # write pidfile
        pid = str(os.getpid())
        file(self.pidfile,'w+').write("%s\n" % pid)
        atexit.register(self.delpid)
        self.log.debug('created pidfile %s' % self.pidfile)

        #redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        si = file(self.stdin, 'r')
        so = file(self.stdout, 'a+')
        se = file(self.stderr, 'a+', 0)
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())
        self.log.debug('redirect standard file descriptors')

    def delpid(self):
        os.remove(self.pidfile)

    @property
    def pid(self):
        try:
            pidfile = file(self.pidfile,'r')
            pid = int(pidfile.read().strip())
            pidfile.close()
        except (IOError, ValueError):
            pid = None
        return pid

    def start(self, daemonize=True):
        """
        Start the daemon
        """
        if self.pid:
            print "already running (%s)" % self.pid
            sys.exit(1)
        else:
            self.pre_start()
            if daemonize:
                self.daemonize()
            self.log.debug('starting daemon...')
            self.run()

    def terminate(self, pid, force=False):
        try:
            stop_time = time.time()
            while True:
                if force or time.time() - stop_time > self.stop_timeout:
                    os.kill(pid, signal.SIGKILL)
                else:
                    os.kill(pid, signal.SIGTERM)
                time.sleep(0.2)
        except OSError, err:
            err = str(err)
            if err.find("No such process") > 0:
                return True
            else:
                print err
                return False

    def stop(self, force=False):
        """
        Stop the daemon
        """
        pid = self.pid

        if pid:
            self.log.debug('pre stopping...')
            self.pre_stop()
            self.log.debug('stopping...')

            terminated = self.terminate(pid, force)
            if terminated:
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
                self.log.debug('stopped')
                self.pre_stop()
                self.log.debug('post stopping...')
                print 'stopped'
            else:
                print 'cannot stop process (%s)' % pid
        else:
            print 'not running'

        lost_processes = self.get_lost_processes()
        if lost_processes:
            for process in lost_processes:
                terminated = self.terminate(process.pid, force)
                if terminated:
                    print 'stopped lost process (%s)' % process.pid
                else:
                    print 'cannot stop lost process (%s)' % process.pid

    def restart(self):
        """
        Restart the daemon
        """
        self.stop()
        self.start()

    def _reload(self):
        if not self.pid:
            print 'stopped'
        else:
            process = self.manager.get(self.pid)
            if process:
                process.signal(signal.SIGHUP)
                print 'reloaded'
            else:
                print "process with pid {pid} not found".format(pid=pid)

    @property
    def daemon(self):
        return sys.argv[0][sys.argv[0].rfind('/')+1:]

    def get_grepline(self):
        if self.default_pidfile:
            return r'(.*?)%s(\x00)+(.*?)start(\x00)*' % self.daemon
        else:
            return r'(.*?)%s(\x00)+(.*?)%s(.*?)start(\x00)*' % (self.daemon, self.pidfile)

    def get_lost_processes(self):
        fount_processes = set(self.manager.find(self.get_grepline()))
        running_process = self.manager.get(os.getpid())
        running_processes = set(running_process.ancestors)
        running_processes.add(running_process)
        fount_processes = fount_processes - running_processes

        if self.pid:
            process = self.manager.get(self.pid)
            if process:
                fount_processes.remove(process)
                return fount_processes - set(process.descendants)
            else:
                return fount_processes
        else:
            return fount_processes

    def status(self):
        '''
        @param args tuple (key, value)
        '''
        pid = self.pid
        if pid is None:
            print 'stopped'
        else:
            process = self.manager.get(pid)
            if process is None:
                print "process with pid {pid} not found".format(pid=pid)
            else:
                if re.search(self.get_grepline(), process.cmdline):
                    self.manager.get(self.pid)
                    print 'running ({pid})'.format(pid=self.pid)
                else:
                    print "pid {pid} is found but it belongs to another process".format(pid=pid)

        lost_processes = self.get_lost_processes()
        if lost_processes:
            print 'lost pids: %s' % ','.join([str(process.pid) for process in lost_processes])

    def run(self, **kwargs):
        """
        You should override this method when you subclass Daemon. It will be called after the process has been
        daemonized by start() or restart().
        """
        raise NotImplemented

    def pre_start(self):
        '''
        Override it if you need
        '''
        pass

    def pre_stop(self):
        '''
        Override it if you need
        '''
        pass

    def post_stop(self):
        '''
        Override it if you need
        '''
        pass

    def reload(self):
        '''
        Override it if you need
        '''
        pass

    def execute(self):
        daemon = self.daemon
        run_args = inspect.getargspec(self.run)
        arg_names = run_args.args[1:]

        optparser = optparse.OptionParser()
        optparser.set_usage('Usage: {daemon} [options] (start|stop|stop-force|restart|reload|status)'.format(daemon=daemon))
        if not self.default_pidfile:
            optparser.add_option('-p', '--pid', dest='pid', help='destination of a pid file')
        optparser.add_option('-d', '--debug', action="store_true", dest='debug', help='debug mode')
        for arg in arg_names:
            optparser.add_option('--%s' % arg, dest=arg, help=arg)
        options, args = optparser.parse_args()

        if not self.default_pidfile:
            self.pidfile = getattr(options, 'pid')
            if not self.pidfile:
                optparser.error('pid file must be specified')

        self.DEBUG = bool(getattr(options, 'debug'))

        command = sys.argv[-1]
        if command == 'start':
            self.start(daemonize=not self.DEBUG)
        elif command == 'stop':
            self.stop()
        elif command == 'stop-force':
            self.stop(force=True)
        elif command == 'restart':
            self.restart()
        elif command == 'reload':
            self._reload()
        elif command == 'status':
            self.status()
        else:
            optparser.error("command %s is not found" % command)
