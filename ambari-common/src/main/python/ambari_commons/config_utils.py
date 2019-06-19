import ConfigParser
import StringIO
import os
from xml.etree import ElementTree

MyConfigParser = type('MyConfigParser', (ConfigParser.RawConfigParser, object), {'optionxform': lambda self, x: x})


def config_file_content(config_file):
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            return f.read().strip()
    else:
        return ''


def properties2dict(config_content):
    config_parser = MyConfigParser()
    config_parser.readfp(StringIO.StringIO('[dummy]\n' + config_content))
    return {key: value for key, value in config_parser.items('dummy')}


def xml2dict(config_content):
    property_nodes = ElementTree.fromstring(config_content).findall('property')
    return {property_node.findall('name')[0].text.strip(): property_node.findall('value')[0].text.strip()
            for property_node in property_nodes}
