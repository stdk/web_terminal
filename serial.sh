#!/bin/bash

WORKDIR=$(dirname $(readlink -f $0))

. $WORKDIR/common.sh

start() {
    local devices
    if [ ! -z "$@" ]; then
        devices="$@"
    else
	devices=`ls /dev/dut* 2>/dev/null`
    fi

    for device in $devices; do
        local title=`basename $device`
        daemon start $title python remote_serial.py $device $title
    done
}

stop() {
    if [ ! -z "$@" ]; then
        pids="$@"
    else
        pids=`ls $WORKDIR/dut*.pid 2>/dev/null`
    fi

    for pid in $pids; do
        title=`basename $pid | awk -F '.' '{ printf $1 }'`
        daemon stop $title
    done
}

status() {
    if [ ! -z "$@" ]; then
        pids="$@"
    else
        pids=`ls $WORKDIR/dut*.pid 2>/dev/null`
    fi

    for pid in $pids; do
        title=`basename $pid | awk -F '.' '{ printf $1 }'`
        daemon status $title
    done
}


command="$1"
shift

case $command in
start)
    start "$@"
    ;;
stop)
    stop "$@"
    ;;
status)
    status "$@"
    ;;
restart)
    stop "$@"
    start "$@"
    ;;
*)
    echo "Usage: $0 {start|stop|restart|status}"
    exit 1
esac
