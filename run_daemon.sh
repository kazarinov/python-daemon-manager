#! /bin/bash

export PYTHONPATH=/vagrant/Python/ProcessMaster:/usr/local/lib/python2.7/dist-packages:$PYTHONPATH

python -B /vagrant/Python/ProcessMaster/tests/daemons/$@