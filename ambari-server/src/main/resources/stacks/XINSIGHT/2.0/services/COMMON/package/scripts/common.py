# coding=utf-8
import socket
from ambari_commons.config_utils import properties2dict
from resource_management import *


def common_configure():
    import params
    Directory(params.common_conf_dir, owner=params.common_user, group=params.common_group,
              create_parents=True, recursive_ownership=True, mode=0755)

    # Step1: set by default
    common_configuration_dict = _common_default_configuration_dict()
    # Step2: update by env
    _common_configuration_update_by_env(common_configuration_dict)
    # Step3: update by custom configuration
    update_configuration_dict = {key: value for key, value in params.config['configurations']['common-conf']
                                 if key in common_configuration_dict}
    common_configuration_dict.update(update_configuration_dict)

    basic_xinsight_properties_content = _xinsight_properties_content(common_configuration_dict)
    custom_xinsight_properties_content = '\n'.join([
        'key=value' for key, value in params.config['configurations']['common-conf']
        if key not in common_configuration_dict and key != 'xinsight_env'
    ])
    xinsight_properties_content = '%s\n\n# others\n%s\n' % (
        basic_xinsight_properties_content, custom_xinsight_properties_content)
    File(format("{common_conf_dir}/xinsight.properties"), content=xinsight_properties_content, mode=0644,
         owner=params.common_user, group=params.common_group)


_common_properties_items = (
    ('cdh', ('cdh.server', 'cdh.username', 'cdh.password', 'zookeeper.quorum', 'zookeeper.timeout',
             'hdfs.server', 'hdfs.user', 'spark_server_addr', 'yarn.rm.webapp.address', 'kafka.broker_list', )),
    ('redis', ('redis.host', 'redis.timeout', )),
    ('redis cluster', ('redis.cluster.host', 'redis.cluster.timeout', 'redis.cluster.maxRedirections', )),
    ('postgres', ('postgres.host', 'postgres.user', 'postgres.password', )),
    ('aas', ('aas.host', 'aas_web.host', 'aas.rest_service_name', 'aas.config_service_name',
             'aas.network.protocol', 'token.timeout', 'aas.kickout',
             'ldap.sync.flag', 'ldap.url', 'ldap.base', 'ldap.userDn', 'ldap.password', )),
    ('ccs', ('ccs.host', 'ccs.rest_service_name', 'ccs.config_service_name', )),
    ('cvs', ('cvs.host', 'cvs.config_service_name', )),
    ('license', ('license.host', 'license.config_service_name', )),
    ('ots', ('ots.host', 'ots.rest_service_name', 'ots.config_service_name', 'ots.indexer_host', )),
    ('pds', ('pds.host', 'pds.rest_service_name', 'pds.config_service_name', 'pds.gateway_host', )),
    ('tsdb', ('tsdb.host', 'tsdb.rest_service_name', 'tsdb.config_service_name',
              'tsdb.gateway_host', 'tsdb.gateway_port', 'tsdb.gateway_subscribe_port', )),
    ('oss', ('oss.host', 'oss.rest_service_name', 'oss.config_service_name')),
    ('sts', ('sts.host', 'sts.rest_service_name', 'sts.config_service_name',
             'sts.kudu.master', 'sts.kudu.master.port',
             'sts.impala.quorum', 'sts.impala.ldap.auth.enabled', 'sts.impala.user', 'sts.impala.password', )),
    ('tss', ('tss.host', 'tss.rest_service_name', 'tss.config_service_name', )),
    ('rgs', ('rgs.host', 'rgs.rest_service_name', 'rgs.config_service_name', 'rgs.meta.topic', 'sts.tablet.server', )),
    ('fcs', ('fcs.host', 'fcs.config_service_name', )),
    ('dts', ('dts.host', 'dts.config_service_name', )),
)


def _xinsight_properties_content(common_configuration_dict):
    configuration_dict = {key.replace('.', '_'): value for key, value in common_configuration_dict.items()}
    template = '\n'.join([
        '# {}\n{}'.format(section[0], ''.join(['%s={{%s}}\n' % (item, item.replace('.', '_')) for item in section[1]]))
        for section in _common_properties_items
    ])
    print(template)
    print(configuration_dict)
    return InlineTemplate(template, extra_imports=[], **configuration_dict).get_content()


