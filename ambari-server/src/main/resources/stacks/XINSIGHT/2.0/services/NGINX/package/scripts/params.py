from ambari_commons.constants import AMBARI_SUDO_BINARY
from resource_management.libraries.functions import format
from resource_management.libraries.script import Script

config = Script.get_config()
sudo = AMBARI_SUDO_BINARY

apps_path = config['configurations']['cluster-env']['apps_path']
nginx_user = 'root'
nginx_group = 'root'

nginx_home_dir = format("{apps_path}/nginx")
nginx_conf_dir = format("{apps_path}/nginx-conf")
nginx_start_cmd = 'service nginxd start'
nginx_stop_cmd = 'service nginxd stop'
nginx_pid_file = format("{nginx_home_dir}/logs/nginx.pid")

nginx_port = config['configurations']['nginx-conf']['nginx_port']
nginx_env = config['configurations']['nginx-env']
