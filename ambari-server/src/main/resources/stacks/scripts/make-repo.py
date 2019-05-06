import paramiko
import socket
import sys
import subprocess


def exception_string(e):
    import traceback
    return '\n{}\n{}'.format(e, traceback.format_exc().decode('unicode-escape'))


def execute_shell_cmd(cmd, check_ret=True, encoding='utf-8'):
    p = subprocess.Popen(cmd, shell=True, universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.wait()
    ret = p.returncode
    _output = p.stdout.read().decode(encoding)
    _err_msg = p.stderr.read().decode(encoding)
    output = _output if ret == 0 or _err_msg == '' else _err_msg
    if ret != 0 and check_ret:
        raise RuntimeError('execute shell command[{}] failed: code[{}], msg[{}]'.format(cmd, ret, output))
    return ret, output


def get_ssh_client(ip, ssh_port, ssh_username, ssh_password, ssh_timeout=10):
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh_client.connect(ip, ssh_port, ssh_username, ssh_password, timeout=ssh_timeout)
    except socket.timeout as e:
        raise RuntimeError('ssh connect timeout, detail:\n{}'.format(exception_string(e)))
    except paramiko.ssh_exception.AuthenticationException as e:
        raise RuntimeError('ssh authentication failed, detail:\n{}'.format(exception_string(e)))
    except Exception as e:
        raise RuntimeError('ssh connect failed, detail:\n{}'.format(exception_string(e)))
    return ssh_client


def close_ssh_client(ssh_client):
    if ssh_client is not None:
        ssh_client.close()


def ssh_exec_cmd(ssh_client, cmd, ssh_timeout=120, check_ret=True, encoding='utf-8'):
    ret = ssh_client.exec_command(cmd, ssh_timeout)
    _ret_code = ret[1].channel.recv_exit_status()
    _output = ret[1].read()
    _err_msg = ret[2].read()
    ret_code = _ret_code
    output = _output if _ret_code == 0 or len(_err_msg) == 0 else _err_msg
    output = output.decode(encoding)
    if ret_code != 0 and check_ret:
        raise RuntimeError('execute [{}] failed. ret: [{}], error: [{}]'.format(cmd, ret_code, output))
    return ret_code, output


def get_sftp(ssh_client):
    return ssh_client.open_sftp()


def copy_file(src_file_path, dst_file_path):
    dst_sftp.put(src_file_path, dst_file_path)


def create_repo():
    repo_dir = '/'.join(dst_dir.split('/', -1)[0:-1]) if repo_in_parent else dst_dir
    print('start to create_repo in {}'.format(repo_dir))
    ssh_exec_cmd(dst_ssh_client, 'createrepo {}'.format(repo_dir))


def usage():
    print('{} <src_root_dir> <dst_info> [repo_in_parent]'.format(sys.argv[0]))
    sys.exit(-1)


if __name__ == '__main__':
    if len(sys.argv) not in (3, 4):
        usage()

    reload(sys)
    sys.setdefaultencoding('utf8')

    src_dir = sys.argv[1]
    dst_host, dst_port, dst_dir, dst_user, dst_password = sys.argv[2].split(':')
    if dst_dir[-1] == '/':
        dst_dir = dst_dir[0:-1]
    repo_in_parent = (sys.argv[3] == 'false') if len(sys.argv) == 4 else True

    dst_port = int(dst_port)
    _, target_files_output = execute_shell_cmd(
        'find {} -name \'ambari-server*.x86_64.rpm\' -o -name \'ambari-agent*.x86_64.rpm\''
        ' -o -name \'ambari-metric*.x86_64.rpm\''.format(src_dir))
    src_rpm_files = target_files_output.strip().split('\n')

    dst_ssh_client = None
    try:
        dst_ssh_client = get_ssh_client(dst_host, dst_port, dst_user, dst_password)
        dst_sftp = get_sftp(dst_ssh_client)

        for src_file in src_rpm_files:
            src_file_name = src_file.split('/')[-1]
            dst_file = '{}/{}'.format(dst_dir, src_file_name)
            print('start to copy {} to {}:{}'.format(src_file, dst_host, dst_file))
            copy_file(src_file, dst_file)

        create_repo()
    finally:
        close_ssh_client(dst_ssh_client)
