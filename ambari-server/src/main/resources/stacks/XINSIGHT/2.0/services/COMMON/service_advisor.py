#!/usr/bin/env ambari-python-wrap
"""
Licensed to the Apache Software Foundation (ASF) under one
or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.  The ASF licenses this file
to you under the Apache License, Version 2.0 (the
"License"); you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import imp
import os
import traceback
import socket
import base64
import urllib2
import ambari_simplejson as json
from ambari_commons.config_utils import properties2dict, xml2dict
from resource_management import Fail
from resource_management.core.logger import Logger
import ambari_commons.network as network


class Cdh(object):
    @staticmethod
    def parse_xsetup_conf(xsetup_conf_dict, ambari_hosts):
        cm_host = xsetup_conf_dict.get('cm.host', '')
        cm_port = int(xsetup_conf_dict.get('cm.port', '7180'))
        cm_admin = xsetup_conf_dict.get('cm.admin', 'admin')
        cm_admin_password = xsetup_conf_dict.get('cm.admin.password', 'admin')
        cm_user = xsetup_conf_dict.get('cm.user', 'view')
        cm_user_password = xsetup_conf_dict.get('cm.user.password', 'view')
        exceptions = []
        if cm_host == '':
            for host in ambari_hosts:
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(1)
                    s.connect((host, cm_port))
                    cm_host = host
                    break
                except Exception as e:
                    exceptions.append(e)
            if cm_host == '':
                for i in range(0, len(ambari_hosts)):
                    Logger.error('%s: %s' % (ambari_hosts[i], str(exceptions[i])))
                raise Fail('parse cm.hosts({}) failed.'.format(ambari_hosts))
        return cm_host, cm_port, cm_admin, cm_admin_password, cm_user, cm_user_password

    @staticmethod
    def _parse_data(data_content, data_type):
        if data_type == 'text':
            return data_content
        elif data_type == 'json':
            return json.loads(data_content)
        elif data_type == 'properties':
            return properties2dict(data_content)
        elif data_type == 'xml':
            return xml2dict(data_content)
        else:
            raise KeyError('unknown rsp_type[{}]'.format(data_type))

    def __init__(self, xsetup_conf_dict, ambari_hosts):
        # TODO: kudu tablet server, kafka
        self.cm_host, self.cm_port, self.cm_admin, self.cm_admin_password, self.cm_user, self.cm_user_password = \
            Cdh.parse_xsetup_conf(xsetup_conf_dict, ambari_hosts)
        self.cdh_hosts = self._get_cdh_hosts()
        self.cdh_cluster_name = self._get_cdh_cluster_name()
        self.cdh_zookeeper_info = self._get_cdh_zookeeper_info()
        self.cdh_hdfs_info = self._get_cdh_hdfs_info()
        self.cdh_yarn_info = self._get_cdh_yarn_info()
        self.cdh_hbase_info = self._get_cdh_hbase_info()
        self.cdh_kafka_info = self._get_cdh_kafka_info()
        self.cdh_impala_info = self._get_cdh_impala_info()
        self.cdh_kudu_info = self._get_cdh_kudu_info()

    def __str__(self):
        return 'CDH[\ncluster_name={}\nhosts={}\ncm={}\nzookeeper={}\nhdfs={}\nyarn={}\nhbase={}\nkafka={}\nimpala={}\nkudu={}\n]'.format(
            self.cdh_cluster_name, [host['ip'] for host in self.cdh_hosts.values()], {
                'cm': '{}:{}'.format(self.cm_host, self.cm_port),
                'admin': '{}:{}'.format(self.cm_admin, self.cm_admin_password),
                'user': '{}:{}'.format(self.cm_user, self.cm_user_password)
            }, self.cdh_zookeeper_info, self.cdh_hdfs_info, self.cdh_yarn_info, self.cdh_hbase_info,
            self.cdh_kafka_info, self.cdh_impala_info, self.cdh_kudu_info)

    __repr__ = __str__

    def get_cdh_nodes(self):
        return ' '.join([host['ip'] for host in self.cdh_hosts.values()])

    def _get_cdh_hosts(self):
        ret = self._call_cm_api('/api/v6/hosts')
        try:
            return {host['hostId']: {'ip': host['ipAddress'], 'hostname': host['hostname']}
                    for host in ret.get('items', []) if 'hostId' in host}
        except Exception as e:
            Logger.error(str(e))
            raise Fail('parse cdh.hosts({}) failed. '.format(ret))

    def _get_cdh_cluster_name(self):
        ret = self._call_cm_api('/api/v6/clusters')
        try:
            return ret.get('items', [])[0]['displayName']
        except Exception as e:
            Logger.error(str(e))
            raise Fail('parse cdh.cluster.name({}) failed. '.format(ret))

    def _call_cm_api(self, url, data=None, rsp_type='json'):
        conn = network.get_http_connection(self.cm_host, self.cm_port)
        quote_url = urllib2.quote(url)
        try:
            user_pass = base64.b64encode(b'{}:{}'.format(self.cm_admin, self.cm_admin_password)).decode("ascii")
            conn.request("GET", quote_url, headers={'Authorization': 'Basic {}'.format(user_pass)},
                         body=json.dumps(data))
        except socket.error as e:
            conn.close()
            Logger.error(str(e))
            raise Fail('connect to cm[{}:{}] failed.'.format(self.cm_admin, self.cm_admin_password))
        else:
            response = conn.getresponse()
            rsp_data = response.read()
            conn.close()
            if response.status != 200:
                raise Fail('request cm_api[http://{}:{}{}] returned {}'.format(
                    self.cm_host, self.cm_port, quote_url, response.status))
            else:
                try:
                    return Cdh._parse_data(rsp_data, rsp_type)
                except Exception as e:
                    Logger.error(str(e))
                    raise Fail('parse cm_api[http://{}:{}{}] response({}) failed'.format(
                        self.cm_host, self.cm_port, quote_url, rsp_data))

    def _url_hostname_to_ip(self, url):
        """
        :param url:
            # print(_url_hostname_to_ip('a'))
            # print(_url_hostname_to_ip('a/'))
            # print(_url_hostname_to_ip('a/a'))
            # print(_url_hostname_to_ip('a:7180'))
            # print(_url_hostname_to_ip('a:7180/'))
            # print(_url_hostname_to_ip('a:7180/a'))
            # print(_url_hostname_to_ip('hdfs://a'))
            # print(_url_hostname_to_ip('hdfs://a/'))
            # print(_url_hostname_to_ip('hdfs://a/a'))
            # print(_url_hostname_to_ip('hdfs://a:7180'))
            # print(_url_hostname_to_ip('hdfs://a:7180/'))
            # print(_url_hostname_to_ip('hdfs://a:7180/a'))
            #
            # print(_url_hostname_to_ip('bdttest01'))
            # print(_url_hostname_to_ip('bdttest01/'))
            # print(_url_hostname_to_ip('bdttest01/bdttest01'))
            # print(_url_hostname_to_ip('bdttest01:7180'))
            # print(_url_hostname_to_ip('bdttest01:7180/'))
            # print(_url_hostname_to_ip('bdttest01:7180/bdttest01'))
            # print(_url_hostname_to_ip('hdfs://bdttest01'))
            # print(_url_hostname_to_ip('hdfs://bdttest01/'))
            # print(_url_hostname_to_ip('hdfs://bdttest01/a'))
            # print(_url_hostname_to_ip('hdfs://bdttest01:7180'))
            # print(_url_hostname_to_ip('hdfs://bdttest01:7180/'))
            # print(_url_hostname_to_ip('hdfs://bdttest01:7180/bdttest01'))
        :return:
        """
        pre_len = url.find('://')
        if pre_len == -1:
            hostname_start = 0
        else:
            hostname_start = pre_len + 3

        url_content = url[hostname_start:]
        hostname_len = url_content.find(':')
        if hostname_len == -1:
            hostname_len = url_content.find('/')
        if hostname_len == -1:
            hostname_len = len(url_content)

        url_prefix = url[0:hostname_start]
        hostname = url[hostname_start:hostname_start+hostname_len]
        url_suffix = url[hostname_start+hostname_len:]

        for host in self.cdh_hosts.values():
            if hostname == host['hostname']:
                return url_prefix + host['ip'] + url_suffix
        return url

    def _cm_service_roles_url(self, service_name):
        return '/api/v6/clusters/{}/services/{}/roles'.format(self.cdh_cluster_name, service_name)

    def _cm_service_config_url(self, service_name, role_name, config_file_name):
        return '/api/v6/clusters/{}/services/{}/roles/{}/process/configFiles/{}'.format(
            self.cdh_cluster_name, service_name, role_name, config_file_name)

    def _get_cdh_zookeeper_info(self):
        service_name = 'zookeeper'
        ret = self._call_cm_api(self._cm_service_roles_url(service_name))
        try:
            server_items = [item for item in ret.get('items', []) if item.get('type', '') == 'SERVER']
            server_role_name = server_items[0]['name']
            servers = [self.cdh_hosts[item['hostRef']['hostId']]['ip'] for item in server_items]
        except Exception as e:
            Logger.error(str(e))
            raise Fail('parse cdh.zookeeper.servers({}) failed. '.format(ret))

        ret = self._call_cm_api(self._cm_service_config_url(
            service_name, server_role_name, 'zoo.cfg'), rsp_type='properties')
        try:
            client_port = ret['clientPort']
        except Exception as e:
            Logger.error(str(e))
            raise Fail('parse cdh.zookeeper.clientPort({}) failed. '.format(ret))

        return {'server': ','.join(['{}:{}'.format(server, client_port) for server in servers])}

    def _get_cdh_hdfs_info(self):
        service_name = 'hdfs'
        ret = self._call_cm_api(self._cm_service_roles_url(service_name))
        try:
            nn_items = [item for item in ret.get('items', []) if item.get('type', '') == 'NAMENODE']
            nn_role_name = nn_items[0]['name']
        except Exception as e:
            Logger.error(str(e))
            raise Fail('parse cdh.hdfs.namenode({}) failed. '.format(ret))

        ret = self._call_cm_api(self._cm_service_config_url(
            service_name, nn_role_name, 'core-site.xml'), rsp_type='xml')
        try:
            default_fs = self._url_hostname_to_ip(ret['fs.defaultFS'])
        except Exception as e:
            Logger.error(str(e))
            raise Fail('parse cdh.hdfs.defaultFS({}) failed. '.format(ret))

        return {'default_fs': default_fs}

    def _get_cdh_yarn_info(self):
        service_name = 'yarn'
        ret = self._call_cm_api(self._cm_service_roles_url(service_name))
        try:
            rm_items = [item for item in ret.get('items', []) if item.get('type', '') == 'RESOURCEMANAGER']
            rm_role_name = rm_items[0]['name']
        except Exception as e:
            Logger.error(str(e))
            raise Fail('parse cdh.yarn.rm(({}) failed. '.format(ret))

        ret = self._call_cm_api(self._cm_service_config_url(
            service_name, rm_role_name, 'yarn-site.xml'), rsp_type='xml')
        try:
            if 'yarn.resourcemanager.ha.rm-ids' in ret:
                rm_webapp_address = [
                    self._url_hostname_to_ip(ret['yarn.resourcemanager.webapp.address.{}'.format(rm_id)])
                    for rm_id in ret['yarn.resourcemanager.ha.rm-ids'].strip().split(',')]
                rm_webapp_https_address = [
                    self._url_hostname_to_ip(ret['yarn.resourcemanager.webapp.https.address.{}'.format(rm_id)])
                    for rm_id in ret['yarn.resourcemanager.ha.rm-ids'].strip().split(',')]
            else:
                rm_webapp_address = [self._url_hostname_to_ip(ret['yarn.resourcemanager.webapp.address'])]
                rm_webapp_https_address = [self._url_hostname_to_ip(ret['yarn.resourcemanager.webapp.https.address'])]
        except Exception as e:
            Logger.error(str(e))
            raise Fail('parse cdh.yarn.resourcemanager.webapp.address({}) failed. '.format(ret))

        return {'rm_webapp_address': ','.join(rm_webapp_address),
                'rm_webapp_https_address': ','.join(rm_webapp_https_address)}

    def _get_cdh_hbase_info(self):
        service_name = 'ks_indexer'
        ret = self._call_cm_api(self._cm_service_roles_url(service_name))
        try:
            indexer_items = [item for item in ret.get('items', []) if item.get('type', '') == 'HBASE_INDEXER']
            indexers = [self.cdh_hosts[item['hostRef']['hostId']]['ip'] for item in indexer_items]
        except Exception as e:
            Logger.error(str(e))
            raise Fail('parse cdh.hbase.indexer(({}) failed. '.format(ret))
        return {'indexer': ','.join(indexers)}

    def _get_cdh_kafka_info(self):
        service_name = 'kafka'
        ret = self._call_cm_api(self._cm_service_roles_url(service_name))
        try:
            broker_items = [item for item in ret.get('items', []) if item.get('type', '') == 'KAFKA_BROKER']
            brokers = [self.cdh_hosts[item['hostRef']['hostId']]['ip'] for item in broker_items]
            broker_role_name = broker_items[0]['name']
        except Exception as e:
            Logger.error(str(e))
            raise Fail('parse cdh.kafka.broker(({}) failed. '.format(ret))

        ret = self._call_cm_api(self._cm_service_config_url(
            service_name, broker_role_name, 'kafka.properties'), rsp_type='properties')
        try:
            port = ret['port']
        except Exception as e:
            Logger.error(str(e))
            raise Fail('parse cdh.kafka.broker.port({}) failed. '.format(ret))
        return {'broker': ','.join(['{}:{}'.format(broker, port) for broker in brokers])}

    def _get_cdh_impala_info(self):
        service_name = 'impala'
        ret = self._call_cm_api(self._cm_service_roles_url(service_name))
        try:
            daemon_items = [item for item in ret.get('items', []) if item.get('type', '') == 'IMPALAD']
            daemon_servers = [self.cdh_hosts[item['hostRef']['hostId']]['ip'] for item in daemon_items]
            daemon_role_name = daemon_items[0]['name']
        except Exception as e:
            Logger.error(str(e))
            raise Fail('parse cdh.impala.daemon(({}) failed. '.format(ret))

        ret = self._call_cm_api(self._cm_service_config_url(
            service_name, daemon_role_name, 'impala-conf/impalad_flags'), rsp_type='text')
        try:
            port_line = None
            ldap_enable_line = None
            for line in ret.strip().split('\n'):
                if line.startswith('-hs2_port'):
                    port_line = line
                if line.startswith('-enable_ldap_auth'):
                    ldap_enable_line = line
                if port_line is not None and ldap_enable_line is not None:
                    break

            port = port_line.strip().split('=')[1]
            ldap_enable = 'false' if ldap_enable_line is None else ldap_enable_line.strip().split('=')[1]
        except Exception as e:
            Logger.error(str(e))
            raise Fail('parse cdh.impala.port({}) failed. '.format(ret))

        return {'server': ','.join(daemon_servers), 'port': port, 'ldap_enable': ldap_enable}

    def _get_cdh_kudu_info(self):
        service_name = 'kudu'
        ret = self._call_cm_api(self._cm_service_roles_url(service_name))
        try:
            master_items = [item for item in ret.get('items', []) if item.get('type', '') == 'KUDU_MASTER']
            master_servers = [self.cdh_hosts[item['hostRef']['hostId']]['ip'] for item in master_items]
            tablet_server_items = [item for item in ret.get('items', []) if item.get('type', '') == 'KUDU_TSERVER']
            tablet_server_servers = [self.cdh_hosts[item['hostRef']['hostId']]['ip'] for item in tablet_server_items]
            tablet_server_role_name = tablet_server_items[0]['name']
        except Exception as e:
            Logger.error(str(e))
            raise Fail('parse cdh.kudu.master(({}) failed. '.format(ret))

        ret = self._call_cm_api(self._cm_service_config_url(
            service_name, tablet_server_role_name, 'gflagfile'), rsp_type='text')
        try:
            web_server_port_line = None
            for line in ret.strip().split('\n'):
                if line.startswith('-webserver_port'):
                    web_server_port_line = line
                    break

            web_server_port = web_server_port_line.strip().split('=')[1]
        except Exception as e:
            Logger.error(str(e))
            raise Fail('parse cdh.impala.port({}) failed. '.format(ret))
        return {'master': ','.join(master_servers), 'master_port': '7051', 'tablet_server': ','.join(
            ['{}:{}'.format(server, web_server_port) for server in tablet_server_servers])}


try:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    STACKS_DIR = os.path.join(SCRIPT_DIR, '../../../../')
    PARENT_FILE = os.path.join(STACKS_DIR, 'service_advisor.py')
    if "BASE_SERVICE_ADVISOR" in os.environ:
        PARENT_FILE = os.environ["BASE_SERVICE_ADVISOR"]

    with open(PARENT_FILE, 'rb') as fp:
        service_advisor = imp.load_module('service_advisor', fp, PARENT_FILE, ('.py', 'rb', imp.PY_SOURCE))
except Exception as imp_e:
    traceback.print_exc()
    print("Failed to load parent")
    print(imp_e)


class XINSIGHT20COMMONServiceAdvisor(service_advisor.ServiceAdvisor):
    def __init__(self, *args, **kwargs):
        self.as_super = super(XINSIGHT20COMMONServiceAdvisor, self)
        self.as_super.__init__(*args, **kwargs)
        # Always call these methods
        Logger.info('!!!!!!init: args[{}], kwargs[{}]'.format(args, kwargs))

    """
    If any components of the service should be colocated with other services,
    this is where you should set up that layout.  Example:

    # colocate HAWQSEGMENT with DATANODE, if no hosts have been allocated for HAWQSEGMENT
    hawqSegment = [component for component in serviceComponents if component["StackServiceComponents"]["component_name"] == "HAWQSEGMENT"][0]
    if not self.isComponentHostsPopulated(hawqSegment):
      for hostName in hostsComponentsMap.keys():
        hostComponents = hostsComponentsMap[hostName]
        if {"name": "DATANODE"} in hostComponents and {"name": "HAWQSEGMENT"} not in hostComponents:
          hostsComponentsMap[hostName].append( { "name": "HAWQSEGMENT" } )
        if {"name": "DATANODE"} not in hostComponents and {"name": "HAWQSEGMENT"} in hostComponents:
          hostComponents.remove({"name": "HAWQSEGMENT"})
    """
    def colocateService(self, hostsComponentsMap, serviceComponents):
        Logger.info('!!!!!!colocateService........................')

    """
    Any configuration recommendations for the service should be defined in this function.
    This should be similar to any of the recommendXXXXConfigurations functions in the stack_advisor.py
    such as recommendYARNConfigurations().
    """
    def getServiceConfigurationRecommendations(self, configurations, clusterSummary, services, hosts):
        Logger.info('!!!!!!getServiceConfigurationRecommendations')
        common_cdh = self.getServicesSiteProperties(services, 'common-cdh')
        if common_cdh is not None:
            cluster_env = self.getServicesSiteProperties(services, "cluster-env")
            xsetup_ini_path = os.path.join(cluster_env['apps_path'], 'xsetup.ini')
            Logger.info('xsetup_ini_path[{}]'.format(xsetup_ini_path))
            # get xsetup.ini
            if os.path.exists(xsetup_ini_path) and os.path.isfile(xsetup_ini_path):
                with open(xsetup_ini_path, 'r') as f:
                    xsetup_ini = f.read()
                Logger.info('xsetup_ini: {}'.format(xsetup_ini))
                xsetup_conf_dict = properties2dict(xsetup_ini)
            else:
                xsetup_conf_dict = {}

            self.refresh_cdh_configurations(configurations, clusterSummary, services, hosts, xsetup_conf_dict)
            self.refresh_conf_configurations(configurations, clusterSummary, services, hosts, xsetup_conf_dict)
            self.refresh_env_configurations(configurations, clusterSummary, services, hosts)
            Logger.info('configurations[{}]'.format(configurations))

    """
    Returns an array of Validation objects about issues with the hostnames to which components are assigned.
    This should detect validation issues which are different than those the stack_advisor.py detects.
    The default validations are in stack_advisor.py getComponentLayoutValidations function.
    """
    def getServiceComponentLayoutValidations(self, services, hosts):
        Logger.info('!!!!!!getServiceComponentLayoutValidations')

        return []

    """
    Any configuration validations for the service should be defined in this function.
    This should be similar to any of the validateXXXXConfigurations functions in the stack_advisor.py
    such as validateHDFSConfigurations.
    """
    def getServiceConfigurationsValidationItems(self, configurations, recommendedDefaults, services, hosts):
        Logger.info('!!!!!!##########################getServiceConfigurationsValidationItems##########################')
        if 'common-cdh' in configurations:
            Logger.info('recommendedDefaults[{}]'.format(recommendedDefaults))
            items = []
            items.extend(self.validate_cdh_configurations(configurations, recommendedDefaults, services, hosts))
            items.extend(self.validate_conf_configurations(configurations, recommendedDefaults, services, hosts))
            items.extend(self.validate_env_configurations(configurations, recommendedDefaults, services, hosts))
            return items
        return []

    def refresh_cdh_configurations(self, configurations, clusterSummary, services, hosts, xsetup_conf_dict):
        try:
            ambari_hosts = [item['Hosts']['ip'] for item in hosts['items']]
            Logger.info('ambari_hosts[{}]'.format(ambari_hosts))
            cdh = Cdh(xsetup_conf_dict, ambari_hosts)
        except Exception as e:
            Logger.error(str(e))
            raise e

        # generate configurations
        putCommonCdhProperty = self.putProperty(configurations, 'common-cdh', services)
        cdh_env_dict = {
            'cm.host': cdh.cm_host, 'cm.port': cdh.cm_port,
            'cm.user': cdh.cm_user, 'cm.user.password': cdh.cm_user_password,
            'cdh.zookeeper.server': cdh.cdh_zookeeper_info['server'],
            'cdh.hdfs.default.fs': cdh.cdh_hdfs_info['default_fs'],
            'cdh.yarn.rm.webapp.address': cdh.cdh_yarn_info['rm_webapp_address'],
            'cdh.yarn.rm.webapp.https.address': cdh.cdh_yarn_info['rm_webapp_https_address'],
            'cdh.hbase.indexer': cdh.cdh_hbase_info['indexer'],
            'cdh.kafka.broker': cdh.cdh_kafka_info['broker'],
            'cdh.impala.daemon.server': cdh.cdh_impala_info['server'],
            'cdh.impala.daemon.hs2.port': cdh.cdh_impala_info['port'],
            'cdh.impala.ldap.enable': cdh.cdh_impala_info['ldap_enable'],
            'cdh.kudu.master': cdh.cdh_kudu_info['master'],
            'cdh.kudu.master.rpc.port': cdh.cdh_kudu_info['master_port'],
            'cdh.kudu.tablet.server': cdh.cdh_kudu_info['tablet_server'],
        }
        cdh_env_info = '\n'.join(['{}={}'.format(key, cdh_env_dict[key]) for key in sorted(cdh_env_dict.keys())])
        putCommonCdhProperty('cdh_env', cdh_env_info)

    def validate_cdh_configurations(self, configurations, recommendedDefaults, services, hosts):
        Logger.info('configurations[{}]'.format({'common-cdh': configurations.get('common-cdh', {})}))
        recommended_cdh_env = recommendedDefaults.get('common-cdh', {}).get('properties', {}).get('cdh_env', None)
        configurations_cdh_env = configurations.get('common-cdh', {}).get('properties', {}).get('cdh_env', None)

        validationItems = []
        if recommended_cdh_env is None:
            item = self.getErrorItem('must set the right value of in xsetup.ini: '
                                     'cm.host, cm.port, cm.user, cm.user.password, cm.user, cm.user.password')
            validationItems.extend([{'config-name': 'cdh_env', 'item': item}])
        elif configurations_cdh_env != recommended_cdh_env:
            recommended_cdh_env_dict = properties2dict(recommended_cdh_env)
            configurations_cdh_env_dict = {} if configurations_cdh_env is None else properties2dict(
                configurations_cdh_env)
            if recommended_cdh_env_dict != configurations_cdh_env_dict:
                item = self.getErrorItem('cdh_env must use the recommended value.')
                validationItems.extend([{'config-name': 'cdh_env', 'item': item}])
            else:
                Logger.warning('recommended_cdh_env is approximately equal to configurations_cdh_env')

        return self.toConfigurationValidationProblems(
            validationItems, "common-cdh") if len(validationItems) != 0 else []

    def refresh_conf_configurations(self, configurations, clusterSummary, services, hosts, xsetup_conf_dict):
        xinsight_env_dict = {
            'glusterfs.volume.directory': xsetup_conf_dict.get('glusterfs.volume.directory', ''),
            'glusterfs.share.mnt.point': xsetup_conf_dict.get('glusterfs.share.mnt.point', ''),
            'postgres.data.directory': xsetup_conf_dict.get('postgres.data.directory', ''),
            'postgres.write.vip': xsetup_conf_dict.get('postgres.write.vip', ''),
            'postgres.read.vip': xsetup_conf_dict.get('postgres.read.vip', ''),
            'redis.vip': xsetup_conf_dict.get('redis.vip', ''),
            'ha.proxy.vip': xsetup_conf_dict.get('ha.proxy.vip', ''),
        }
        # generate configurations
        putCommonConfProperty = self.putProperty(configurations, 'common-conf', services)
        xinsight_conf_info = '\n'.join(['{}={}'.format(key, xinsight_env_dict[key])
                                       for key in sorted(xinsight_env_dict.keys())])
        putCommonConfProperty('xinsight_conf', xinsight_conf_info)

    def validate_conf_configurations(self, configurations, recommendedDefaults, services, hosts):
        Logger.info('configurations[{}]'.format({'common-conf': configurations.get('common-conf', {})}))
        recommended_xinsight_conf = recommendedDefaults.get('common-conf', {}).get(
            'properties', {}).get('xinsight_conf', None)
        configurations_xinsight_conf = configurations.get('common-conf', {}).get(
            'properties', {}).get('xinsight_conf', None)

        validationItems = []
        if recommended_xinsight_conf is None or configurations_xinsight_conf is None:
            item = self.getErrorItem('must set XINSIGHT Configuration.')
            validationItems.extend([{'config-name': 'xinsight_conf', 'item': item}])
        else:
            recommended_xinsight_conf_dict = properties2dict(recommended_xinsight_conf)
            configurations_xinsight_conf_dict = properties2dict(configurations_xinsight_conf)
            xinsight_conf_dict = dict(recommended_xinsight_conf_dict)
            xinsight_conf_dict.update(configurations_xinsight_conf_dict)
            if '' in xinsight_conf_dict.values():
                item = self.getErrorItem('must set [{}] in XINSIGHT Configuration'.format(
                    ','.join(recommended_xinsight_conf_dict.keys())))
                validationItems.extend([{"config-name": "xinsight_conf", "item": item}])

        return self.toConfigurationValidationProblems(
            validationItems, "common-conf") if len(validationItems) != 0 else []

    def refresh_env_configurations(self, configurations, clusterSummary, services, hosts):
        # generate configurations
        putCommonEnvProperty = self.putProperty(configurations, "common-env", services)
        xinsight_env_dict = {
            'nginx.server': '',
            'ldap.enable': 'false',
            'redis.host': '',
            'redis.cluster.host': '',
        }
        # TODO: update
        xinsight_env_info = '\n'.join(['{}={}'.format(key, xinsight_env_dict[key])
                                       for key in sorted(xinsight_env_dict.keys())])
        putCommonEnvProperty('xinsight_env', xinsight_env_info)

    def validate_env_configurations(self, configurations, recommendedDefaults, services, hosts):
        Logger.info('configurations[{}]'.format({'common-env': configurations.get('common-env', {})}))
        recommended_xinsight_env = recommendedDefaults.get(
            'common-env', {}).get('properties', {}).get('xinsight_env', None)
        configurations_xinsight_env = configurations.get(
            'common-env', {}).get('properties', {}).get('xinsight_env', None)

        validationItems = []
        if recommended_xinsight_env is None:
            item = self.getErrorItem("some thing wrong happened when get xinsight_env.")
            validationItems.extend([{"config-name": "xinsight_env", "item": item}])
        elif configurations_xinsight_env != recommended_xinsight_env:
            recommended_xinsight_env_dict = properties2dict(recommended_xinsight_env)
            configurations_xinsight_env_dict = {} if configurations_xinsight_env is None else properties2dict(
                configurations_xinsight_env)
            if recommended_xinsight_env_dict != configurations_xinsight_env_dict:
                item = self.getErrorItem('xinsight_env must use the recommended value.')
                validationItems.extend([{'config-name': 'xinsight_env', 'item': item}])
            else:
                Logger.warning('recommended_xinsight_env is approximately equal to configurations_xinsight_env')

        return self.toConfigurationValidationProblems(
            validationItems, "common-env") if len(validationItems) != 0 else []


if __name__ == '__main__':
    import locale
    locale.setlocale(locale.LC_ALL, '')
    locale.getlocale(locale.LC_ALL)
    Logger.initialize_logger('test', logging_level='INFO')
    print(Cdh({}, ['168.2.6.171', '168.2.6.172']))
