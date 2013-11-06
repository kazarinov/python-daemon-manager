#! /bin/bash

export PYTHONPATH=.:./bin:/usr/local/lib/python2.7/dist-packages:$PYTHONPATH

python -B ./tests/$@