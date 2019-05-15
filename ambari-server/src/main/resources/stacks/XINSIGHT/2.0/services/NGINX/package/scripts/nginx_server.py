import nginx
from resource_management import *


class NginxServer(Script):
    def install(self, env):
        import params
        env.set_params(params)
        self.install_packages(env)
        nginx.nginx_configure()

    def configure(self, env):
        import params
        env.set_params(params)
        nginx.nginx_configure()

    def start(self, env):
        self.configure(env)
        nginx.nginx_start()

    def stop(self, env):
        import params
        env.set_params(params)
        nginx.nginx_stop()

    def status(self, env):
        import params
        env.set_params(params)
        nginx.nginx_status()


if __name__ == "__main__":
    NginxServer().execute()
