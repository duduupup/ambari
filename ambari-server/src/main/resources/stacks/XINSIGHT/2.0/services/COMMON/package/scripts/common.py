# coding=utf-8
from ambari_commons.config_utils import properties2dict
from resource_management import *
import xinsight


def common_configure():
    import params
    Directory(params.common_conf_dir, owner=params.common_user, group=params.common_group,
              create_parents=True, recursive_ownership=True, mode=0755)

    common_conf = params.config['configurations']['common-conf']
    cdh_env_dict = properties2dict(params.config['configurations']['common-cdh']['cdh_env'])
    xinsight_env_dict = properties2dict(params.config['configurations']['common-env']['xinsight_env'])

    nginx_server = xinsight_env_dict.get('nginx.server', '')
    ha_proxy_vip = xinsight_env_dict.get('haproxy.vip', '')
    ldap_enable = True if xinsight_env_dict['ldap.enable'] == 'true' else False

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
            'redis.host': xinsight_env_dict.get('redis.server', ''),
            'redis.timeout': xinsight.get_conf(common_conf, 'redis.timeout'),
        },
        'redis_cluster': {
            'redis.cluster.host': xinsight_env_dict.get('redis.cluster.server', ''),
            'redis.cluster.timeout': xinsight.get_conf(common_conf, 'redis.cluster.timeout'),
            'redis.cluster.maxRedirections': xinsight.get_conf(common_conf, 'redis.cluster.maxRedirections'),
        },
        'postgres': {
            'postgres.host': xinsight_env_dict.get('postgres.server', ''),
            'postgres.user': xinsight_env_dict.get('postgres.user', ''),
            'postgres.password': xinsight_env_dict.get('postgres.password', ''),
        },
        'aas': {
            'aas.host': nginx_server,
            'aas_web.host': nginx_server,

            'ldap.sync.flag': 'true' if ldap_enable else 'false',
            'ldap.url': '{}:{}'.format(ha_proxy_vip, xinsight_env_dict.get('haproxy.ldap.port', '')
                                       ) if ha_proxy_vip != '' else xinsight_env_dict.get('ldap.server', ''),
            'ldap.base': 'dc={},dc={}'.format(xinsight_env_dict['ldap.domain.name'],
                                              xinsight_env_dict['ldap.domain.suffix']) if ldap_enable else '',
            'ldap.userDn': 'cn={},dc={},dc={}'.format(xinsight_env_dict['ldap.common.name'],
                                                      xinsight_env_dict['ldap.domain.name'],
                                                      xinsight_env_dict['ldap.domain.suffix']) if ldap_enable else '',
            'ldap.password': xinsight_env_dict['ldap.admin.password'] if ldap_enable else '',

            'token.timeout': xinsight.get_conf(common_conf, 'aas.token.timeout'),
            'aas.kickout': xinsight.get_conf(common_conf, 'aas.kickout'),
            'aas.rest_service_name': xinsight.get_conf(common_conf, 'aas.rest_service_name'),
            'aas.config_service_name': xinsight.get_conf(common_conf, 'aas.config_service_name'),
            'aas.network.protocol': xinsight.get_conf(common_conf, 'aas.network.protocol'),
        },
        'ccs': {
            'ccs.host': nginx_server,
            'ccs.rest_service_name': xinsight.get_conf(common_conf, 'ccs.rest_service_name'),
            'ccs.config_service_name': xinsight.get_conf(common_conf, 'ccs.config_service_name'),
        },
        'cvs': {
            'cvs.host': nginx_server,
            'cvs.config_service_name': xinsight.get_conf(common_conf, 'cvs.config_service_name'),
        },
        'license': {
            'license.host': nginx_server,
            'license.config_service_name': xinsight.get_conf(common_conf, 'license.config_service_name'),
        },
        'ots': {
            'ots.host': nginx_server,
            'ots.indexer_host': cdh_env_dict['cdh.hbase.indexer'],

            'ots.rest_service_name': xinsight.get_conf(common_conf, 'ots.rest_service_name'),
            'ots.config_service_name': xinsight.get_conf(common_conf, 'ots.config_service_name'),
        },
        'pds': {
            'pds.host': nginx_server,
            'pds.gateway_host': '{}:{}'.format(ha_proxy_vip, xinsight_env_dict.get('haproxy.pds.gateway.port', '')
                                               ) if ha_proxy_vip != '' else '',

            'pds.rest_service_name': xinsight.get_conf(common_conf, 'pds.rest_service_name'),
            'pds.config_service_name': xinsight.get_conf(common_conf, 'pds.config_service_name'),
        },
        'tsdb': {
            'tsdb.host': nginx_server,
            'tsdb.gateway_host': '{}:{}'.format(ha_proxy_vip, xinsight_env_dict.get('haproxy.tsdb.gateway.port')
                                                ) if ha_proxy_vip else xinsight_env_dict.get('tsdb.gateway.server', ''),

            'tsdb.rest_service_name': xinsight.get_conf(common_conf, 'tsdb.rest_service_name'),
            'tsdb.config_service_name': xinsight.get_conf(common_conf, 'tsdb.config_service_name'),
            'tsdb.gateway_port': xinsight.get_conf(common_conf, 'tsdb.gateway_port'),
            'tsdb.gateway_subscribe_port': xinsight.get_conf(common_conf, 'tsdb.gateway_subscribe_port'),
        },
        'oss': {
            'oss.host': nginx_server,
            'oss.rest_service_name': xinsight.get_conf(common_conf, 'oss.rest_service_name'),
            'oss.config_service_name': xinsight.get_conf(common_conf, 'oss.config_service_name'),
        },
        'sts': {
            'sts.host': nginx_server,
            'sts.impala.ldap.auth.enabled': cdh_env_dict['cdh.impala.ldap.enable'],
            'sts.impala.quorum': cdh_env_dict['cdh.impala.daemon.server'] if ha_proxy_vip == '' else ha_proxy_vip,
            'sts.impala.port': cdh_env_dict['cdh.impala.daemon.hs2.port'] if ha_proxy_vip == '' else (
                xinsight_env_dict.get('ha.proxy.impala.port')),
            'sts.kudu.master': cdh_env_dict['cdh.kudu.master'],
            'sts.kudu.master.port': cdh_env_dict['cdh.kudu.master.rpc.port'],
            'sts.tablet.server': cdh_env_dict['cdh.kudu.tablet.server'],

            'sts.rest_service_name': xinsight.get_conf(common_conf, 'sts.rest_service_name'),
            'sts.config_service_name': xinsight.get_conf(common_conf, 'sts.config_service_name'),
            'sts.impala.user': xinsight_env_dict.get('ldap.impala.user', ''),
            'sts.impala.password': xinsight_env_dict.get('ldap.impala.password', ''),
        },
        'tss': {
            'tss.host': nginx_server,
            'tss.rest_service_name': xinsight.get_conf(common_conf, 'tss.rest_service_name'),
            'tss.config_service_name': xinsight.get_conf(common_conf, 'tss.config_service_name'),
        },
        'rgs': {
            'rgs.host': nginx_server,
            'rgs.rest_service_name': xinsight.get_conf(common_conf, 'rgs.rest_service_name'),
            'rgs.config_service_name': xinsight.get_conf(common_conf, 'rgs.config_service_name'),
            'rgs.meta.topic': xinsight_env_dict.get('rgs.meta.topic', ''),
        },
        'fcs': {
            'fcs.host': nginx_server,
            'fcs.config_service_name': xinsight.get_conf(common_conf, 'fcs.config_service_name'),
        },
        'dts': {
            'dts.host': nginx_server,
            'dts.config_service_name': xinsight.get_conf(common_conf, 'dts.config_service_name'),
        }
    }

    xinsight_properties_content = '\n'.join([
        '#{}\n{}'.format(section, ''.join(sorted(
            ['{}={}\n'.format(key, value) for key, value in xinsight_properties_dict[section].items()])
        )) for section in sorted(xinsight_properties_dict.keys())
    ])
    File(format("{common_conf_dir}/xinsight.properties"), content=xinsight_properties_content, mode=0644,
         owner=params.common_user, group=params.common_group)
