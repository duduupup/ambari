# coding=utf-8
from resource_management import *
from resource_management.core.exceptions import ClientComponentHasNoStatus


class ServiceClient(Script):

    def install(self, env):
        self.configure(env)
        pass

    def configure(self, env):
        import params
        env.set_params(params)

    def status(self, env):
        raise ClientComponentHasNoStatus()


if __name__ == "__main__":
    ServiceClient().execute()
