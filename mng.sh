. pdev/bin/activate

mkdir -p logs

daemon() {
    action=$1
    title=$2
    pid="$title.pid"
    shift 2
    case "$action" in
    start)
        printf "Starting $title... "
        start-stop-daemon -S -b -m -p "$pid" -d `pwd` --startas /bin/bash -- -c "exec "$@" > logs/$app.log 2>&1"
        echo OK
        ;;
    stop)
        printf "Stopping $title... "
        start-stop-daemon -K -p "$pid"
        echo OK
        ;;
    status)
        printf "$title: "
        start-stop-daemon -T -p "$pid"
        [ "$?" -eq "0" ] && echo "running" || echo "stopped" 
        ;;
    esac      

}

case "$1" in
start)
    daemon start backend backend.py
    sleep 2
    daemon start serial1 python remote_serial.py /dev/ttyUSB0 serial1
    daemon start serial2 python remote_serial.py /dev/ttyUSB1 serial2
    ;;
stop)
    daemon stop serial1
    daemon stop backend
    ;;
status)
    daemon status backend
    daemon status serial1
    daemon status serial2
    ;;
restart)
    $0 stop
    $0 start
    ;;
*)
    echo "Usage: $0 {start|stop|restart|status}"
    exit 1
esac
