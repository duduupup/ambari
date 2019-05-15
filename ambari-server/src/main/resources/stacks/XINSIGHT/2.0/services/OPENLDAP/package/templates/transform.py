# -*- coding: utf-8 -*-
import sys
import hashlib
import base64

def ldap_password():
    algorithm = 'MD5'
    password = 'q1w2e3'

    md5 = hashlib.new(algorithm)
    md5.update(password.encode('utf-8'))
    secret = str(base64.b64encode(md5.digest()), 'utf-8')
    return '{{{}}}{}'.format(algorithm, secret)


if len(sys.argv) != 3:
    sys.exit(1)

user_info = sys.argv[1]
group_info = sys.argv[2]

with open(user_info, 'r') as user_info_file:
    change_map = {}
    for line in user_info_file:
        if line.startswith('uid: '):
            user_name = line.split(": ")[-1][:-1]
        if line.startswith('uidNumber: '):
            user_id = line.split(": ")[-1][:-1]
            change_map[user_name] = user_id

with open(group_info, 'r+') as group_info_file:
    content = group_info_file.readlines()
    group_info_file.seek(0)
    group_info_file.truncate()
    for line in content:
        if 'memberUid: ' in line:
            user_name = line.split(': ')[-1][:-1]
            line = line.replace(user_name, change_map[user_name])
        group_info_file.write(line)
