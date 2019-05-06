#!/usr/bin/env bash

set -e

ERROR=""
SCRIPT_NAME=`basename $0`
LSOF="/usr/sbin/lsof"

INITDB="/usr/bin/initdb"
PSQL="/usr/bin/psql"
PG_DATA=""
PG_PORT=""
PG_SERVICE_NAME=""
DB_OWNER="postgres"
DB_USER=""
DB_PASSWORD=""
USER_PRIVILEGE=""

print_error()
{
    echo -e "\n\n--------------------------------ERROR DETAIL--------------------------------"
    echo "${ERROR}" | while read line
    do
        echo -e "\t${line}"
    done
    echo -e "----------------------------------------------------------------------------"
    exit 2
}

pg_port_in_use()
{
    declare -i rc=0

    ${LSOF} -s TCP:LISTEN -i:${PG_PORT} 2>&1 >/dev/null || rc=$?
    return ${rc}
}

generate_db_service()
{
    local db_service_file="/lib/systemd/system/${PG_SERVICE_NAME}.service"

    (cat << EOF
[Unit]
Description=PostgreSQL database server
After=network.target

[Service]
Type=forking

User=${DB_OWNER}
Group=${DB_OWNER}

# Port number for server to listen on
Environment=PGPORT=${PG_PORT}

# Location of database directory
Environment=PGDATA=${PG_DATA}

# Where to send early-startup messages from the server (before the logging
# options of postgresql.conf take effect)
# This is normally controlled by the global default set by systemd
# StandardOutput=syslog

# Disable OOM kill on the postmaster
OOMScoreAdjust=-1000

ExecStartPre=/usr/bin/postgresql-check-db-dir \${PGDATA}
ExecStart=/usr/bin/pg_ctl start -D \${PGDATA} -s -o "-p \${PGPORT}" -w -t 300
ExecStop=/usr/bin/pg_ctl stop -D \${PGDATA} -s -m fast
ExecReload=/usr/bin/pg_ctl reload -D \${PGDATA} -s

# Give a reasonable amount of time for the server to start up/shut down
TimeoutSec=300

[Install]
WantedBy=multi-user.target
EOF
) > ${db_service_file}

    systemctl daemon-reload
    systemctl enable "${PG_SERVICE_NAME}" 2>&1 > /dev/null
}

start_db_service()
{
    ERROR=`systemctl restart ${PG_SERVICE_NAME}` || rc=$?
    if [[ ${rc} -ne 0 ]]; then
        print_error
    fi
    # wait start successfully
    local i=0
    while ((${i}<12))
    do
        if pg_port_in_use; then
            return
        else
            sleep 10
        fi
        i=$((${i}+1))
    done
    ERROR="postgres cannot start successfully in 120s"
    print_error
}

init_db()
{
    declare -i rc=0

    ERROR=`su - ${DB_OWNER} -c "${INITDB} -D ${PG_DATA} --encoding=UTF8 --locale=C --auth-local trust --auth-host md5"` || rc=$?
    if [[ ${rc} -ne 0 ]]; then
        print_error
    fi

    # generate service script
    generate_db_service

    # config listen_address
    local pg_conf="${PG_DATA}/postgresql.conf"
    sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/" ${pg_conf}
    sed -i "s/#port = 5432/port = ${PG_PORT}/" ${pg_conf}

    # config pg_hba
    if [[ -n ${DB_USER} ]]; then
        local pg_hba="${PG_DATA}/pg_hba.conf"
        rm -f ${pg_hba}.old
        cp ${pg_hba} ${pg_hba}.old
        echo "local all ${DB_USER} md5" >> ${pg_hba}
        echo "host all ${DB_USER} 0.0.0.0/0 md5" >> ${pg_hba}
        echo "host all ${DB_USER} ::/0 md5" >> ${pg_hba}
    fi

    # start pg
    start_db_service

    # create db user
    ERROR=`su - ${DB_OWNER} -c "${PSQL} -p ${PG_PORT} -c \"CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASSWORD}' NOSUPERUSER ${USER_PRIVILEGE} INHERIT LOGIN;\"" 2>&1` || rc=$?
    if [[ ${rc} -ne 0 ]]; then
        print_error
    fi

    # start pg
    start_db_service
}

usage()
{
    echo "Usage: ${SCRIPT_NAME} [options]"
    echo "-p|--port ---- listen port of pg database"
    echo "-d|--data ---- data directory of pg database"
    echo "-s|--service-name ---- service name for pg database"
    echo "-u|--db-user ---- user name for pg database"
    echo "-P|--db-password ---- password for pg database, default the same as user name"
    echo "-a|--user-privilege ---- user privilege for pg database, default create role and create db"
}

if [[ $# -ne 0 ]]; then
    ARGS=`getopt -o "p:d:s:o:u:P:a:h" \
          -l "port:,data:,service-name:,db-owner:,db-user:,db-password:,user-privilege:,help" \
          -n "${SCRIPT_NAME}" -- "$@"`
    eval set -- "${ARGS}"
    while true
    do
        case "$1" in
        -p|--port)
            PG_PORT=$2
            shift 2
            ;;
        -d|--data)
            PG_DATA=$2
            shift 2
            ;;
        -s|--service-name)
            PG_SERVICE_NAME=$2
            shift 2
            ;;
        -u|--db-user)
            DB_USER=$2
            shift 2
            ;;
        -P|--db-password)
            DB_PASSWORD=$2
            shift 2
            ;;
        -a|--user-privilege)
            USER_PRIVILEGE=$2
            shift 2
            ;;
        -h|--help)
            shift
            usage
            exit 0
            ;;
        --)
            shift
            break
            ;;
        *)
            echo "inconsistent error in parsing option $1"
            shift
            exit -1
            ;;
        esac
    done
fi

if [[ -z "${PG_PORT}" ]] || [[ -z "${PG_DATA}" ]] || [[ -z "${PG_SERVICE_NAME}" ]]; then
    usage
    exit 1
fi
echo -n "PG_PORT: ${PG_PORT}, PG_DATA: ${PG_DATA}, PG_SERVICE_NAME: ${PG_SERVICE_NAME}"
if [[ -n "${DB_USER}" ]]; then
    if [[ -z "${DB_PASSWORD}" ]]; then
        DB_PASSWORD=${DB_USER}
    fi
    if [[ -z "${USER_PRIVILEGE}" ]]; then
        USER_PRIVILEGE="CREATEDB CREATEROLE"
    fi
    echo "DB_USER: ${DB_USER}, DB_PASSWORD: ${DB_PASSWORD}, USER_PRIVILEGE: ${USER_PRIVILEGE}"
fi

if [[ ! -f "${LSOF}" ]]; then
    echo "must install ${LSOF}"
    exit 1
fi
if [[ ! -d `dirname ${PG_DATA}` ]]; then
    echo "parent directory of ${PG_DATA} should exists"
    exit 1
fi
if [[ -d "${PG_DATA}" ]] && [[ -n "ls -A ${PG_DATA}" ]]; then
    echo "${PG_DATA} exists and not empty"
    exit 1
fi
if pg_port_in_use; then
    echo "${PG_PORT} is in-use"
    exit 1
fi

init_db
