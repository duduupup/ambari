# coding=utf-8
import os
import socket
from resource_management.libraries.functions.format import format
from resource_management import check_process_status, ComponentIsNotRunning, Fail, InvalidArgument
from resource_management.core.resources import Execute, Directory, File, Package
from resource_management.libraries.functions.get_user_call_output import get_user_call_output
import ambari_simplejson as json


def es_need_do_operation(role_name):
    import params
    if role_name == 'ELK_MASTER':
        return True
    elif role_name == 'ELK_DATA':
        for host in params.config['clusterHostInfo'].get('elk_master_hosts', []):
            if host == params.config['hostname']:
                return False
    elif role_name == 'ELK_CLIENT':
        for host in params.config['clusterHostInfo'].get('elk_master_hosts', []):
            if host == params.config['hostname']:
                return False
        for host in params.config['clusterHostInfo'].get('elk_data_hosts', []):
            if host == params.config['hostname']:
                return False
    else:
        raise Fail(format("unknown {role_name}"))

    return True


def es_pre_install():
    import params
    Package('elasticsearch-oss', action='remove')
    Directory(params.es_home_dir, owner='root', action='delete')
    Directory(params.es_conf_dir, owner='root', action='delete')
    es_data_dir = params.es_path_data[0:-1] if params.es_path_data[-1] == '/' else params.es_path_data
    es_data_parent_dir = '/'.join(es_data_dir.split('/')[0:-1])
    if not os.path.exists(es_data_parent_dir) or not os.path.isdir(es_data_parent_dir):
        raise InvalidArgument(format('parent directory of es_path_data[{es_path_data}] must exist'))
    if os.path.exists(es_data_dir) and len(os.listdir(es_data_dir)) != 0:
        raise InvalidArgument(format("es_path_data[{es_path_data}] should be not exist or null"))


def es_post_install():
    import params
    Execute(format("chmod g+w {es_conf_dir}"))
    Directory(params.es_path_data, owner='elasticsearch', group='elasticsearch', create_parents=False, mode=0755)
    Execute(params.es_set_java8_cmd, user='root', logoutput=True)
    Execute(params.es_ln_tools_cmd, user='root', logoutput=True)
    # Directory(params.es_plugin_security_dir, owner='root', action='delete')
    Directory(params.es_plugin_ik_dir, owner='root', action='delete')
    Directory(params.es_plugin_ik_dir, owner='root', group='root', create_parents=False, mode=0755)
    base_url = json.loads(params.config['hostLevelParams']['repo_info'])[0]['baseUrl']
    ik_download_path = format("{pkgs_cache_path}/{es_plugin_ik_name}")
    File(ik_download_path, owner='root', action='delete')
    Execute(format("wget -q -O {ik_download_path} {base_url}/elasticsearch/{es_plugin_ik_name}"),
            user='root', logoutput=True)
    Execute(format("unzip -q {ik_download_path} -d {es_plugin_ik_dir}"), user='root', logoutput=True)


