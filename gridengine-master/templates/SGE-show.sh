#!/bin/bash

# USER =================================================================
echo "show a list of all managers"
qconf -sm

echo "show a list of all operators"
qconf -so

echo "show a list of all userset lists"
USERSETS=`qconf -sul`

for userset in ${USERSETS}; do
    echo "how the given userset list"
    qconf -su ${userset}
done


# HOST =================================================================
echo "show a list of all administrative hosts"
qconf -sh

echo "show a list of all submit hosts"
qconf -ss

echo "show a list of all exec servers"
qconf -sel

echo "show host group list"
HOST_GROUPS=`qconf -shgrpl`

echo "show host group"
for host_group in ${HOST_GROUPS}; do
    qconf -shgrp_tree ${host_group}
    # qconf -shgrp_resolved ${host_group}
done


# queue ================================================================
echo "show a list of all queues"
qconf -sql

# parallel env =========================================================
echo "show all parallel environments"
PE_LIST=`qconf -spl`

echo "show a parallel environment"
for pe in ${PE_LIST}; do
    echo "> ${pe}"
    qconf -sp ${pe}
done



