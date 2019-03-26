#!/bin/bash

WORKDIR=$(dirname $(readlink -f $0))

cd $WORKDIR

. pdev/bin/activate

mkdir -p logs

daemon() {
    action=$1
    title=$2
    pid="$title.pid"
    shift 2
    cmd="$@"
    case "$action" in
    start)
        printf "Starting $title... "
        echo start-stop-daemon -S -b -m -p "$pid" -d `pwd` --startas /bin/bash -- -c "exec $cmd > logs/$title.log 2>&1"
        start-stop-daemon -S -b -m -p "$pid" -d `pwd` --startas /bin/bash -- -c "exec $cmd > logs/$title.log 2>&1"
        echo OK
        ;;
    stop)
        printf "Stopping $title... "
        start-stop-daemon -K -p "$pid"
        rm -f "$pid"
        echo OK
        ;;
    status)
        printf "$title: "
        start-stop-daemon -T -p "$pid"
        [ "$?" -eq "0" ] && echo "running" || echo "stopped"
        ;;
    esac

}

ports="dut1 dut2"

case "$1" in
start)
    daemon start backend python backend.py
    sleep 2
    for dev in $ports; do
        daemon start $dev python remote_serial.py /dev/$dev $dev
    done
    ;;
stop)
    for dev in $ports; do
        daemon stop $dev
    done
    daemon stop backend
    ;;
status)
    daemon status backend
    for dev in $ports; do
        daemon status $dev
    done
    ;;
restart)
    $0 stop
    $0 start
    ;;
*)
    echo "Usage: $0 {start|stop|restart|status}"
    exit 1
esac
