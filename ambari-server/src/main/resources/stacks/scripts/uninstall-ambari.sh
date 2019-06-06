#!/bin/sh

kill_processes()
{
    echo "stop process for $1......"
    pid=`ps aux | grep $1 | grep -v grep | awk {'print $2'} | xargs echo`
    if [ ! -z "$pid" ]; then
        kill ${pid}
        sleep 1
        for p_e in ${pid[@]}; do
            kill -0 $p_e 2> /dev/null
            if [ $? -eq 0 ]; then
                kill -9 ${p_e} 2> /dev/null
            fi
        done
    fi
}

remove_packages()
{
    echo "remove rpm packages for $1......"
    for package in `rpm -qa | grep $1`
    do
        echo -e "\tremove ${package}"
        yum remove -q -y ${package} > /dev/null 2>&1
    done
}

clear_files()
{
    echo "clear files for $1..... "
    rm -rf /etc/$1*
    rm -rf /var/run/$1*
    rm -rf /var/log/$1*
    rm -rf /var/lib/$1*
    rm -rf /usr/lib/$1*
}

uninstall_ambari_metrics()
{
    kill_processes ambari-metrics
    kill_processes resource_monitoring
    remove_packages ambari-metrics
    clear_files ambari-metrics
    clear_files ams-hbase
    rm -rf /usr/lib/flume
    rm -rf /usr/lib/storm
    rm -rf /usr/lib/ambari-metrics-hadoop-sink
    rm -rf /usr/lib/ambari-metrics-kafka-sink
}

uninstall_ambari_server()
{
    #kill_processes ambari-server
    remove_packages ambari-server
    clear_files ambari-server
}

uninstall_ambari_agent()
{
    kill_processes ambari-agent
    remove_packages ambari-agent
    clear_files ambari-agent
}

uninstall_ambari_meta()
{
    echo "remove ambari-db......"
    systemctl stop ambari-meta >/dev/null 2>&1 || true
    sleep 3
    rm -rf /var/lib/pgsql/ambari-meta
    rm -f /var/lib/pgsql/initdb.log
    rm -f /lib/systemd/system/ambari-meta.service
    systemctl daemon-reload
}

usage()
{
    echo "Usage: ${SCRIPT_NAME} <all|server|agent|metrics>"
    exit 1
}

if [[ $# -ne 1 ]]; then
    usage
elif [[ $1 == "all" ]]; then
    uninstall_ambari_metrics
    uninstall_ambari_agent
    uninstall_ambari_server
    uninstall_ambari_meta
elif [[ $1 == "server" ]]; then
    uninstall_ambari_server
elif [[ $1 == "agent" ]]; then
    uninstall_ambari_agent
elif [[ $1 == "metrics" ]]; then
    uninstall_ambari_metrics
else
    usage
fi