# -*- coding: utf-8 -*-
import os
import signal
import re


class ProcessError(Exception):
    pass


class ProcessNotFound(ProcessError):
    def __init__(self, pid):
        self.pid = pid
        super(ProcessNotFound, self).__init__("Process %s doesn't exist" % pid)


class ProcessManager(object):

    def find(self, pattern):
        processes = self.get_all()
        found_processes = []
        for process in processes:
            if re.search(pattern, process.cmdline, re.I):
                found_processes.append(process)
        return found_processes

    def get(self, pid):
        try:
            return Process(pid)
        except ProcessNotFound:
            return None

    def get_all(self):
        processes = []
        for pid in os.listdir('/proc'):
            if pid.isdigit():
                try:
                    process = Process(pid)
                    processes.append(process)
                except ProcessNotFound:
                    pass
        return processes


class Process(object):

    @staticmethod
    def get_info(pid):
        info = {}
        try:
            with open('/proc/%s/stat' % pid) as stat:
                process_stat = stat.read().split(' ')
                info['pid'] = int(process_stat[0])
                info['name'] = process_stat[1][1:-1]
                info['state'] = process_stat[2]
                info['parent_pid'] = int(process_stat[3])
                info['gid'] = process_stat[4]
                info['vsize'] = process_stat[22]
            with open('/proc/%s/cmdline' % pid) as cmdline:
                info['cmdline'] = cmdline.read()
            return info
        except IOError:
            return None

    def _get_all_pids(self):
        return [pid for pid in os.listdir('/proc') if pid.isdigit()]

    def __init__(self, pid):
        try:
            pid = int(pid)
        except (ValueError, TypeError):
            raise AttributeError('pid must be integer')

        process_info = Process.get_info(pid)
        if process_info is not None:
            self.pid = pid
            self.name = process_info['name']
            self.cmdline = process_info['cmdline']
        else:
            raise ProcessNotFound(pid)

    @property
    def parent_pid(self):
        process_info = Process.get_info(self.pid)
        return process_info['parent_pid']

    @property
    def parent(self):
        return Process(self.parent_pid)

    @property
    def ancestors(self):
        processes = []
        process = self
        while True:
            try:
                process = process.parent
                processes.append(process)
            except ProcessNotFound:
                break
        return processes

    @property
    def children(self):
        processes = []
        for pid in self._get_all_pids():
            try:
                process = Process(pid)
                if process.parent_pid == self.pid:
                    processes.append(process)
            except ProcessNotFound:
                pass
        return processes

    @property
    def descendants(self):
        return self._get_children_tree(self.pid)

    def _get_children_tree(self, parent_pid):
        processes = []
        for pid in self._get_all_pids():
            try:
                process = Process(pid)
                if process.parent_pid == parent_pid:
                    processes.append(process)
                    processes.extend(self._get_children_tree(pid))
            except ProcessNotFound:
                pass
        return processes

    @property
    def state(self):
        process_info = Process.get_info(self.pid)
        return process_info['state']

    @property
    def memory(self):
        process_info = Process.get_info(self.pid)
        return process_info['vsize']

    def kill(self):
        os.kill(self.pid, signal.SIGKILL)

    def terminate(self):
        os.kill(self.pid, signal.SIGTERM)

    def signal(self, sign):
        os.kill(self.pid, sign)

    def __repr__(self):
        process_info = Process.get_info(self.pid)
        return "<Process pid={pid}, name={name}, cmdline={cmdline}, " \
               "parent_pid={parent_pid}, state={state}, memory={memory}>".format(
            pid=self.pid,
            name=self.name,
            cmdline=self.cmdline,
            parent_pid=process_info['parent_pid'],
            state=process_info['state'],
            memory=process_info['vsize']
        )

    def __cmp__(self, other):
        if other is None:
            return 1

        if self.pid == other.pid:
            return 0
        elif self.pid > other.pid:
            return 1
        else:
            return -1

    def __eq__(self, other):
        return other is not None and self.pid == other.pid

    def __hash__(self):
        return self.pid


class ProcessState(object):
    RUNNING = 'R'
    SLEEPING = 'S'
    DISK_WAITING = 'D'
    ZOMBIE = 'Z'
    TERMINATED = 'T'
    WAITING = 'W'