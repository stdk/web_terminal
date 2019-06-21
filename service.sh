#!/bin/bash

WORKDIR=$(dirname $(readlink -f $0))

. $WORKDIR/pdev/bin/activate

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
*)
    echo "Usage: $0 {backend|serial}"
    exit 1
esac
