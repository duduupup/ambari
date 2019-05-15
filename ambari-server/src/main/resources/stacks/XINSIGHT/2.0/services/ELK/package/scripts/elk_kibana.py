import elk
from resource_management import *


class ElkKibana(Script):
    def install(self, env):
        import params
        env.set_params(params)
        elk.kibana_pre_install()
        self.install_packages(env)
        elk.kibana_post_install()
        elk.kibana_configure()

    def configure(self, env):
        import params
        env.set_params(params)
        elk.kibana_configure()

    def start(self, env):
        self.configure(env)
        elk.kibana_start()

    def stop(self, env):
        import params
        env.set_params(params)
        elk.kibana_stop()

    def status(self, env):
        import params
        env.set_params(params)
        elk.kibana_status()


if __name__ == "__main__":
    ElkKibana().execute()
