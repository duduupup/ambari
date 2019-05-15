# coding=utf-8
from ambari_commons.config_utils import properties2dict
from resource_management import *
import xinsight


def common_configure():
    import params
    Directory(params.common_conf_dir, owner=params.common_user, group=params.common_group,
              create_parents=True, recursive_ownership=True, mode=0755)

    common_env = params.config['configurations']['common-env']
    common_cdh = params.config['configurations']['common-cdh']
    common_conf = params.config['configurations']['common-conf']

    cdh_env_dict = properties2dict(common_cdh['cdh_env'])
    xinsight_env_dict = properties2dict(common_env['xinsight_env'])

    ha_proxy_vip = xinsight.get_conf(common_conf, 'ha.proxy.vip')
    postgres_write_vip = xinsight.get_conf(common_conf, 'postgres.write.vip')
    redis_vip = xinsight.get_conf(common_conf, 'redis.vip')
    redis_host = '{}:{}'.format(redis_vip, xinsight.get_conf(common_conf, 'redis.port')) if redis_vip != '' else ''

    nginx_server = xinsight_env_dict['nginx.server']
    ldap_enable = True if xinsight_env_dict['ldap.enable'] == 'true' else False
    redis_cluster_host = xinsight_env_dict['redis.cluster.host']
    nginx_addr = '{}:{}'.format(nginx_server, xinsight.get_conf(common_conf, 'nginx.port')
                                ) if nginx_server != '' else ''

    xinsight_properties_dict = {
        'cdh': {
            'cdh.server': '{}:{}'.format(cdh_env_dict['cm.host'], cdh_env_dict['cm.port']),
            'cdh.username': cdh_env_dict['cm.user'],
            'cdh.password': cdh_env_dict['cm.user.password'],
            'zookeeper.quorum': cdh_env_dict['cdh.zookeeper.server'],
            'zookeeper.timeout': xinsight.get_conf(common_conf, 'zookeeper.timeout'),
            'hdfs.server': cdh_env_dict['cdh.hdfs.default.fs'],
            'hdfs.user': xinsight.get_conf(common_conf, 'hdfs.user'),
            'spark_server_addr': cdh_env_dict['cdh.yarn.rm.webapp.https.address'],
            'yarn.rm.webapp.address': cdh_env_dict['cdh.yarn.rm.webapp.address'],
            'kafka.broker_list': cdh_env_dict['cdh.kafka.broker'],
        },
        'redis': {
            'redis.host': redis_host,
            'redis.timeout': xinsight.get_conf(common_conf, 'redis.timeout'),
        },
        'redis_cluster': {
            'redis.cluster.host': redis_cluster_host,
            'redis.cluster.timeout': xinsight.get_conf(common_conf, 'redis.cluster.timeout'),
            'redis.cluster.maxRedirections': xinsight.get_conf(common_conf, 'redis.cluster.maxRedirections'),
        },
        'postgres': {
            'postgres.host': '{}:{}'.format(postgres_write_vip, xinsight.get_conf(common_conf, 'postgres.port')
                                            ) if postgres_write_vip != '' else '',
            'postgres.user': xinsight.get_conf(common_conf, 'postgres.user'),
            'postgres.password': xinsight.get_conf(common_conf, 'postgres.password'),
        },
        'aas': {
            'aas.host': nginx_addr,
            'aas_web.host': nginx_addr,

            'token.timeout': xinsight.get_conf(common_conf, 'aas.token.timeout'),
            'aas.kickout': xinsight.get_conf(common_conf, 'aas.kickout'),
            'aas.rest_service_name': xinsight.get_conf(common_conf, 'aas.rest_service_name'),
            'aas.config_service_name': xinsight.get_conf(common_conf, 'aas.config_service_name'),
            'aas.network.protocol': xinsight.get_conf(common_conf, 'aas.network.protocol'),

            'ldap.sync.flag': str(ldap_enable),
            'ldap.url': '{}:{}'.format(ha_proxy_vip, xinsight.get_conf(common_conf, 'ha.proxy.ldap.port')
                                       ) if ha_proxy_vip != '' else '',
            'ldap.base': 'dc={},dc={}'.format(xinsight_env_dict['ldap.domain.name'],
                                              xinsight_env_dict['ldap.domain.suffix']) if ldap_enable else '',
            'ldap.userDn': 'cn={},dc={},dc={}'.format(xinsight_env_dict['ldap.common.name'],
                                                      xinsight_env_dict['ldap.domain.name'],
                                                      xinsight_env_dict['ldap.domain.suffix']) if ldap_enable else '',
            'ldap.password': xinsight_env_dict['ldap.admin.password'] if ldap_enable else '',
        },
        'ccs': {
            'ccs.host': nginx_addr,
            'ccs.rest_service_name': xinsight.get_conf(common_conf, 'ccs.rest_service_name'),
            'ccs.config_service_name': xinsight.get_conf(common_conf, 'ccs.config_service_name'),
        },
        'cvs': {
            'cvs.host': nginx_addr,
            'cvs.config_service_name': xinsight.get_conf(common_conf, 'cvs.config_service_name'),
        },
        'license': {
            'license.host': nginx_addr,
            'license.config_service_name': xinsight.get_conf(common_conf, 'license.config_service_name'),
        },
        'ots': {
            'ots.host': nginx_addr,
            'ots.indexer_host': cdh_env_dict['cdh.hbase.indexer'],

            'ots.rest_service_name': xinsight.get_conf(common_conf, 'ots.rest_service_name'),
            'ots.config_service_name': xinsight.get_conf(common_conf, 'ots.config_service_name'),
        },
        'pds': {
            'pds.host': nginx_addr,
            'pds.gateway_host': '{}:{}'.format(ha_proxy_vip,
                                               xinsight.get_conf(common_conf, 'ha.proxy.pds.gateway.port')
                                               ) if ha_proxy_vip != '' else '',

            'pds.rest_service_name': xinsight.get_conf(common_conf, 'pds.rest_service_name'),
            'pds.config_service_name': xinsight.get_conf(common_conf, 'pds.config_service_name'),
        },
        'tsdb': {
            'tsdb.host': nginx_addr,
            'tsdb.gateway_host': ha_proxy_vip,

            'tsdb.rest_service_name': xinsight.get_conf(common_conf, 'tsdb.rest_service_name'),
            'tsdb.config_service_name': xinsight.get_conf(common_conf, 'tsdb.config_service_name'),
            'tsdb.gateway_port': xinsight.get_conf(common_conf, 'tsdb.gateway_port'),
            'tsdb.gateway_subscribe_port': xinsight.get_conf(common_conf, 'tsdb.gateway_subscribe_port'),
        },
        'oss': {
            'oss.host': nginx_addr,
            'oss.rest_service_name': xinsight.get_conf(common_conf, 'oss.rest_service_name'),
            'oss.config_service_name': xinsight.get_conf(common_conf, 'oss.config_service_name'),
        },
        'sts': {
            'sts.host': nginx_addr,
            'sts.impala.ldap.auth.enabled': cdh_env_dict['cdh.impala.ldap.enable'] if ldap_enable else 'false',
            'sts.impala.quorum': cdh_env_dict['cdh.impala.daemon.server'] if ha_proxy_vip == '' else ha_proxy_vip,
            'sts.impala.port': cdh_env_dict['cdh.impala.daemon.hs2.port'] if ha_proxy_vip == '' else xinsight.get_conf(
                common_conf, 'ha.proxy.impala.port'),
            'sts.kudu.master': cdh_env_dict['cdh.kudu.master'],
            'sts.kudu.master.port': cdh_env_dict['cdh.kudu.master.rpc.port'],
            'sts.tablet.server': cdh_env_dict['cdh.kudu.tablet.server'],

            'sts.rest_service_name': xinsight.get_conf(common_conf, 'sts.rest_service_name'),
            'sts.config_service_name': xinsight.get_conf(common_conf, 'sts.config_service_name'),
            'sts.impala.user': xinsight.get_conf(common_conf, 'sts.impala.user'),
            'sts.impala.password': xinsight_env_dict['ldap.impala.password'] if ldap_enable else '',
        },
        'tss': {
            'tss.host': nginx_addr,
            'tss.rest_service_name': xinsight.get_conf(common_conf, 'tss.rest_service_name'),
            'tss.config_service_name': xinsight.get_conf(common_conf, 'tss.config_service_name'),
        },
        'rgs': {
            'rgs.host': nginx_addr,
            'rgs.rest_service_name': xinsight.get_conf(common_conf, 'rgs.rest_service_name'),
            'rgs.config_service_name': xinsight.get_conf(common_conf, 'rgs.config_service_name'),
            'rgs.meta.topic': xinsight.get_conf(common_conf, 'rgs.meta.topic'),
        },
        'fcs': {
            'fcs.host': nginx_addr,
            'fcs.config_service_name': xinsight.get_conf(common_conf, 'fcs.config_service_name'),
        },
        'dts': {
            'dts.host': nginx_addr,
            'dts.config_service_name': xinsight.get_conf(common_conf, 'dts.config_service_name'),
        }
    }

    xinsight_properties_content = '\n'.join([
        '#{}\n{}'.format(section, ''.join(sorted(
            ['{}={}\n'.format(key, value) for key, value in xinsight_properties_dict[section].items()])
        )) for section in sorted(xinsight_properties_dict.keys())
    ])
    File(format("{service_path}/conf/xinsight.properties"), content=xinsight_properties_content, mode=0644,
         owner=params.common_user, group=params.common_group)
