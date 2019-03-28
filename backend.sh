#!/bin/bash

WORKDIR=$(dirname $(readlink -f $0))

. $WORKDIR/common.sh

case "$1" in
start)
    daemon start backend python backend.py
    [ "$?" -eq 0 ] && sleep 3
    ;;
stop)
    daemon stop backend
    ;;
status)
    daemon status backend
    ;;
restart)
    $0 stop
    $0 start
    ;;
*)
    echo "Usage: $0 {start|stop|restart|status}"
    exit 1
esac