def _common_default_configuration_dict():
    configuration_dict = {}
    for section in _common_properties_items:
        for item in section[1]:
            configuration_dict[item] = ''
    configuration_dict.update({
        'zookeeper.timeout': '3000', 'hdfs.user': 'tomcat',
        'redis.timeout': '3000', 'redis.cluster.timeout': '60000', 'redis.cluster.maxRedirections': '3',
        'aas.rest_service_name': 'aas', 'aas.config_service_name': 'aas_web', 'aas.network.protocol': 'http',
        'aas.kickout': 'false', 'token.timeout': '86400000', 'ldap.sync.flag': 'false',
        'ccs.rest_service_name': 'ccsrest', 'ccs.config_service_name': 'ccscfgsvr',
        'cvs.config_service_name': 'cvscfgsvr',
        'license.config_service_name': 'license',
        'ots.rest_service_name': 'otsrest', 'ots.config_service_name': 'otscfgsvr',
        'pds.rest_service_name': 'pdsrest', 'pds.config_service_name': 'pdscfgsvr',
        'tsdb.rest_service_name': 'tsdbrest', 'tsdb.config_service_name': 'tsdbcfgsvr',
        'sts.rest_service_name': 'stsrest', 'sts.config_service_name': 'stscfgsvr',
        'sts.impala.ldap.auth.enabled': 'false',
        'oss.rest_service_name': 'ossrest', 'oss.config_service_name': 'osscfgsvr',
        'tss.rest_service_name': 'tssrest', 'tss.config_service_name': 'tsscfgsvr',
        'rgs.rest_service_name': 'rgsrest', 'rgs.config_service_name': 'rgscfgsvr',
        'fcs.config_service_name': 'fcscfgsvr',
        'dts.config_service_name': 'dtscfgsvr',
    })
    return configuration_dict


