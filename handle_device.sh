#!/bin/bash

WORKDIR=$(dirname $(readlink -f $0))

echo `date` ":" "$@" >> /home/ubnt/dev/web_terminal/udev.log

command=$1
shift

echo `date` ":" command[$command]["$@"] >> /home/ubnt/dev/web_terminal/udev.log

case $command in
add)
    /bin/su -c "$WORKDIR/backend.sh start" ubnt
    /bin/su -c "$WORKDIR/serial.sh start $@" ubnt
    ;;
remove)
    /bin/su -c "$WORKDIR/serial.sh stop $@" ubnt
    sleep 1
    ;;
*)
    exit 1;
    ;;
esac

