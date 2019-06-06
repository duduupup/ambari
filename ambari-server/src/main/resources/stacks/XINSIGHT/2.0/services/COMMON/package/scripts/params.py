from resource_management import *
from resource_management.libraries.functions import default, format
from ambari_commons.constants import AMBARI_SUDO_BINARY

config = Script.get_config()
tmp_dir = Script.get_tmp_dir()
sudo = AMBARI_SUDO_BINARY

common_user = config['configurations']['cluster-env']['user_name']
common_group = config['configurations']['cluster-env']['user_group']

xinsight_path = config['configurations']['cluster-env']['xinsight_path']
common_home_dir = format("{xinsight_path}/common")
common_conf_dir = format("{common_home_dir}/conf")
