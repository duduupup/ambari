# -*- coding: utf-8 -*-
# maintainer: Yunlong Zhang
# date:2018-01-29
from resource_management import Template, check_process_status, ComponentIsNotRunning
from resource_management.core.resources import File, Execute, Directory
from resource_management.libraries.functions.format import format

import os, time


def openladp_handler(action=None):

    """
        handler start, stop function about ldap server
    """
    if action == 'start':
        import params
        Execute(params.ldap_stop_command, user='root', ignore_failures=True)
        File(params.sldap_pid_file, action="delete", only_if=format("test -f {sldap_pid_file}"))
        Execute(params.ldap_start_command, user='root', logoutput=True)
    elif action == 'stop':
        import params
        if os.path.exists(params.sldap_pid_file):
            Execute(params.ldap_stop_command, user='root', logoutput=True)
            File(params.sldap_pid_file, action="delete", only_if=format("test -f {sldap_pid_file}"))
    elif action == 'status':
        import openldap_param
        for i in range(1, 3):
            try:
                check_process_status(openldap_param.sldap_pid_file)
                return
            except ComponentIsNotRunning:
                time.sleep(0.1)
                continue
        File(openldap_param.sldap_pid_file, action="delete", only_if="test -f {}".format(openldap_param.sldap_pid_file))
        raise ComponentIsNotRunning()


def install_pre():
    import params
    Execute('echo ======== stop openldap  =========', user='root', logoutput=True)
    Execute(params.ldap_stop_ldap_service_command, user='root', logoutput=True, only_if=format('{ldap_check_ldap_pid_file_command}'))
    Execute('echo ======== delete openldap config =========', user='root', logoutput=True)
    Execute(params.ldap_remove_etc_ldap_slapd_command, user='root', logoutput=True)
    Execute('echo ======== delete openldap operation directory =========', user='root', logoutput=True)
    Execute(params.ldap_remove_ldap_directory_command, user='root', logoutput=True)


def multiple_master_config():
    import params
    Execute('echo ======== multiple master config  =========', user='root', logoutput=True)
    Execute(params.ldap_master_mod_syncprov_command, user='root', logoutput=True)
    Execute(params.ldap_master_syncprov_command, user='root', logoutput=True,)
    Execute(params.ldap_master_slave_syncprov_command, user='root', logoutput=True,)


# def ldap_haproxy_config():
#     import params
#     Execute('echo ======== ldap_haproxy_config  =========', user='root', logoutput=True)
#     Execute(params.ldap_ha_config_config_row_delete_command, user='root', logoutput=True, only_if=format('{ldap_ha_config_check_command}'))
#     Execute(params.ldap_ha_config_command, user='root', logoutput=True, only_if=format('{ldap_ha_config_check_command}'))
#     Execute(params.ldap_ha_config_install_command, user='root', logoutput=True, not_if=format('{ldap_ha_config_check_command}'))



def service_install():
    import params
    """
        install ldap via rmp
    """

    def _discribute_files():
        Execute('echo ======== install openldap ==========', user='root', logoutput=True)
        Execute(params.ldap_reinstall_openldap_command, user='root', logoutput=True)
        # Execute('echo ======== install openldap slave ==========', user='root', logoutput=True)
        # Execute(params.ldap_reinstall_openldap_slave_command, user='root', logoutput=True)
        # Execute('echo ======== install openldap  client==========', user='root', logoutput=True)
        # Execute(params.ldap_reinstall_openldap_client_command, user='root', logoutput=True)
        Directory(format('{ldap_root_path}'),
                  owner=params.service_user,
                  group=params.user_group,
                  recursive_ownership=True,
                  mode=0755
                  )
        File(format('{ldap_root_path}/openldap.conf'),
             content=Template('openldap.conf'),
             owner=params.service_user,
             group=params.user_group,
             mode=0755
             )
        '''
            upload the ldap scripts 
        '''
        Directory(format('{ldap_scripts_path}'),
                  owner=params.service_user,
                  group=params.user_group,
                  recursive_ownership=True,
                  mode=0755
                  )

        File(format('{ldap_scripts_path}/init_openldap.sh'),
             content=Template('init_openldap.sh'),
             owner=params.service_user,
             group=params.user_group,
             mode=0755

             )
        File(format('{ldap_scripts_path}/migrate.sh'),
             content=Template('migrate.sh'),
             owner=params.service_user,
             group=params.user_group,
             mode=0755

             )
        File(format('{ldap_scripts_path}/transform.py'),
             content=Template('transform.py'),
             owner=params.service_user,
             group=params.user_group,
             mode=0755

             )

        '''
            upload the ldap templates
        '''
        Directory(format('{ldap_templates_path}'),
                  owner=params.service_user,
                  group=params.user_group,
                  recursive_ownership=True,
                  mode=0755
                  )
        File(format('{ldap_templates_path}/basedomain.ldif.template'),
             content=Template('basedomain.ldif.template'),
             owner=params.service_user,
             group=params.user_group,
             mode=0755

             )
        File(format('{ldap_templates_path}/chdomain.ldif.template'),
             content=Template('chdomain.ldif.template'),
             owner=params.service_user,
             group=params.user_group,
             mode=0755

             )
        File(format('{ldap_templates_path}/chrootpw.ldif.template'),
             content=Template('chrootpw.ldif.template'),
             owner=params.service_user,
             group=params.user_group,
             mode=0755

             )
        File(format('/tmp/mod_syncprov.ldif'),
             content=Template('mod_syncprov.ldif'),
             owner=params.service_user,
             group=params.user_group,
             mode=0755
             )
        File(format('/tmp/syncprov.ldif'),
             content=Template('syncprov.ldif'),
             owner=params.service_user,
             group=params.user_group,
             mode=0755
             )
        File(format('/tmp/syncrepl.ldif'),
             content=Template('syncrepl.ldif'),
             owner=params.service_user,
             group=params.user_group,
             mode=0755
             )
        Directory(format('{ldap_temp_path}'),
                  owner=params.service_user,
                  group=params.user_group,
                  recursive_ownership=True,
                  mode=0755
                  )
    try:
        Execute('echo before distribute file', user='root', logoutput=True)
        _discribute_files()
        Execute('echo after distribute file', user='root', logoutput=True)
    except Exception as e:
        raise e
    Execute('echo install before', user='root', logoutput=True)
    Execute(params.ldap_start_and_initialize_command, user='root', logoutput=True)
    Execute(params.ldap_migrate_command, user='root', logoutput=True)
    Execute('echo install after', user='root', logoutput=True)


