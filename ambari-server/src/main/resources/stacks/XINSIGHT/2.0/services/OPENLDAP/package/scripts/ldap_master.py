from resource_management import *
import ldap


class LdapMaster(Script):
    def install(self, env):
        import params
        print('-----------------------------------------------------------------------------')
        print(params.config)
        self.configure(env)
        self.install_packages(env)

    def configure(self, env):
        import params
        env.set_params(params)

    def start(self, env):
        self.configure(env)
        ldap.ldap_master_start()

    def stop(self, env):
        self.configure(env)
        ldap.ldap_master_stop()

    def status(self, env):
        self.configure(env)
        ldap.ldap_master_status()


if __name__ == "__main__":
    LdapMaster().execute()
