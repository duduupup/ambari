from resource_management import *
from resource_management.libraries.functions.format import format
from ambari_commons.constants import AMBARI_SUDO_BINARY

config = Script.get_config()
tmp_dir = Script.get_tmp_dir()
sudo = AMBARI_SUDO_BINARY

service_name = 'common'
user_group = config['configurations']['cluster-env']['user_group']
service_user = user_group

xinsight_path = config['configurations']['cluster-env']['xinsight_path']
xsetup_path = config['configurations']['cluster-env']['xsetup_path']

service_path = format("{xinsight_path}/common")

pkgs_cache_path = format("{xsetup_path}/pkgs_cache")
packages_server = config["clusterHostInfo"]['ambari_server_host'][0]
