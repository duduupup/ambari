# coding=utf-8
import common
from resource_management import *


class ServiceClient(Script):
    def install(self, env):
        self.configure(env)

    def configure(self, env):
        import params
        env.set_params(params)
        common.common_configure()

    def status(self, env):
        raise ClientComponentHasNoStatus()


if __name__ == "__main__":
    ServiceClient().execute()
