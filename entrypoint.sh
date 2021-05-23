#!/bin/sh

if [ "$SHOWHELP" == "true" ]; then
   /usr/local/bin/hs110exporter.py -h
   exit $?
fi

if [ -z "$HS110IP" ]; then
    echo "Enviroment var 'HS110IP' is required"
    exit 1
fi

HS110IP=$(getent hosts $HS110IP | cut -f1 -d' ')

if [ -z "$FREQUENCY" ]; then
    FREQUENCY=1
fi

if [ -z "$LISTENPORT" ]; then
    LISTENPORT=8110
fi

if [ -z "$LABEL" ]; then
    LABEL=location=home
fi

export PYTHONUNBUFFERED=1

exec python /usr/local/bin/hs110exporter.py -t $HS110IP -f $FREQUENCY -p $LISTENPORT -l $LABEL