def es_configure():
    import params
    es_masters = params.config['clusterHostInfo'].get('elk_master_hosts', [])
    es_datas = params.config['clusterHostInfo'].get('elk_data_hosts', [])
    es_yml_dict = {
        'path.logs': '/var/log/elasticsearch',
        'network.host': '0.0.0.0',
        'opendistro_security.disabled': 'true',
        'cluster.routing.allocation.disk.threshold_enabled': 'false',
        'node.max_local_storage_nodes': '1',

        # 'opendistro_security.ssl.transport.pemcert_filepath': 'esnode.pem',
        # 'opendistro_security.ssl.transport.pemkey_filepath': 'esnode - key.pem',
        # 'opendistro_security.ssl.transport.pemtrustedcas_filepath': 'root - ca.pem',
        # 'opendistro_security.ssl.transport.enforce_hostname_verification': 'false',
        # 'opendistro_security.ssl.http.enabled': 'true',
        # 'opendistro_security.ssl.http.pemcert_filepath': 'esnode.pem',
        # 'opendistro_security.ssl.http.pemkey_filepath': 'esnode - key.pem',
        # 'opendistro_security.ssl.http.pemtrustedcas_filepath': 'root - ca.pem',
        # 'opendistro_security.allow_unsafe_democertificates': 'true',
        # 'opendistro_security.allow_default_init_securityindex': 'true',
        # 'opendistro_security.authcz.admin_dn': '\n  - CN=kirk,OU=client,O=client,L=test, C=de',
        #
        # 'opendistro_security.audit.type': 'internal_elasticsearch',
        # 'opendistro_security.enable_snapshot_restore_privilege': 'true',
        # 'opendistro_security.check_snapshot_restore_write_privileges': 'true',
        # 'opendistro_security.restapi.roles_enabled': '["all_access", "security_rest_api_access"]',
    }
    es_yml_dict.update({key: value
                        for key, value in params.config['configurations']['es'].items() if key != 'es_path_data'})

    es_yml_dict.update({
        'path.data': params.es_path_data,
        'http.port': params.es_http_port,
        'transport.tcp.port': params.es_transport_tcp_port,
        'cluster.name': params.config['clusterName'],
        'node.name': params.config['hostname'],
        'node.master': 'true' if params.config['hostname'] in es_masters else 'false',
        'node.data': 'true' if params.config['hostname'] in es_datas else 'false',
        'discovery.zen.ping.unicast.hosts': '[{}]'.format(', '.join(['\"{}:{}\"'.format(
            socket.gethostbyname(es_master), params.es_transport_tcp_port) for es_master in es_masters])),
    })
    discovery_min_masters = len(es_masters)/2 + 1
    if es_yml_dict.get('discovery.zen.minimum_master_nodes', 0) < discovery_min_masters:
        es_yml_dict['discovery.zen.minimum_master_nodes'] = discovery_min_masters

    es_yml_content = '\n'.join(['{}: {}'.format(key, value) for key, value in es_yml_dict.items()])

    File(format('{es_conf_dir}/jvm.options'), content=params.es_jvm_options,
         owner='root', group='elasticsearch', encoding='utf-8')
    File(format('{es_conf_dir}/elasticsearch.yml'), content=es_yml_content,
         owner='root', group='elasticsearch', encoding='utf-8')


def es_start():
    import params
    try:
        check_process_status(params.es_pid_file)
    except ComponentIsNotRunning:
        Execute(params.es_start_cmd, user='root', logoutput=True)


def es_stop():
    import params
    Execute(params.es_stop_cmd, user='root', logoutput=True)


def es_status():
    import params
    check_process_status(params.es_pid_file)


def kibana_pre_install():
    Package('opendistroforelasticsearch-kibana', action='remove')


def kibana_post_install():
    import params
    Execute(params.kibana_remove_security_cmd, user='root', logoutput=True)


def kibana_configure():
    import params
    es_masters = params.config['clusterHostInfo'].get('elk_master_hosts', [])
    kibana_yml_dict = {
        'elasticsearch.ssl.verificationMode': 'none',
        'elasticsearch.username': 'kibanaserver',
        'elasticsearch.password': 'kibanaserver',
        'elasticsearch.requestHeadersWhitelist': '["securitytenant", "Authorization"]',
        # 'opendistro_security.multitenancy.enabled': 'true',
        # 'opendistro_security.multitenancy.tenants.preferred': '["Private", "Global"]',
        # 'opendistro_security.readonly_mode.roles': '["kibana_read_only"]',
        'server.host': '0.0.0.0',
    }
    kibana_yml_dict.update({key: value for key, value in params.config['configurations']['kibana'].items()})
    kibana_yml_dict.update({
        'elasticsearch.url': 'http://{}:{}'.format(socket.gethostbyname(es_masters[0]), params.es_http_port),
        'server.port': params.kibana_server_port,
    })
    kibana_yml_content = '\n'.join(['{}: {}'.format(key, value) for key, value in kibana_yml_dict.items()])
    File(format('{kibana_conf_dir}/kibana.yml'), content=kibana_yml_content,
         owner='root', group='root', encoding='utf-8')


def kibana_start():
    import params
    Execute(params.kibana_start_cmd, user='root', logoutput=True)


def kibana_stop():
    import params
    Execute(params.kibana_stop_cmd, user='root', logoutput=True)


def kibana_status():
    import params
    code, _, _ = get_user_call_output(params.kibana_status_cmd, user='root', is_checked_call=False)
    if code != 0:
        raise ComponentIsNotRunning()
