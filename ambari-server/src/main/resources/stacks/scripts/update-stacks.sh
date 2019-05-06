#!/bin/sh

ambari-server stop
rm -rf /var/lib/ambari-server/resources/stacks/HDP
rm -rf /var/lib/ambari-server/resources/stacks/XINSIGHT
scp -r liuhj@168.2.237.163:/home/liuhj/data/projects/ambari/ambari-stack/XINSIGHT /var/lib/ambari-server/resources/stacks/
ls -l /var/lib/ambari-server/resources/stacks/
ambari-server start
