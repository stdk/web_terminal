#!/bin/bash

WORKDIR="$(dirname $(readlink -f $0))"

cd "$WORKDIR"

. "$WORKDIR"/pdev/bin/activate

case "$1" in
backend)
    python -u backend.py
    ;;
serial)
    if [ $# -lt 2 ]; then
        echo 'Argument required'
        exit 1
    fi
    index=$2
    python -u remote_serial.py -D /dev/dut$index -t dut$index
    ;;
udm)
    if [ $# -lt 2 ]; then
        echo 'Argument required'
        exit 1
    fi
    index=$2
    python -u remote_command.py -t dut$index -c "$WORKDIR/udm-console.sh $index"
    ;;
*)
    echo "Usage: $0 {backend|serial}"
    exit 1
esac
