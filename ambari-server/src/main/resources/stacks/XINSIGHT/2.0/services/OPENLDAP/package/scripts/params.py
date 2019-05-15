from resource_management.libraries.functions import default
from resource_management import *
from resource_management.libraries.functions.format import format
from ambari_commons.constants import AMBARI_SUDO_BINARY

config = Script.get_config()

ldap_master_pid_file = '/var/run/openldap/slapd.pid'
ldap_master_start_cmd = 'systemctl start slapd'
ldap_master_stop_cmd = 'systemctl stop slapd'
