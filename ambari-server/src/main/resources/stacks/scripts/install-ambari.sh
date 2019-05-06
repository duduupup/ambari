#!/bin/bash

set -e

ERROR=""
SCRIPT_NAME=`basename $0`
LSOF="/usr/sbin/lsof"
INITDB="/usr/bin/initdb"
PSQL="/usr/bin/psql"
PG_HOST=`hostname -f`
PG_DEFAULT_DATA="/var/lib/pgsql/ambari-meta"
PG_DEFAULT_PORT="15432"
PG_DATA=""
PG_PORT=""
PG_SERVICE_NAME="ambari-meta"

JAVA_HOME="/usr/java/jdk1.8.0_112"

DB_NAME="ambari"
DB_USER="ambari"
DB_PASSWORD="bigdata"

FORCE="true"

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

check_pg_rpm() {
    if [[ ! -f "${INITDB}" ]]; then
        ERROR=`yum install -y postgresql-server` || rc=$?
        if [[ ${rc} -ne 0 ]]; then
            print_error
        fi
    fi

    local pg_ver=`${INITDB} --version | awk '{print $3}'`
    local pg_ver_major=`echo ${pg_ver} | cut -d '.' -f 1`
    local pg_ver_minor=`echo ${pg_ver} | cut -d '.' -f 2`
    if ((${pg_ver_major} > 8)); then
        return 0
    elif ((${pg_ver_major} == 8)) && ((${pg_ver_minor} < 1)); then
        return 0
    else
        echo "postgresql-server must >= 8.1"
        exit 2
    fi
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

User=postgres
Group=postgres

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

init_db()
{
    declare -i rc=0

    ERROR=`su - postgres -c "${INITDB} -D ${PG_DATA} --encoding=UTF8 --locale=C --auth-local trust --auth-host md5"` || rc=$?
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
    local pg_hba="${PG_DATA}/pg_hba.conf"
    rm -f ${pg_hba}.old
    cp ${pg_hba} ${pg_hba}.old
    echo "local all ambari md5" >> ${pg_hba}
    echo "host all ambari 0.0.0.0/0 md5" >> ${pg_hba}
    echo "host all ambari ::/0 md5" >> ${pg_hba}

    ERROR=`systemctl start ${PG_SERVICE_NAME}` || rc=$?
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

init_ambari_schema()
{
    local ambari_init_sql="/var/lib/ambari-server/resources/Ambari-DDL-Postgres-CREATE.sql"

    ERROR=`su - postgres -c "${PSQL} -p ${PG_PORT} -c \"CREATE USER ambari WITH PASSWORD '${DB_PASSWORD}' NOSUPERUSER CREATEDB NOCREATEROLE INHERIT LOGIN;\"" 2>&1` || rc=$?
    if [[ ${rc} -ne 0 ]]; then
        print_error
    fi

    ERROR=`env PGPASSWORD=${DB_PASSWORD} ${PSQL} -h ${PG_HOST} -p ${PG_PORT} -U ${DB_USER} -d postgres -c "CREATE DATABASE ambari ENCODING 'UTF8' TEMPLATE template0 LC_COLLATE 'C' LC_CTYPE 'C';" 2>&1` || rc=$?
    if [[ ${rc} -ne 0 ]]; then
        print_error
    fi

    ERROR=`env PGPASSWORD=${DB_PASSWORD} ${PSQL} -h ${PG_HOST} -p ${PG_PORT} -U ${DB_USER} -d ${DB_NAME} -c "CREATE SCHEMA ambari;" 2>&1` || rc=$?
    if [[ ${rc} -ne 0 ]]; then
        print_error
    fi

    ERROR=`env PGPASSWORD=${DB_PASSWORD} ${PSQL} -h ${PG_HOST} -p ${PG_PORT} -U ${DB_USER} -d ${DB_NAME} -p ${PG_PORT} -f ${ambari_init_sql} 2>&1` || rc=$?
    if [[ ${rc} -ne 0 ]]; then
        print_error
    fi
}

install_ambari()
{
    declare -i rc=0

    ERROR=`yum install -y ambari-server` || rc=$?
    if [[ ${rc} -ne 0 ]]; then
        print_error
    fi

    check_pg_rpm
}

setup_ambari()
{
    ERROR=`ambari-server setup -s -j ${JAVA_HOME} --database=postgres --databasehost=${PG_HOST} --databaseport=${PG_PORT} \
        --databasename=${DB_NAME} --databaseusername=${DB_USER} --databasepassword=${DB_PASSWORD} 2>&1` || rc=$?
    if [[ ${rc} -ne 0 ]]; then
        print_error
    fi
}

main()
{
    echo -n "Step1: install ambari-server......"
    install_ambari
    echo " successfully."

    echo -n "Step2: init database for ambari......"
    init_db
    echo " successfully."

    echo -n "Step3: init schema for ambari......"
    init_ambari_schema
    echo " successfully."

    echo -n "Step4: setup ambari......"
    setup_ambari
    echo " successfully."
}

usage()
{
    echo "Usage: ${SCRIPT_NAME} [options]"
    echo "-p ---- listen port of pg database for ambari, default is ${PG_DEFAULT_PORT}"
    echo "-D ---- data directory of pg database for ambari, default is ${PG_DEFAULT_DATA}"
}

if [[ $# -ne 0 ]]; then
    ARGS=`getopt -o "p:D:j:s:h" -l "port:,data:,java,stack-java,help" -n "${SCRIPT_NAME}" -- "$@"`
    eval set -- "${ARGS}"
    while true
    do
        case "$1" in
        -p|--port)
            PG_PORT=$2
            shift 2
            ;;
        -D|--data)
            PG_DATA=$2
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

if [[ -z "${PG_PORT}" ]]; then
    PG_PORT=${PG_DEFAULT_PORT}
fi
if [[ -z "${PG_DATA}" ]]; then
    PG_DATA=${PG_DEFAULT_DATA}
fi
echo "PG_PORT: ${PG_PORT}, PG_DATA: ${PG_DATA}, JAVA_HOME: ${JAVA_HOME}, UPDATE_STACK: ${FORCE}"
if [[ ! -f "${LSOF}" ]]; then
    echo "must install ${LSOF}"
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
if [[ ! -d ${JAVA_HOME} ]]; then
    echo "make sure have java in both ${JAVA_HOME}"
    exit 1
fi

main
