from resource_management import *
from resource_management.libraries.functions.format import format
from ambari_commons.constants import AMBARI_SUDO_BINARY

config = Script.get_config()
tmp_dir = Script.get_tmp_dir()
pkgs_cache_path = tmp_dir
sudo = AMBARI_SUDO_BINARY

user_group = config['configurations']['cluster-env']['user_group']
service_user = user_group

es_java_home = '/usr/java/jdk1.8.0_162'
es_plugin_dir = '/usr/share/elasticsearch/plugins'
es_plugin_ik_dir = format('{es_plugin_dir}/analysis-ik')
es_plugin_security_dir = format('{es_plugin_dir}/opendistro_security')
es_plugin_ik_name = 'elasticsearch-analysis-ik-6.7.1.zip'
es_conf_dir = '/etc/elasticsearch'
es_home_dir = '/usr/share/elasticsearch'
es_start_cmd = 'systemctl start elasticsearch'
es_stop_cmd = 'systemctl stop elasticsearch'
es_pid_file = '/var/run/elasticsearch/elasticsearch.pid'
es_set_java8_cmd = format('sed \'/# now set the path to java/a\export JAVA_HOME=\/usr\/java\/jdk1.8.0_162\' -i {es_home_dir}/bin/elasticsearch-env')
es_ln_tools_cmd = format('rm -f {es_home_dir}/lib/tools.jar && ln -s {es_java_home}/lib/tools.jar {es_home_dir}/lib/')

es_http_port = config['configurations']['elk-env']['es_http_port']
es_transport_tcp_port = config['configurations']['elk-env']['es_transport_tcp_port']
es_path_data = config['configurations']['es']['es_path_data']
es_jvm_options = config['configurations']['es-jvm']['es_jvm_options']

kibana_conf_dir = '/etc/kibana'
kibana_home_dir = '/usr/share/kibana'
kibana_start_cmd = 'systemctl start kibana'
kibana_stop_cmd = 'systemctl stop kibana'
kibana_status_cmd = 'systemctl status kibana'
kibana_remove_security_cmd = '/usr/share/kibana/bin/kibana-plugin remove opendistro_security'

kibana_server_port = config['configurations']['elk-env']['kibana_server_port']
