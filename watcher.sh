#!/bin/bash

NAME=$1
INITD="/etc/init.d/$NAME"

if [[ `$INITD status | grep stopped` ]]; then
    $INITD restart;
    if [ "$?" -ne 0 ]; then
        echo "Don't restart  ${NAME}"
    fi;
fi;
