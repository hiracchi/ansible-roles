#!/bin/sh

set -eux

ADMIN_USERS="{{ gridengine_admin_users }}"
GROUP1_USERS="{{ gridengine_users }}"
MASTER_HOST="{{ gridengine_master_host }}"

DATADIR="/usr/local/gridengine/data"

HOSTLIST_FILES=`ls ${DATADIR}/hostlist*`
PE_FILES=`ls ${DATADIR}/pe*`
QUEUE_FILES=`ls ${DATADIR}/queue*`

init()
{
    if [ x"`qconf -sql`" != x ]; then
        QUEUES=`qconf -sql`
        for QUEUE in ${QUEUES}; do
            qconf -dq ${QUEUE}
        done
    fi

    if [ x"`qconf -shgrpl`" != x ]; then
        GRPS=`qconf -shgrpl`
        for GRP in ${GRPS}; do
            qconf -dhgrp "${GRP}"
        done
    fi

    if [ x"`qconf -spl`" != x ]; then
        PES=`qconf -spl`
        for PE in ${PES}; do
            qconf -dp ${PE}
        done
    fi

    if [ x"`qconf -sul`" != x ]; then
        USERSETS=`qconf -sul`
        for USERSET in ${USERSETS}; do
            if [ x${USERSET} != xarusers \
                  -a x${USERSET} != xdeadlineusers \
                  -a x${USERSET} != xdefaultdepartment ]; then
                qconf -dul ${USERSET}
            fi
        done
    fi
    
    if [ x"`qconf -sm`" != x ]; then
        MANAGERS=`qconf -sm`
        for MANAGER in ${MANAGERS}; do
            if [ x${MANAGER} != xroot -a x${MANAGER} != xsgeadmin ]; then
                sudo -u sgeadmin qconf -dm ${MANAGER}
            fi
        done
    fi

    if [ x"`qconf -sel`" != x ]; then
        HOSTS=`qconf -sel`
        for HOST in ${HOSTS}; do
            qconf -de ${HOST}
        done
    fi
    
    echo "initialize done."
    echo
}


# initialize
init

# add a submit host
sudo -u sgeadmin qconf -as ${MASTER_HOST}

# add user to manager list
for ADMIN_USER in ${ADMIN_USERS}; do
    sudo -u sgeadmin qconf -am ${ADMIN_USER}
done

# add user(s) to userset list(s)
for USER in ${GROUP1_USERS}; do
    qconf -au ${USER} group1
done

# add new host group entry
for hostlist in ${HOSTLIST_FILES}; do
    qconf -Ahgrp ${hostlist}
done

# add a new parallel environment
for pe in ${PE_FILES}; do
    qconf -Ap ${pe}
done

# add a new cluster queue
for q in ${QUEUE_FILES}; do
    qconf -Aq ${q}
done


