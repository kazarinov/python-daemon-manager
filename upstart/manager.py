# -*- coding: utf-8 -*-
import atexit
import stat
import time
import logging
import shlex
import subprocess
import os
import yaml
import sys

from .daemon import Daemon
from .settings import SETTINGS_MANAGER


log = logging.getLogger(__name__)

class Manager(object):
    def __init__(self, conf_path):
        configs_path = conf_path + '/conf-enabled'
        configs = os.listdir(configs_path)

        hooks_path = conf_path + '/hooks'

        self.daemons = {}
        for daemon_name in configs:
            full_config_path = configs_path + '/' + daemon_name

            daemon = DaemonConfiguration.parse(full_config_path)
            pre_start_script = hooks_path + '/pre-start/' + daemon_name
            if os.path.exists(pre_start_script):
                self._make_executable(pre_start_script)
                daemon.pre_start_script = pre_start_script

            pre_stop_script = hooks_path + '/pre-stop/' + daemon_name
            if os.path.exists(pre_stop_script):
                self._make_executable(pre_start_script)
                daemon.pre_stop_script = pre_start_script

            post_stop_script = hooks_path + '/post-stop/' + daemon_name
            if os.path.exists(post_stop_script):
                self._make_executable(post_stop_script)
                daemon.pre_stop_script = post_stop_script

            self.daemons[daemon_name] = daemon

    def _make_executable(self, file_path):
        st = os.stat(file_path)
        os.chmod(file_path, st.st_mode | stat.S_IEXEC)

    def get(self, name):
        return self.daemons[name]

    def start(self, name):
        daemon = self.get(name)
        return daemon.start()

    def stop(self, name):
        daemon = self.get(name)
        return daemon.stop()

    def restart(self, name):
        daemon = self.get(name)
        return daemon.restart()

    def reload(self, name):
        daemon = self.get(name)
        return daemon._reload()

    def status(self, name):
        daemon = self.get(name)
        return daemon.status()


class DaemonConfiguration(Daemon):
    def __init__(self, pidfile,
                 run,
                 user=None,
                 respawn=False,
                 respawn_limit=0,
                 respawn_interval=0,
                 expect=None,

                 start_timeout=SETTINGS_MANAGER['defaults']['timeouts']['start'],
                 stop_timeout=SETTINGS_MANAGER['defaults']['timeouts']['stop'],

                 terminate_signal=SETTINGS_MANAGER['defaults']['signals']['terminate'],
                 kill_signal=SETTINGS_MANAGER['defaults']['signals']['kill'],
                 reload_signal=SETTINGS_MANAGER['defaults']['signals']['reload'],
    ):
        self.run_script = run

        self.respawn = respawn
        self.respawn_limit = respawn_limit
        self.respawn_interval = respawn_interval
        self.expect = expect
        self.crash_number = 0
        self.respawn_time = time.time()
        self.start_timeout = start_timeout

        self.pre_start_script = None
        self.pre_stop_script = None
        self.post_stop_script = None

        log = logging.getLogger()
        super(DaemonConfiguration, self).__init__(
            log, pidfile, user,
            stop_timeout=stop_timeout,
            terminate_signal=terminate_signal,
            kill_signal=kill_signal,
            reload_signal=reload_signal
        )

    def _prepare_run(self):
        if self.user:
            self._set_user()
        os.chdir("/")
        os.setsid()
        os.umask(0)

    def call(self, command):
        args = shlex.split(command)
        popen = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=self._prepare_run)
        popen_process = self.manager.get(popen.pid)

        if not popen_process:
            raise DaemonConfigurationError('cannot run process %s' % command)

        if not self.expect:
            return popen.pid
        else:
            time.sleep(self.start_timeout)
            processes = self.manager.find(self.get_grepline())
            child_pid = None
            for process in processes:
                if process.parent_pid == 1:
                    child_pid = process.pid
                else:
                    raise DaemonConfigurationError('two forked proceesses were found: %s and %s' %
                                                       (child_pid, process.pid))
            log.debug('child_pid %s', child_pid)
            return child_pid

    def get_grepline(self):
        return self.run_script.replace(' ', '\x00')

    def run(self):
        return self.call(self.run_script)

    def start(self, daemonize=False):
        if self.pid:
            print "already running (%s)" % self.pid
            return None
        else:
            self.pre_start()
            self.log.debug('starting daemon...')
            pid = self.run()
            self.log.debug('started daemon (%s)', pid)
            self._write_pidfile(pid)
            return pid

    def pre_stop(self):
        if self.pre_stop_script and os.path.exists(self.pre_stop_script):
            self.call(self.pre_stop_script)

    def post_stop(self):
        if self.post_stop_script and os.path.exists(self.post_stop_script):
            self.call(self.post_stop_script)

    def pre_start(self):
        if self.pre_start_script and os.path.exists(self.pre_start_script):
            self.call(self.pre_start_script)

    @staticmethod
    def parse(conf_path):
        config_file = open(conf_path, 'r')
        try:
            config = yaml.load(config_file)
        except yaml.scanner.ScannerError:
            raise AttributeError('invalid config %s' % conf_path)

        config_file.close()
        pidfile = config.get('pid')
        if not pidfile:
            raise AttributeError('pid attribute is not specified')

        run = config.get('run')
        if not run:
            raise AttributeError('run is not specified')

        respawn_raw = config.get('respawn', SETTINGS_MANAGER['defaults']['respawn'])
        respawn_limit = SETTINGS_MANAGER['defaults']['respawn']['limit']
        respawn_interval = SETTINGS_MANAGER['defaults']['respawn']['interval']
        if isinstance(respawn_raw, dict):
            try:
                respawn_limit = int(respawn_raw.get('limit', respawn_limit))
            except ValueError:
                raise AttributeError('respawn:limit must be integer')

            try:
                respawn_interval = int(respawn_raw.get('interval', respawn_interval))
            except ValueError:
                raise AttributeError('respawn:interval must be integer')

            respawn = respawn_limit > 0
        else:
            respawn = bool(respawn_raw)

        expect = config.get('expect', SETTINGS_MANAGER['defaults']['expect'])
        if expect not in ['fork', 'daemon', False]:
            raise AttributeError('expect must be fork or daemon or not exist')

        signals = config.get('signals', SETTINGS_MANAGER['defaults']['signals'])
        terminate_signal = signals.get('terminate', SETTINGS_MANAGER['defaults']['signals']['terminate'])
        kill_signal = signals.get('kill', SETTINGS_MANAGER['defaults']['signals']['kill'])
        reload_signal = signals.get('reload', SETTINGS_MANAGER['defaults']['signals']['reload'])

        timeouts = config.get('timeouts', SETTINGS_MANAGER['defaults']['timeouts'])
        start_timeout = signals.get('start', SETTINGS_MANAGER['defaults']['timeouts']['start'])
        stop_timeout = signals.get('stop', SETTINGS_MANAGER['defaults']['timeouts']['stop'])

        return DaemonConfiguration(
            pidfile=pidfile,
            run=run,
            user=config.get('user'),
            respawn=respawn,
            respawn_limit=respawn_limit,
            respawn_interval=respawn_interval,
            expect=expect,

            start_timeout=start_timeout,
            stop_timeout=stop_timeout,

            terminate_signal=terminate_signal,
            kill_signal=kill_signal,
            reload_signal=reload_signal
        )


class DaemonConfigurationError(Exception):
    pass