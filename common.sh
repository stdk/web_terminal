#!/bin/bash

WORKDIR=$(dirname $(readlink -f $0))
LOGDIR=$WORKDIR/logs
PIDDIR=$WORKDIR

mkdir -p $LOGDIR

. $WORKDIR/pdev/bin/activate

daemon() {
    action=$1
    title=$2
    pid="$PIDDIR/$title.pid"
    shift 2
    cmd="$@"
    case "$action" in
    start)
        printf "Starting $title... "
        echo start-stop-daemon -S -b -m -p "$pid" -d $WORKDIR --startas /bin/bash -- -c "exec $cmd > $LOGDIR/$title.log 2>&1"
        start-stop-daemon -S -b -m -p "$pid" -d $WORKDIR --startas /bin/bash -- -c "exec $cmd > $LOGDIR/$title.log 2>&1"
        rc=$?
        echo OK
        return $rc
        ;;
    stop)
        printf "Stopping $title... "
        start-stop-daemon -K -p "$pid"
        rc=$?
        rm -f "$pid"
        echo OK
        return $rc
        ;;
    status)
        printf "$title: "
        start-stop-daemon -T -p "$pid"
        rc=$?
        case $rc in
           0) echo "running";;
           1) echo "stopped";;
           3) echo "pid not found";;
           *) echo "unknown error";;
        esac
        return $rc
        ;;
    esac
}
