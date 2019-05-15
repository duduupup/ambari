from ambari_commons.config_utils import properties2dict
from resource_management import check_process_status, Fail, format, Execute, File, Logger
import ambari_simplejson as json


def nginx_configure():
    import params
    web_services = {key: json.loads(value) for key, value in properties2dict(params.nginx_env['nginx_env']).items()}
    for key, value in params.nginx_env.items():
        if key != 'nginx_env':
            try:
                web_services[key] = json.loads(value)
            except Exception as e:
                Logger.warning("wrong custom nginx-env: {}={}, skip it".format(key, value))
                Logger.warning(str(e))
    cloud_conf_content = _nginx_cloud_conf_content(web_services, params.nginx_home_dir,
                                                   params.nginx_conf_dir, params.nginx_port)
    cluster_conf_content = _nginx_cluster_conf_content(web_services)
    File(format("{nginx_conf_dir}/cloud.conf"), content=cloud_conf_content, mode=0644,
         owner=params.nginx_user, group=params.nginx_group)
    File(format("{nginx_conf_dir}/cluster.conf"), content=cluster_conf_content, mode=0644,
         owner=params.nginx_user, group=params.nginx_group)


def nginx_start():
    import params
    Execute(params.nginx_start_cmd, user='root', logoutput=True)


def nginx_stop():
    import params
    Execute(params.nginx_stop_cmd, user='root', logoutput=True)


def nginx_status():
    import params
    check_process_status(params.nginx_pid_file)


def _nginx_cloud_conf_content(web_services, nginx_home_dir, nginx_conf_dir, nginx_port):
    service_cloud_content = '\n'.join([
        _nginx_generate_cloud_item(service_name, service_info.get('url', []))
        for service_name, service_info in web_services.items()])
    return '''include {nginx_conf_dir}/cluster.conf;
server {{
    listen       {nginx_port};
    server_name  localhost;

    #charset koi8-r;
    #access_log  {nginx_home_dir}/logs/access.log  main;

    location / {{
        root   {nginx_home_dir}/html;
        index  index.html index.htm;
    }}

    # redirect server error pages to the static page /50x.html
    error_page   500 502 503 504  /50x.html;
    location = /50x.html {{
        root   {nginx_home_dir}/html;
    }}
    
{service_cloud_content}
}}
'''.format(nginx_conf_dir=nginx_conf_dir, nginx_home_dir=nginx_home_dir,
           nginx_port=nginx_port, service_cloud_content=service_cloud_content)


def _nginx_cluster_conf_content(web_services):
    return '\n'.join([_nginx_generate_cluster_item(service_name, service_info.get('servers', []))
                      for service_name, service_info in web_services.items()])


def _nginx_generate_cloud_item(name, urls):
    return ''.join(['''    location /{url}/ {{
        proxy_pass http://{name}_IP;
        proxy_redirect http://{name}_IP/{url}/ /{url}/;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header Host $http_host;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
    }}
'''.format(url=url, name=name) for url in urls])


def _nginx_generate_cluster_item(name, server_list):
    return 'upstream {}_IP {{\n    ip_hash;\n    server {};\n}}\n'.format(name, ';\n    server '.join(server_list))


if __name__ == '__main__':
    print(_nginx_cloud_conf_content({}, '/apps/nginx', '/apps/nginx-conf', '80'))
    print(_nginx_cluster_conf_content({}))
    services = {
        'oss': {'url': ['osscfgsvr', 'ossrest'], 'servers': ['xinsight8.cloud:18094', 'xinsight9.cloud:18094']},
        'ots': {'url': ['otscfgsvr'], 'servers': ['xinsight8.cloud:18094']},
    }
    print(_nginx_cloud_conf_content(services, '/apps/nginx', '/apps/nginx-conf', '80'))
    print(_nginx_cluster_conf_content(services))
