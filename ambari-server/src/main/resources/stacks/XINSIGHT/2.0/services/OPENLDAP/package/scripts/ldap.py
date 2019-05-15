from resource_management import check_process_status
from resource_management.core.resources import Execute


def ldap_master_start():
    import params
    Execute(params.ldap_master_start_cmd, user='root')


def ldap_master_stop():
    import params
    Execute(params.ldap_master_stop_cmd, user='root')


def ldap_master_status():
    import params
    check_process_status(params.ldap_master_pid_file)
