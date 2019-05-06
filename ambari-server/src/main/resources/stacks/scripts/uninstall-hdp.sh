#!/bin/sh

names="ranger atlas-metadata zookeeper bigtop-jsvc spark"

for name in ${names}
do
	#echo ${name}
	for package in `rpm -qa | grep "${name}"`
        do
		echo "start to remove ${package}"
                yum remove -q -y ${package} > /dev/null 2>&1
        done
done