def _common_configuration_update_by_env(common_configuration_dict):
    import params
    cdh_env_dict = properties2dict(params.config['configurations']['common-cdh']['cdh_env'])
    # !!!!!! Note: keep the order, haproxy nginx must at the last
    # cdh
    common_configuration_dict.update({
        'cdh.server': '{}:{}'.format(cdh_env_dict['cm.host'], cdh_env_dict['cm.port']),
        'cdh.username': cdh_env_dict['cm.user'],
        'cdh.password': cdh_env_dict['cm.user.password'],
        'zookeeper.quorum': cdh_env_dict['cdh.zookeeper.server'],
        'hdfs.server': cdh_env_dict['cdh.hdfs.default.fs'],
        'spark_server_addr': cdh_env_dict['cdh.yarn.rm.webapp.https.address'],
        'yarn.rm.webapp.address': cdh_env_dict['cdh.yarn.rm.webapp.address'],
        'kafka.broker_list': cdh_env_dict['cdh.kafka.broker'],

        'ots.indexer_host': cdh_env_dict['cdh.hbase.indexer'],
        'sts.impala.ldap.auth.enabled': cdh_env_dict['cdh.impala.ldap.enable'],
        'sts.impala.quorum': cdh_env_dict['cdh.impala.daemon.server'],
        'sts.impala.port': cdh_env_dict['cdh.impala.daemon.hs2.port'],
        'sts.kudu.master': cdh_env_dict['cdh.kudu.master'],
        'sts.kudu.master.port': cdh_env_dict['cdh.kudu.master.rpc.port'],
        'sts.tablet.server': cdh_env_dict['cdh.kudu.tablet.server'],
    })
    # redis
    if 'redis_server_hosts' in params.config['clusterHostInfo']:
        conf = params.config['configurations']['redis-conf-pub']
        common_configuration_dict.update({
            'redis.host': '{}:{}'.format(conf['redis_vip'], conf['redis_port'])
        })
    # redis cluster
    if 'rediscls_server_hosts' in params.config['clusterHostInfo']:
        servers = params.config['clusterHostInfo']['rediscls_server_hosts']
        conf = params.config['configurations']['rediscls-conf-pub']
        common_configuration_dict.update({
            'redis.cluster.host': ','.join([
                ','.join(['{}:{}'.format(socket.gethostbyname(server), port) for port in conf['rediscls_port']])
                for server in servers
            ]),
        })
    # rds
    if 'rds_server_hosts' in params.config['clusterHostInfo']:
        conf = params.config['configurations']['rds-conf-pub']
        common_configuration_dict.update({
            'postgres.host': '{}:{}'.format(conf['rds_xinsight_meta_write_vip'], conf['rds_xinsight_meta_port']),
            'postgres.user': conf['rds_xinsight_meta_user'],
            'postgres.password': conf['rds_xinsight_meta_password'],
        })
    # pds
    if 'pds_gateway_hosts' in params.config['clusterHostInfo']:
        servers = params.config['clusterHostInfo']['pds_gateway_hosts']
        conf = params.config['configurations']['pds-conf-pub']
        common_configuration_dict.update({
            'pds.gateway_host': ','.join(['{}:{}'.format(socket.gethostbyname(server), conf['pds_gateway_port'])
                                          for server in servers]),
        })
    # tsdb
    if 'tsdb_gateway_hosts' in params.config['clusterHostInfo']:
        servers = params.config['clusterHostInfo']['tsdb_gateway_hosts']
        conf = params.config['configurations']['tsdb-conf-pub']
        common_configuration_dict.update({
            'tsdb.gateway_host': ','.join([socket.gethostbyname(server) for server in servers]),
            'tsdb.gateway.port': conf['tsdb_gateway_port'],
            'tsdb.gateway.subscribe.port': conf['tsdb_gateway_subscribe_port'],
        })
    # rgs
    if 'rgs_server_hosts' in params.config['clusterHostInfo']:
        conf = params.config['configurations']['tsdb-conf-pub']
        common_configuration_dict.update({
            'rgs.meta.topic': conf['rgs_meta_topic'],
        })
    # ldap
    if 'ldap_server_hosts' in params.config['clusterHostInfo']:
        servers = params.config['clusterHostInfo']['ldap_server_hosts']
        conf = params.config['configurations']['ldap-conf-pub']
        common_configuration_dict.update({
            'ldap.sync.flag': 'true',
            'ldap.url': ','.join(['{}:{}'.format(socket.gethostbyname(server), conf['ldap_port'])
                                  for server in servers]),
            'ldap.base': 'dc={},dc={}'.format(conf['ldap_domain_name'], conf['ldap_domain_suffix']),
            'ldap.userDn': 'cn={},dc={},dc={}'.format(conf['ldap_common_name'], conf['ldap_domain_name'],
                                                      conf['ldap_domain_suffix']),
            'ldap.password': conf['ldap_admin_password'],

            'sts.impala.ldap.auth.enabled': conf['cdh_impala_ldap_enable'],
            'sts.impala.user': conf['ldap_impala_user'],
            'sts.impala.password': conf['ldap_impala_password'],
        })
    # nginx
    if 'nginx_server_hosts' in params.config['clusterHostInfo']:
        servers = params.config['clusterHostInfo']['nginx_server_hosts']
        conf = params.config['configurations']['nginx-conf-pub']
        nginx_server = ','.join(['{}:{}'.format(socket.gethostbyname(server), conf['nginx_port'])
                                 for server in servers])
        common_configuration_dict.update({
            'aas.host': nginx_server, 'aas_web.host': nginx_server, 'ccs.host': nginx_server,
            'cvs.host': nginx_server, 'license.host': nginx_server, 'ots.host': nginx_server,
            'pds.host': nginx_server, 'tsdb.host': nginx_server, 'oss.host': nginx_server,
            'sts.host': nginx_server, 'tss.host': nginx_server, 'rgs.host': nginx_server,
            'fcs.host': nginx_server, 'dts.host': nginx_server,
        })
    # haproxy
    if 'haproxy_server_hosts' in params.config['clusterHostInfo']:
        conf = params.config['configurations']['haproxy-conf-pub']
        haproxy_vip = conf['haproxy_vip']
        common_configuration_dict.update({
            'ldap.url': '{}:{}'.format(haproxy_vip, conf['haproxy_ldap_port']),
            'pds.gateway_host': '{}:{}'.format(haproxy_vip, conf['haproxy_pds_gateway_port']),
            'tsdb.gateway_host': haproxy_vip,
            'tsdb.gateway_port': conf['haproxy_tsdb_gateway_port'],
            'tsdb.gateway_subscribe_port': conf['haproxy_tsdb_gateway_subscribe_port'],
            'sts.impala.quorum': haproxy_vip,
            'sts.impala.port': conf['haproxy_impala_port'],
        })
