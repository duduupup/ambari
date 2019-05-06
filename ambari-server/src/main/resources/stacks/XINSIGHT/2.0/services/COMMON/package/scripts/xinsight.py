from ambari_commons.config_utils import properties2dict

xinsight_default_dict = {
    'zookeeper.timeout': '3000',
    'hdfs.user': 'tomcat',
    'nginx.port': '80',
    'ha.proxy.port': '8866',
    'ha.proxy.ldap.port': '1389',
    'ha.proxy.impala.port': '31050',
    'ha.proxy.pds.gateway.port': '20006',
    'ha.proxy.tsdb.proxy': '19877',
    'ha.proxy.tsdb.gateway_port': '20007',
    'ha.proxy.tsdb.gateway_subscribe_port': '20008',
    'ldap.common.name': 'Manager',
    'ldap.domain.name': 'xinsight',
    'ldap.domain.suffix': 'com',
    'ldap.root.password': 'q1w2e3',
    'redis.timeout': '3000',
    'redis.cluster.timeout': '60000',
    'redis.cluster.maxRedirections': '3',
    'postgres.port': '5432',
    'postgres.user': 'xinsight',
    'postgres.password': 'root',
    'aas.rest_service_name': 'aas',
    'aas.config_service_name': 'aas_web',
    'aas.network.protocol': 'http',
    'aas.kickout': 'false',
    'aas.token.timeout': '86400000',
    'ccs.rest_service_name': 'ccsrest',
    'ccs.config_service_name': 'ccscfgsvr',
    'cvs.config_service_name': 'cvscfgsvr',
    'license.config_service_name': 'license',
    'ots.rest_service_name': 'otsrest',
    'ots.config_service_name': 'otscfgsvr',
    'pds.rest_service_name': 'pdsrest',
    'pds.config_service_name': 'pdscfgsvr',
    'pds.gateway.port': '10006',
    'tsdb.rest_service_name': 'tsdbrest',
    'tsdb.config_service_name': 'tsdbcfgsvr',
    'tsdb.proxy_port': '9877',
    'tsdb.gateway_port': '10007',
    'tsdb.gateway_subscribe_port': '10008',
    'sts.rest_service_name': 'stsrest',
    'sts.config_service_name': 'stscfgsvr',
    'sts.impala.user': 'impala',
    'sts.impala.password': 'q1w2e3',
    'oss.rest_service_name': 'ossrest',
    'oss.config_service_name': 'osscfgsvr',
    'tss.rest_service_name': 'tssrest',
    'tss.config_service_name': 'tsscfgsvr',
    'rgs.rest_service_name': 'rgsrest',
    'rgs.config_service_name': 'rgscfgsvr',
    'rgs.meta.topic': 'rgs.meta',
    'fcs.config_service_name': 'fcscfgsvr',
    'dts.config_service_name': 'dtscfgsvr',
}


def get_conf(common_conf, item_name):
    if item_name in xinsight_default_dict:
        return common_conf.get(item_name, xinsight_default_dict.get(item_name, ''))
    else:
        xinsight_conf_dict = properties2dict(common_conf['xinsight_conf'])
        return xinsight_conf_dict.get(item_name, '')
