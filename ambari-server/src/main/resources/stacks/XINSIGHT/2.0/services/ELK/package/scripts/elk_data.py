import elk
from resource_management import *


class ElkData(Script):
    def install(self, env):
        import params
        env.set_params(params)
        if elk.es_need_do_operation('ELK_DATA'):
            elk.es_pre_install()
            self.install_packages(env)
            elk.es_post_install()
            elk.es_configure()

    def configure(self, env):
        import params
        env.set_params(params)
        if elk.es_need_do_operation('ELK_DATA'):
            elk.es_configure()

    def start(self, env):
        import params
        env.set_params(params)
        if elk.es_need_do_operation('ELK_DATA'):
            elk.es_configure()
            elk.es_start()

    def stop(self, env):
        import params
        env.set_params(params)
        elk.es_stop()

    def status(self, env):
        import params
        env.set_params(params)
        elk.es_status()


if __name__ == "__main__":
    ElkData().execute()
