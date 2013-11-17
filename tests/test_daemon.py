# -*- coding: utf-8 -*-

import unittest
import subprocess
import shlex


class TestConsole(unittest.TestCase):
    def call(self, command):
        args = shlex.split(command)
        command = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return command.stdout.read()

    def command(self, daemon, command, args=None):
        if args is None:
            args = {}
        options = ['--%s=%s' % (key, value) for key, value in args.iteritems()]
        result = self.call('./run_daemon.sh {daemon} {options} {command}'.format(daemon=daemon, options=' '.join(options), command=command))
        return result


class TestDaemon(TestConsole):

    def test_start_stop(self):
        result_start = self.command('simple.py', 'start')
        result_status = self.command('simple.py', 'status')
        self.assertRegexpMatches(result_status, r'^running \([0-9]+\)$')
        result_stop = self.command('simple.py', 'stop')
        result_status = self.command('simple.py', 'status')
        self.assertEqual(result_status, 'stopped\n')

    def test_restart(self):
        result_start = self.command('simple.py', 'start')
        result_status = self.command('simple.py', 'status')
        self.assertRegexpMatches(result_status, r'^running \([0-9]+\)$')
        result_restart = self.command('simple.py', 'restart')
        result_status = self.command('simple.py', 'status')
        self.assertRegexpMatches(result_status, r'^running \([0-9]+\)$')
        result_stop = self.command('simple.py', 'stop')
        result_status = self.command('simple.py', 'status')
        self.assertEqual(result_status, 'stopped\n')

    def test_start_stop_with_options(self):
        args = {
            'param': 'not default value'
        }
        result_start = self.command('simple.py', 'start', args=args)
        result_status = self.command('simple.py', 'status')
        self.assertRegexpMatches(result_status, r'^running \([0-9]+\)$')
        result_stop = self.command('simple.py', 'stop')
        result_status = self.command('simple.py', 'status')
        self.assertEqual(result_status, 'stopped\n')

    def test_reload(self):
        result_start = self.command('simple.py', 'start')
        result_status = self.command('simple.py', 'status')
        self.assertRegexpMatches(result_status, r'^running \([0-9]+\)$')
        result_restart = self.command('simple.py', 'reload')
        result_status = self.command('simple.py', 'status')
        self.assertRegexpMatches(result_status, r'^running \([0-9]+\)$')
        result_stop = self.command('simple.py', 'stop')
        result_status = self.command('simple.py', 'status')
        self.assertEqual(result_status, 'stopped\n')



if __name__ == '__main__':
    unittest.main()