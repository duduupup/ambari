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
from ambari_commons.config_utils import properties2dict
from resource_management.core.logger import Logger
import ambari_simplejson as json

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


class XINSIGHT20NGINXServiceAdvisor(service_advisor.ServiceAdvisor):
    def __init__(self, *args, **kwargs):
        self.as_super = super(XINSIGHT20NGINXServiceAdvisor, self)
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
        Logger.info('!!!!!!NGINX colocateService........................')

    """
    Any configuration recommendations for the service should be defined in this function.
    This should be similar to any of the recommendXXXXConfigurations functions in the stack_advisor.py
    such as recommendYARNConfigurations().
    """
    def getServiceConfigurationRecommendations(self, configurations, clusterSummary, services, hosts):
        Logger.info('##########NGINX getServiceConfigurationRecommendations')
        nginx_env = self.getServicesSiteProperties(services, 'nginx-env')
        if nginx_env is not None:
            self.refresh_nginx_env_configurations(configurations, clusterSummary, services, hosts)
            Logger.info('configurations[{}]'.format(configurations))

    """
    Returns an array of Validation objects about issues with the hostnames to which components are assigned.
    This should detect validation issues which are different than those the stack_advisor.py detects.
    The default validations are in stack_advisor.py getComponentLayoutValidations function.
    """
    def getServiceComponentLayoutValidations(self, services, hosts):
        Logger.info('!!!!!!NGINX getServiceComponentLayoutValidations')

        return []

    """
    Any configuration validations for the service should be defined in this function.
    This should be similar to any of the validateXXXXConfigurations functions in the stack_advisor.py
    such as validateHDFSConfigurations.
    """
    def getServiceConfigurationsValidationItems(self, configurations, recommendedDefaults, services, hosts):
        Logger.info('##########NGINX getServiceConfigurationsValidationItems')
        if 'nginx-env' in configurations:
            items = []
            items.extend(self.validate_nginx_env_configurations(configurations, recommendedDefaults, services, hosts))
            return items
        return []

    def refresh_nginx_env_configurations(self, configurations, clusterSummary, services, hosts):
        # generate configurations
        services_component_dict = self.get_service_component_dict(services, hosts)
        Logger.info('##########services_component_dict[{}]'.format(json.dumps(services_component_dict)))
        nginx_env_dict = {}
        if 'AAS' in services_component_dict:
            servers = services_component_dict['AAS']['AAS_SERVER']
            port = self.getServicesSiteProperties(services, 'aas-conf')['aas_port']
            nginx_env_dict.update({'aas': {
                'url': ['aas', 'aas_web', 'ccs', 'ccs_web'],
                'servers': ['{}:{}'.format(server, port) for server in servers]
            }})

        if 'LICENSE' in services_component_dict:
            servers = services_component_dict['LICENSE']['LICENSE_SERVER']
            port = self.getServicesSiteProperties(services, 'license-conf')['license_port']
            nginx_env_dict.update({'license': {
                'url': ['license'],
                'servers': ['{}:{}'.format(server, port) for server in servers]
            }})

        if 'XINSIGHTCLOUD' in services_component_dict:
            servers = services_component_dict['XINSIGHTCLOUD']['XINSIGHTCLOUD_SERVER']
            port = self.getServicesSiteProperties(services, 'xinsightcloud-conf')['xinsightcloud_port']
            nginx_env_dict.update({'xinsightcloud': {
                'url': ['xinsightcloud'],
                'servers': ['{}:{}'.format(server, port) for server in servers]
            }})

        if 'CVS' in services_component_dict:
            servers = services_component_dict['CVS']['CVS_SERVER']
            port = self.getServicesSiteProperties(services, 'cvs-conf')['cvs_port']
            nginx_env_dict.update({'cvs': {
                'url': ['cvscfgsvr'],
                'servers': ['{}:{}'.format(server, port) for server in servers]
            }})

        if 'RDS' in services_component_dict:
            servers = services_component_dict['RDS']['RDS_SERVER']
            port = self.getServicesSiteProperties(services, 'rds-conf')['rds_port']
            nginx_env_dict.update({'rds': {
                'url': ['rds'],
                'servers': ['{}:{}'.format(server, port) for server in servers]
            }})

        if 'OTS' in services_component_dict:
            servers = services_component_dict['OTS']['OTS_SERVER']
            port = self.getServicesSiteProperties(services, 'ots-conf')['ots_port']
            nginx_env_dict.update({'ots': {
                'url': ['otscfgsvr', 'otsrest'],
                'servers': ['{}:{}'.format(server, port) for server in servers]
            }})

        if 'PDS' in services_component_dict:
            servers = services_component_dict['PDS']['PDS_SERVER']
            port = self.getServicesSiteProperties(services, 'pds-conf')['pds_port']
            nginx_env_dict.update({'pds': {
                'url': ['pdscfgsvr', 'pdsrest'],
                'servers': ['{}:{}'.format(server, port) for server in servers]
            }})

        if 'TSDB' in services_component_dict:
            servers = services_component_dict['TSDB']['TSDB_SERVER']
            port = self.getServicesSiteProperties(services, 'tsdb-conf')['tsdb_port']
            nginx_env_dict.update({'tsdb': {
                'url': ['tsdbcfgsvr', 'tsdbrest'],
                'servers': ['{}:{}'.format(server, port) for server in servers]
            }})

        if 'STS' in services_component_dict:
            servers = services_component_dict['STS']['STS_SERVER']
            port = self.getServicesSiteProperties(services, 'sts-conf')['sts_port']
            nginx_env_dict.update({'sts': {
                'url': ['stscfgsvr', 'stsrest'],
                'servers': ['{}:{}'.format(server, port) for server in servers]
            }})

        if 'OSS' in services_component_dict:
            servers = services_component_dict['OSS']['OSS_SERVER']
            port = self.getServicesSiteProperties(services, 'oss-conf')['oss_port']
            nginx_env_dict.update({'oss': {
                'url': ['osscfgsvr', 'ossrest'],
                'servers': ['{}:{}'.format(server, port) for server in servers]
            }})

        if 'TSS' in services_component_dict:
            servers = services_component_dict['TSS']['TSS_SERVER']
            port = self.getServicesSiteProperties(services, 'tss-conf')['tss_port']
            nginx_env_dict.update({'tss': {
                'url': ['tsscfgsvr', 'tssrest'],
                'servers': ['{}:{}'.format(server, port) for server in servers]
            }})

        if 'RGS' in services_component_dict:
            servers = services_component_dict['RGS']['RGS_SERVER']
            port = self.getServicesSiteProperties(services, 'rgs-conf')['rgs_port']
            nginx_env_dict.update({'rgs': {
                'url': ['rgscfgsvr', 'rgsrest'],
                'servers': ['{}:{}'.format(server, port) for server in servers]
            }})

        if 'SMS' in services_component_dict:
            servers = services_component_dict['SMS']['SMS_SERVER']
            port = self.getServicesSiteProperties(services, 'sms-conf')['sms_port']
            nginx_env_dict.update({'sms': {
                'url': ['smscfgsvr'],
                'servers': ['{}:{}'.format(server, port) for server in servers]
            }})

        if 'DTS' in services_component_dict:
            servers = services_component_dict['DTS']['DTS_SERVER']
            port = self.getServicesSiteProperties(services, 'dts-conf')['dts_port']
            nginx_env_dict.update({'dts': {
                'url': ['dtscfgsvr'],
                'servers': ['{}:{}'.format(server, port) for server in servers]
            }})

        if 'DMS' in services_component_dict:
            servers = services_component_dict['DMS']['DMS_SERVER']
            port = self.getServicesSiteProperties(services, 'sts-conf')['sts_port']
            nginx_env_dict.update({'dms': {
                'url': ['dmscfgsvr'],
                'servers': ['{}:{}'.format(server, port) for server in servers]
            }})

        if 'FCS' in services_component_dict:
            servers = services_component_dict['FCS']['FCS_SERVER']
            port = self.getServicesSiteProperties(services, 'fcs-conf')['fcs_port']
            nginx_env_dict.update({'fcs': {
                'url': ['fcscfgsvr'],
                'servers': ['{}:{}'.format(server, port) for server in servers]
            }})

        nginx_env_content = '\n'.join(['{}:{}'.format(key, json.dumps(value)) for key, value in nginx_env_dict.items()])
        putNginxEnvProperty = self.putProperty(configurations, 'nginx-env', services)
        putNginxEnvProperty('nginx_env', nginx_env_content)

    def validate_nginx_env_configurations(self, configurations, recommendedDefaults, services, hosts):
        Logger.info('recommendedDefaults[{}]'.format(recommendedDefaults))
        recommended_nginx_env = recommendedDefaults.get('nginx-env', {}).get('properties', {})
        configurations_nginx_env = configurations.get('nginx-env', {}).get('properties', {})
        validationItems = []
        if 'nginx-env' in recommended_nginx_env:
            if recommended_nginx_env.get('nginx_env', None) != configurations_nginx_env['nginx_env']:
                item = self.getErrorItem('must use recommended nginx.env')
                validationItems.extend([{'config-name': 'nginx.env', 'item': item}])

        return self.toConfigurationValidationProblems(
            validationItems, "ams-site") if len(validationItems) != 0 else []
