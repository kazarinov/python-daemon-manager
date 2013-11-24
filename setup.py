#!/usr/bin/evn python

from distutils.core import setup

setup(
    name='daemon-manager',
    version='0.1',
    author='Andrey Kazarinov',
    author_email='andrei.kazarinov@gmail.com',
    description='Daemon manager',
    packages=[
        'upstart'
    ],
    scripts=[
        'daemon-tools',
        'daemon-runtime'
    ],
    data_files=[
        ('/etc/daemon-manager/',
            [
                'watcher.sh',
            ]
        )
    ],
    requires=[
        'PyYAML'
    ]
)