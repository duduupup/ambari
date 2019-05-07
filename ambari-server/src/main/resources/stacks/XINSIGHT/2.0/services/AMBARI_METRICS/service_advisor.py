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


class XINSIGHT20AMBARIMETRICSServiceAdvisor(service_advisor.ServiceAdvisor):
    def __init__(self, *args, **kwargs):
        self.as_super = super(XINSIGHT20AMBARIMETRICSServiceAdvisor, self)
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
        Logger.info('!!!!!!AMBARI_METRICS colocateService........................')

    """
    Any configuration recommendations for the service should be defined in this function.
    This should be similar to any of the recommendXXXXConfigurations functions in the stack_advisor.py
    such as recommendYARNConfigurations().
    """
    def getServiceConfigurationRecommendations(self, configurations, clusterSummary, services, hosts):
        Logger.info('##########AMBARI_METRICS getServiceConfigurationRecommendations')
        ams_env = self.getServicesSiteProperties(services, 'ams-env')
        if ams_env is not None:
            self.refresh_ams_site_configurations(configurations, clusterSummary, services, hosts)
            Logger.info('configurations[{}]'.format(configurations))

    """
    Returns an array of Validation objects about issues with the hostnames to which components are assigned.
    This should detect validation issues which are different than those the stack_advisor.py detects.
    The default validations are in stack_advisor.py getComponentLayoutValidations function.
    """
    def getServiceComponentLayoutValidations(self, services, hosts):
        Logger.info('!!!!!!AMBARI_METRICS getServiceComponentLayoutValidations')

        return []

    """
    Any configuration validations for the service should be defined in this function.
    This should be similar to any of the validateXXXXConfigurations functions in the stack_advisor.py
    such as validateHDFSConfigurations.
    """
    def getServiceConfigurationsValidationItems(self, configurations, recommendedDefaults, services, hosts):
        Logger.info('##########AMBARI_METRICS getServiceConfigurationsValidationItems')
        if 'ams-env' in configurations:
            items = []
            items.extend(self.validate_ams_site_configurations(configurations, recommendedDefaults, services, hosts))
            return items
        return []

    def refresh_ams_site_configurations(self, configurations, clusterSummary, services, hosts):
        # generate configurations
        cdh_zk_server = None
        common_cdh = self.getServicesSiteProperties(services, 'common-cdh')
        if common_cdh is not None:
            cdh_env = common_cdh.get('cdh_env', None)
            cdh_zk_server = properties2dict(cdh_env).get('cdh.zookeeper.server', None) if cdh_env is not None else None
        if cdh_zk_server is None:
            cdh_env = configurations.get('common-cdh', {}).get('properties', {}).get('cdh_env', None)
            cdh_zk_server = properties2dict(cdh_env).get('cdh.zookeeper.server', None) if cdh_env is not None else None
        Logger.info('cdh_zk_server[{}]'.format(cdh_zk_server))
        if cdh_zk_server is not None:
            cluster_zk_quorum = ','.join([server.split(':')[0] for server in cdh_zk_server.split(',')])
            cluster_zk_client_port = cdh_zk_server.split(',')[0].split(':')[1]
            putAmsSiteProperty = self.putProperty(configurations, 'ams-site', services)
            putAmsSiteProperty('cluster.zookeeper.quorum', cluster_zk_quorum)
            putAmsSiteProperty('cluster.zookeeper.property.clientPort', cluster_zk_client_port)

    def validate_ams_site_configurations(self, configurations, recommendedDefaults, services, hosts):
        Logger.info('recommendedDefaults[{}]'.format(recommendedDefaults))
        recommended_ams_site = recommendedDefaults.get('ams-site', {}).get('properties', {})
        configurations_ams_site = configurations.get('ams-site', {}).get('properties', {})
        validationItems = []
        if 'cluster.zookeeper.quorum' in recommended_ams_site:
            if (recommended_ams_site.get('cluster.zookeeper.quorum', None)
                    != configurations_ams_site['cluster.zookeeper.quorum']):
                item = self.getErrorItem('must use recommended cluster.zookeeper.quorum')
                validationItems.extend([{'config-name': 'cluster.zookeeper.quorum', 'item': item}])

            if (recommended_ams_site.get('cluster.zookeeper.property.clientPort', None)
                    != configurations_ams_site['cluster.zookeeper.property.clientPort']):
                item = self.getErrorItem('must use recommended cluster.zookeeper.property.clientPort')
                validationItems.extend([{'config-name': 'cluster.zookeeper.property.clientPort', 'item': item}])

        return self.toConfigurationValidationProblems(
            validationItems, "ams-site") if len(validationItems) != 0 else []
