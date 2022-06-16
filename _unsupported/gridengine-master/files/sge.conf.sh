#!/bin/bash

if [ $PARAMETER ]; then
    sleep 1
    sed -i -e "/^$PARAMETER /d;\$a$PARAMETER $VALUE" $1
else
    export EDITOR=$0
    export COMMAND=$1
    export PARAMETER=$2
    export VALUE=$3
    export HOST=$4
    qconf -$COMMAND $HOST
fi


