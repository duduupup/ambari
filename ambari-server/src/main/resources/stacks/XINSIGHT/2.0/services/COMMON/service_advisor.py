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
import ConfigParser
import StringIO
from xml.etree import ElementTree
import ambari_simplejson as json
from resource_management import Fail
from resource_management.core.logger import Logger
import ambari_commons.network as network


class Cdh(object):
    MyConfigParser = type('MyConfigParser', (ConfigParser.RawConfigParser, object), {'optionxform': lambda self, x: x})

    @staticmethod
    def parse_xinsight_ini(xinsight_ini, ambari_hosts):
        xinsight_config = Cdh._parse_data(xinsight_ini, 'properties')
        cm_host = xinsight_config.get('cm_host', '')
        cm_port = int(xinsight_config.get('cm_port', '7180'))
        cm_admin = xinsight_config.get('cm_admin', 'admin')
        cm_admin_password = xinsight_config.get('cm_admin_password', 'admin')
        cm_user = xinsight_config.get('cm_user', 'view')
        cm_user_password = xinsight_config.get('cm_user_password', 'view')
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
                print(exceptions[0])
                raise Fail('parse cm.hosts({}) failed.'.format(ambari_hosts))
        return cm_host, cm_port, cm_admin, cm_admin_password, cm_user, cm_user_password

    @staticmethod
    def _parse_data(data_content, data_type):
        if data_type == 'text':
            return data_content
        elif data_type == 'json':
            return json.loads(data_content)
        elif data_type == 'properties':
            config_parser = Cdh.MyConfigParser()
            config_parser.readfp(StringIO.StringIO('[dummy]\n' + data_content))
            return {key: value for key, value in config_parser.items('dummy')}
        elif data_type == 'xml':
            property_nodes = ElementTree.fromstring(data_content).findall('property')
            return {property_node.findall('name')[0].text.strip(): property_node.findall('value')[0].text.strip()
                    for property_node in property_nodes}
        else:
            raise KeyError('unknown rsp_type[{}]'.format(data_type))

    def __init__(self, xinsight_ini, ambari_hosts):
        self.cm_host, self.cm_port, self.cm_admin, self.cm_admin_password, self.cm_user, self.cm_user_password = \
            Cdh.parse_xinsight_ini(xinsight_ini, ambari_hosts)
        self.cdh_hosts = self._get_cdh_hosts()
        self.cdh_cluster_name = self._get_cdh_cluster_name()
        self.cdh_zookeeper_info = self._get_cdh_zookeeper_info()
        self.cdh_hdfs_info = self._get_cdh_hdfs_info()
        self.cdh_yarn_info = self._get_cdh_yarn_info()
        self.cdh_impala_info = self._get_cdh_impala_info()
        self.chd_kudu_info = self._get_cdh_kudu_info()

    def __str__(self):
        return 'CDH[\ncluster_name={}\nhosts={}\ncm={}\nzookeeper={}\nhdfs={}\nyarn={}\nimpala={}\nkudu={}\n]'.format(
            self.cdh_cluster_name, [host['ip'] for host in self.cdh_hosts.values()], {
                'cm': '{}:{}'.format(self.cm_host, self.cm_port),
                'admin': '{}:{}'.format(self.cm_admin, self.cm_admin_password),
                'user': '{}:{}'.format(self.cm_user, self.cm_user_password)
            }, self.cdh_zookeeper_info, self.cdh_hdfs_info, self.cdh_yarn_info,
            self.cdh_impala_info, self.chd_kudu_info)

    __repr__ = __str__

    def get_cdh_nodes(self):
        return ' '.join([host['ip'] for host in self.cdh_hosts.values()])

    def _get_cdh_hosts(self):
        ret = self._call_cm_api('/api/v6/hosts')
        try:
            return {host['hostId']: {'ip': host['ipAddress'], 'hostname': host['hostname']}
                    for host in ret.get('items', []) if 'hostId' in host}
        except Exception as e:
            print(e)
            raise Fail('parse cdh.hosts({}) failed. '.format(ret))

    def _get_cdh_cluster_name(self):
        ret = self._call_cm_api('/api/v6/clusters')
        try:
            return ret.get('items', [])[0]['displayName']
        except Exception as e:
            print(e)
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
            print(e)
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
                    print(e)
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
            print(e)
            raise Fail('parse cdh.zookeeper.servers({}) failed. '.format(ret))

        ret = self._call_cm_api(self._cm_service_config_url(
            service_name, server_role_name, 'zoo.cfg'), rsp_type='properties')
        try:
            client_port = ret['clientPort']
        except Exception as e:
            print(e)
            raise Fail('parse cdh.zookeeper.clientPort({}) failed. '.format(ret))

        return {'servers': servers, 'client_port': client_port}

    def _get_cdh_hdfs_info(self):
        service_name = 'hdfs'
        ret = self._call_cm_api(self._cm_service_roles_url(service_name))
        try:
            nn_items = [item for item in ret.get('items', []) if item.get('type', '') == 'NAMENODE']
            nn_role_name = nn_items[0]['name']
        except Exception as e:
            print(e)
            raise Fail('parse cdh.hdfs.namenode({}) failed. '.format(ret))

        ret = self._call_cm_api(self._cm_service_config_url(
            service_name, nn_role_name, 'core-site.xml'), rsp_type='xml')
        try:
            default_fs = self._url_hostname_to_ip(ret['fs.defaultFS'])
        except Exception as e:
            print(e)
            raise Fail('parse cdh.hdfs.defaultFS({}) failed. '.format(ret))

        return {'default_fs': default_fs}

    def _get_cdh_yarn_info(self):
        service_name = 'yarn'
        ret = self._call_cm_api(self._cm_service_roles_url(service_name))
        try:
            rm_items = [item for item in ret.get('items', []) if item.get('type', '') == 'RESOURCEMANAGER']
            rm_role_name = rm_items[0]['name']
        except Exception as e:
            print(e)
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
            print(e)
            raise Fail('parse cdh.yarn.resourcemanager.webapp.address({}) failed. '.format(ret))

        return {'rm_webapp_address': rm_webapp_address, 'rm_webapp_https_address': rm_webapp_https_address}

    def _get_cdh_impala_info(self):
        service_name = 'impala'
        ret = self._call_cm_api(self._cm_service_roles_url(service_name))
        try:
            daemon_items = [item for item in ret.get('items', []) if item.get('type', '') == 'IMPALAD']
            daemon_servers = [self.cdh_hosts[item['hostRef']['hostId']]['ip'] for item in daemon_items]
            daemon_role_name = daemon_items[0]['name']
        except Exception as e:
            print(e)
            raise Fail('parse cdh.impala.daemon(({}) failed. '.format(ret))

        ret = self._call_cm_api(self._cm_service_config_url(
            service_name, daemon_role_name, 'impala-conf/impalad_flags'), rsp_type='text')
        try:
            port_line = None
            for line in ret.strip().split('\n'):
                if line.startswith('-hs2_port'):
                    port_line = line

            port = port_line.strip().split('=')[1]
        except Exception as e:
            print(e)
            raise Fail('parse cdh.impala.port({}) failed. '.format(ret))

        return {'server': daemon_servers, 'port': port}

    def _get_cdh_kudu_info(self):
        service_name = 'kudu'
        ret = self._call_cm_api(self._cm_service_roles_url(service_name))
        try:
            master_items = [item for item in ret.get('items', []) if item.get('type', '') == 'KUDU_MASTER']
            master_servers = [self.cdh_hosts[item['hostRef']['hostId']]['ip'] for item in master_items]
        except Exception as e:
            print(e)
            raise Fail('parse cdh.kudu.master(({}) failed. '.format(ret))

        return {'master': master_servers, 'port': '7051'}


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
        Logger.info('!!!!!!args: ')
        Logger.info(args)
        Logger.info('!!!!!!args: ')
        Logger.info(kwargs)

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
        Logger.info('!!!!!!hostsComponentsMap: ' + hostsComponentsMap)
        Logger.info('!!!!!!hostsComponentsMap: ' + serviceComponents)

    """
    Any configuration recommendations for the service should be defined in this function.
    This should be similar to any of the recommendXXXXConfigurations functions in the stack_advisor.py
    such as recommendYARNConfigurations().
    """
    def getServiceConfigurationRecommendations(self, configurations, clusterSummary, services, hosts):
        Logger.info('!!!!!!configurations: ' + configurations)
        Logger.info('!!!!!!clusterSummary: ' + clusterSummary)
        Logger.info('!!!!!!services: ' + services)
        Logger.info('!!!!!!hosts: ' + hosts)

    """
    Returns an array of Validation objects about issues with the hostnames to which components are assigned.
    This should detect validation issues which are different than those the stack_advisor.py detects.
    The default validations are in stack_advisor.py getComponentLayoutValidations function.
    """
    def getServiceComponentLayoutValidations(self, services, hosts):
        Logger.info('!!!!!!services: ' + services)
        Logger.info('!!!!!!hosts: ' + hosts)
        return []

    """
    Any configuration validations for the service should be defined in this function.
    This should be similar to any of the validateXXXXConfigurations functions in the stack_advisor.py
    such as validateHDFSConfigurations.
    """
    def getServiceConfigurationsValidationItems(self, configurations, recommendedDefaults, services, hosts):
        Logger.info('!!!!!!configurations: ' + configurations)
        Logger.info('!!!!!!recommendedDefaults: ' + recommendedDefaults)
        Logger.info('!!!!!!services: ' + services)
        Logger.info('!!!!!!hosts: ' + hosts)
        return []


if __name__ == '__main__':
    print(Cdh('', ['168.2.6.171', '168.2.6.172']))
