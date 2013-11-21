# -*- coding: utf-8 -*-
import sys, os, atexit
import inspect
import signal
import pwd
import time
import optparse
import re
from multiprocessing import Process

from .processes import ProcessManager


class Daemon(object):
    """
    Usage: subclass the Daemon class and override the run() method
    """
    def __init__(self,
                 log,
                 pidfile=None,
                 user=None,
                 stop_timeout=5,
                 terminate_signal=signal.SIGTERM,
                 kill_signal=signal.SIGKILL,
                 reload_signal=signal.SIGHUP,
                 stdin='/dev/null',
                 stdout='/dev/null',
                 stderr='/dev/null'):
        self.log = log
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.default_pidfile = pidfile is not None
        self.pidfile = pidfile
        self.user = user

        self.stop_timeout = stop_timeout

        self._manager = None
        self.DEBUG = False
        self.run_args = {}

        self.terminate_signal = terminate_signal
        self.kill_signal = kill_signal
        self.reload_signal = reload_signal
        self._set_signals_hooks()

    def _set_signals_hooks(self):
        signal.signal(self.reload_signal, self._sighup_hook)
        signal.signal(self.terminate_signal, self._sigterm_hook)

    def _sighup_hook(self, signum, frame):
        self.reload()

    def _sigterm_hook(self, signum, frame):
        self.pre_stop()
        self.delpid()
        sys.exit(0)

    @property
    def manager(self):
        if not self._manager:
            self._manager = ProcessManager()
        return self._manager

    def _set_user(self):
        pw_record = pwd.getpwnam(self.user)
        user_uid = pw_record.pw_uid
        user_gid = pw_record.pw_gid
        os.setgid(user_gid)
        os.setuid(user_uid)

    def _write_pidfile(self, pid):
        fpid = open(self.pidfile, 'w+')
        fpid.write("%s\n" % pid)
        fpid.close()
        self.log.debug('created pidfile %s' % self.pidfile)

    def daemonize(self):
        try:
            pid = os.fork()
            if pid > 0:
                # exit first parent
                sys.exit(0)
        except OSError, e:
            sys.stderr.write("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

        if self.user:
            self._set_user()

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
        self._write_pidfile(pid)
        atexit.register(self.delpid)

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
        if os.path.exists(self.pidfile):
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
        Don't override!
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
            self.run(**self.run_args)

    def terminate(self, pid, force=False):
        try:
            stop_time = time.time()
            while True:
                if force or time.time() - stop_time > self.stop_timeout:
                    os.kill(pid, self.kill_signal)
                else:
                    os.kill(pid, self.terminate_signal)
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
        Don't override!
        Stop the daemon
        """
        pid = self.pid

        if pid:
            self.log.debug('stopping...')
            terminated = self.terminate(pid, force)
            if terminated:
                self.log.debug('stopped')
                self.post_stop()
                self.log.debug('post stopping...')
                print 'stopped'
            else:
                print 'cannot stop process (%s)' % pid
        else:
            print 'not running'

        self.delpid()

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
        Don't override!
        Restart the daemon
        """
        self.stop()
        return self.start()

    def _reload(self):
        if not self.pid:
            print 'stopped'
        else:
            process = self.manager.get(self.pid)
            if process:
                process.signal(self.reload_signal)
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
        found_processes = set(self.manager.find(self.get_grepline()))
        running_process = self.manager.get(os.getpid())
        running_processes = set(running_process.ancestors)
        running_processes.add(running_process)
        found_processes = found_processes - running_processes

        if self.pid:
            process = self.manager.get(self.pid)
            if process:
                found_processes.remove(process)
                return found_processes - set(process.descendants)
            else:
                return found_processes
        else:
            return found_processes

    def status(self):
        '''
        Don't override!
        @param args tuple (key, value)
        '''
        result = False
        pid = self.pid
        if pid is None:
            print 'stopped'
            result = True
        else:
            process = self.manager.get(pid)
            if process is None:
                print "process with pid {pid} not found".format(pid=pid)
            else:
                if re.search(self.get_grepline(), process.cmdline):
                    self.manager.get(self.pid)
                    print 'running ({pid})'.format(pid=self.pid)
                    result = True
                else:
                    print "pid {pid} is found but it belongs to another process".format(pid=pid)

        lost_processes = self.get_lost_processes()
        if lost_processes:
            result = False
            print 'lost pids: %s' % ','.join([str(process.pid) for process in lost_processes])
        return result

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
        optparser = optparse.OptionParser()
        optparser.set_usage('Usage: {daemon} [options] (start|stop|stop-force|restart|reload|status)'.format(daemon=daemon))

        if len(sys.argv) < 2:
            optparser.print_usage()
            sys.exit(1)

        command_args = inspect.getargspec(self.run)
        arg_names = command_args.args[1:]
        args = {}

        if command_args.defaults:
            for i in xrange(len(command_args.defaults), 0, -1):
                args[arg_names[-i]] = command_args.defaults[-i]

        if not self.default_pidfile:
            optparser.add_option('-p', '--pid', dest='pid', help='destination of a pid file')
        optparser.add_option('-d', '--debug', action="store_true", dest='debug', default=False, help='debug mode')

        for arg_name in arg_names:
            try:
                if isinstance(args[arg_name], bool):
                    if args[arg_name]:
                        optparser.add_option('--%s' % arg_name, action='store_false', default=args[arg_name],
                                             dest=arg_name, help=arg_name)
                    else:
                        optparser.add_option('--%s' % arg_name, action='store_true', default=args[arg_name],
                                             dest=arg_name, help=arg_name)
                else:
                    optparser.add_option('--%s' % arg_name, dest=arg_name, default=args[arg_name], help=arg_name)
            except KeyError:
                optparser.add_option('--%s' % arg_name, dest=arg_name, help=arg_name)

        options, _ = optparser.parse_args()
        if not self.default_pidfile:
            self.pidfile = getattr(options, 'pid')
            if not self.pidfile:
                optparser.error('pid file must be specified')

        for arg_name in arg_names:
            if arg_name not in args and getattr(options, arg_name) is None:
                optparser.error('%s must be specified' % arg_name)
            else:
                self.run_args[arg_name] = getattr(options, arg_name)

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


class DaemonMaster(Daemon):
    pass


class DaemonWorker(Process):
    pass
