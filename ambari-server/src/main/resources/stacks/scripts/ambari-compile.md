# make xinsight-ambari repository
## install httpd
```
yum install httpd
systemctl start httpd
```
## install createrepo
```
yum install createrepo
mkdir -p /var/www/html/xinsight-ambari/ambari
```
# compile ambari
## install rpmbuild
```
yum install rpm-build
```
## compile
```
export MAVEN_OPTS="-Xmx2g -XX:MaxPermSize=512M -XX:ReservedCodeCacheSize=512m"
export PATH=$(echo $PATH | sed s#$(dirname $(whereis node | cut -d ':' -f 2)):##g)
mvn versions:set -DnewVersion=2.6.2.0.0
pushd ambari-metrics
mvn versions:set -DnewVersion=2.6.2.0.0
popd
mvn -B clean install rpm:rpm -DnewVersion=2.6.2.0.0 -DbuildNumber=631319b00937a8d04667d93714241d2a0cb17275 -Drat.skip=true -DskipTests -Dpython.ver="python >= 2.6" -Dbuild-rpm
```
## make repository
```
# copy rpm
python /data/projects/ambari/ambari/ambari-server/src/main/resources/stacks/scripts/make-repo.py /data/projects/ambari/ambari 168.2.6.174:22:/var/www/html/xinsight-ambari/ambari:root:test123
```
# install ambari-server
## install yum-plugin-priorities 
```
yum install yum-plugin-priorities
```
## create file /etc/yum.repos.d/ambari.repo
```
[xinsight-ambari]
name=xinsight-ambari
baseurl=http://168.2.6.174/ambari/
gpgcheck=0
enabled=1
priority=1
```