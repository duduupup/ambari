# coding=utf-8
from ambari_commons.config_utils import properties2dict
from resource_management import *
from resource_management.core.exceptions import ClientComponentHasNoStatus


def generate_xinsight_properties():
    import params
    Directory(format("{service_path}/conf"),
              owner=params.service_user, group=params.user_group,
              create_parents=True,
              recursive_ownership=True,
              mode=0755)
    cdh_env_info = params.config['configurations']['common-cdh']['cdh_env']
    xinsight_properties_dict = properties2dict(cdh_env_info)
    PropertiesFile(format("{service_path}/conf/xinsight.properties"), properties=xinsight_properties_dict,
                   owner=params.service_user, group=params.user_group)


class ServiceClient(Script):

    def install(self, env):
        self.configure(env)
        generate_xinsight_properties()

    def configure(self, env):
        import params
        env.set_params(params)

    def status(self, env):
        raise ClientComponentHasNoStatus()


if __name__ == "__main__":
    ServiceClient().execute()
