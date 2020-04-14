#!/bin/bash

# USER =================================================================
echo ">>>> show a list of all managers"
qconf -sm
echo

echo ">>>> show a list of all operators"
qconf -so
echo

echo ">>>> show a list of all userset lists"
USERSETS=`qconf -sul`
echo "${USERSETS}"
echo

for userset in ${USERSETS}; do
    echo ">>>> show the given userset list: ${userset}"
    qconf -su ${userset}
    echo
done


# HOST =================================================================
echo ">>>> show a list of all administrative hosts"
qconf -sh
echo

echo ">>>> show a list of all submit hosts"
qconf -ss
echo

echo ">>>> show a list of all exec servers"
qconf -sel
echo

echo ">>>> show host group list"
HOST_GROUPS=`qconf -shgrpl`
echo "${HOST_GROUPS}"
echo

for host_group in ${HOST_GROUPS}; do
    echo ">>>> show host group: ${host_group}"
    qconf -shgrp_tree ${host_group}
    # qconf -shgrp_resolved ${host_group}
    echo
done


# queue ================================================================
echo ">>>> show a list of all queues"
Q_LIST=`qconf -sql`
echo "${Q_LIST}"
echo

for q in ${Q_LIST}; do
    echo ">>>> show queue: ${q}"
    qconf -sq ${q}
    echo
done

# parallel env =========================================================
echo ">>>> show all parallel environments"
PE_LIST=`qconf -spl`
echo "${PE_LIST}"
echo

for pe in ${PE_LIST}; do
    echo ">>>> show a parallel environment: ${pe}"
    qconf -sp ${pe}
    echo
done



