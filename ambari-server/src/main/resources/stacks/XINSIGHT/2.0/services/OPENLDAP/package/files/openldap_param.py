# -*- coding: utf-8 -*-
# maintainer: Yunlong Zhang
# date:2018-01-29

from resource_management import *
from resource_management.libraries.functions.format import format
from ambari_commons.constants import AMBARI_SUDO_BINARY

import openldap_param


sldap_pid_file = openldap_param.sldap_pid_file
config = Script.get_config()
tmp_dir = Script.get_tmp_dir()
sudo = AMBARI_SUDO_BINARY
BREAK = '\n'
# ldap donfig
user_group = 'ldap'
service_user = user_group


def ldap_olcServerIDCreate(olcid='key_value'):
    olcServer_id_dict = {}
    for item in ldap_node_hostname_list:
        olcServer_id_dict[item] = ldap_node_hostname_list.index(item) + 1
    return olcServer_id_dict[olcid]


ldap_node_hostname_list = config['clusterHostInfo']['openldap_hosts']
ldap_node_hostname = config["hostname"]
ldap_olcServerID = ldap_olcServerIDCreate(ldap_node_hostname)
apps_path = config['configurations']['cluster-env']['apps_path']
xsetup_path = config['configurations']['cluster-env']['xsetup_path']
ldap_root_pass = config['configurations']['openldap-env']['openldap_root_pass']
ldap_domain_name_value = config['configurations']['openldap-env']['openldap_domain_name']
ldap_domain_suffix = config['configurations']['openldap-env']['openldap_domain_suffix']

openldap_multiple_master_file_content = '''
  olcSyncRepl: rid={}
  provider=ldap://{}:389/
  bindmethod=simple
  binddn="cn=Manager,dc={},dc={}"
  credentials={}
  searchbase="dc={},dc={}"
  scope=sub
  schemachecking=on
  type=refreshAndPersist
  retry="30 5 300 3"
  interval=00:00:05:00

'''
openldap_ha_config = '''
listen openldap_http_in
  bind :389
  mode http
  default_backend openldap_server

backend openldap_server
   balance   roundrobin
   {}  
'''

openlda_haproxy_server_map = '''
    server {}-openldap-ha {} check inter 1000
'''


def ldap_salve_config():
    try:
        slave_hosts_list = ldap_node_hostname_list
        print(slave_hosts_list)
        slave_hosts_list.remove(ldap_node_hostname)
        print(slave_hosts_list)
        ldap_slave_cluster_content = ''
        for hosts in slave_hosts_list:
            ldap_slave_cluster_content = ldap_slave_cluster_content + openldap_multiple_master_file_content.format(
                hosts, hosts, ldap_domain_name_value, ldap_domain_suffix, ldap_root_pass, ldap_domain_name_value,
                ldap_domain_suffix)
    except Exception as e:
        raise e
    return ldap_slave_cluster_content


# def openldap_node_check_config():
#     for host in ldap_node_hostname_list:
#         backend_server_map = BREAK + openlda_haproxy_server_map.format(host, host)
#     return backend_server_map
#
#
# ldap_haproxy_backend_server_map = openldap_node_check_config()
#
#
# def backend_server_map_config():
#     try:
#         backend_server_map = ldap_haproxy_backend_server_map
#         haproxy_config = openldap_ha_config.format(backend_server_map)
#     except Exception as e:
#         raise e
#     return haproxy_config
#
#
# ldap_haproxy_config = backend_server_map_config()

# ldap directory
ldap_root_path = format('{apps_path}/ldap_auto')
ldap_rpm_path = format('{xsetup_path}/soft')
ldap_scripts_path = format('{ldap_root_path}/scripts')
ldap_templates_path = format('{ldap_root_path}/templates')
ldap_temp_path = format('{ldap_root_path}/temp')
ldap_multiple_master_salves_config = ldap_salve_config()

# ldap etc config file
ldap_etc_openldap_config_file = format('/etc/openldap/ldap.conf')
ldap_etc_openldap_server_config_directory = format('/etc/openldap/slapd.d')
ldap_openldap_run_directory = format('/var/lib/ldap')

# ldap command
ldap_start_and_initialize_command = format('bash {ldap_scripts_path}/init_openldap.sh')
ldap_migrate_command = format('bash {ldap_scripts_path}/migrate.sh')
ldap_start_command = format('systemctl restart slapd')
ldap_stop_command = format('systemctl stop slapd')
ldap_reinstall_openldap_command = format('yum -yq reinstall openldap-*')
ldap_reinstall_openldap_slave_command = format(' yum -yq reinstall openldap-servers-2.4.44')
ldap_reinstall_openldap_client_command = format(' yum -yq reinstall openldap-clients-2.4.44')
ldap_remove_etc_ldap_slapd_command = format('cd /etc/openldap; rm -rf *')
ldap_remove_ldap_directory_command = format('rm -rf /var/lib/ldap')
ldap_stop_ldap_service_command = format('systemctl stop slapd.service')
ldap_check_ldap_pid_file_command = format(
    'ls {sldap_pid_file} >/dev/null 2>&1 && ps -p `cat {sldap_pid_file}` >/dev/null 2>&1')
ldap_master_mod_syncprov_command = format('cd /tmp; ldapadd -Y EXTERNAL -H ldapi:/// -f mod_syncprov.ldif')
ldap_master_syncprov_command = format('cd /tmp; ldapadd -Y EXTERNAL -H ldapi:/// -f syncprov.ldif')
ldap_master_slave_syncprov_command = format('cd /tmp; ldapmodify -Y EXTERNAL -H ldapi:/// -f syncrepl.ldif')
# ldap_ha_config_check_command = format('grep -wq "openldap_server" /usr/local/haproxy/conf/haproxy.cfg ')
# ldap_ha_config_config_row_delete_command = format('sed "/-openldap-ha/"d /usr/local/haproxy/conf/haproxy.cfg')
# ldap_ha_config_install_command = format('sed -i "$a\{ldap_haproxy_config}" /usr/local/haproxy/conf/haproxy.cfg')
# ldap_insert_config_command = format(
#     'openldap_server=`grep -n "^backend openldap_server" /usr/local/haproxy/conf/haproxy.cfg | cut -f 1 -d ":"` && inert_count=$[${openldap_server}+2] && sed -i "${inert_count} {ldap_haproxy_backend_server_map}" /usr/local/haproxy/conf/haproxy.cfg')
# ldap_ha_config_update_command = format(
#     'cd /usr/local/haproxy/conf && {ldap_insert_config_command}')
