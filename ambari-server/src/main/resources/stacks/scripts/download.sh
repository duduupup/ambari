#!/bin/sh

URL="http://168.2.237.163/ambari/scripts"
DST_DIR="/root/ambari"

download()
{
        name=$1
        rm -f "$DST_DIR"/"$name"
        wget -P "$DST_DIR" "$URL"/"$name"
}

download "install-ambari.sh"
download "uninstall-ambari.sh"
download "uninstall-hdp.sh"
download "update-stacks.sh"

chmod +x ${DST_DIR}/*.sh
