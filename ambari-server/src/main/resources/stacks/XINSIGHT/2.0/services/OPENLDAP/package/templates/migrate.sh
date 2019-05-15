#!/bin/bash
set -e errexit

# env variable
basepath=$(cd `dirname $0`; pwd)
source $basepath/../openldap.conf
migration_tool_path=/usr/share/migrationtools
user_info_file=$basepath/../temp/user_info.ldif
group_info_file=$basepath/../temp/group_info.ldif

# modify migration common
sed -i "s/^\$DEFAULT_MAIL_DOMAIN = .*/\$DEFAULT_MAIL_DOMAIN = \"$LDAP_DOMAIN_NAME.$LDAP_DOMAIN_SUFFIX\";/g" $migration_tool_path/migrate_common.ph
sed -i "s/^\$DEFAULT_BASE = .*/\$DEFAULT_BASE = \"dc=$LDAP_DOMAIN_NAME,dc=$LDAP_DOMAIN_SUFFIX\";/g" $migration_tool_path/migrate_common.ph

# export user and group info
$migration_tool_path/migrate_passwd.pl /etc/passwd $user_info_file
$migration_tool_path/migrate_group.pl /etc/group $group_info_file

# transform for sentry
python $basepath/transform.py $user_info_file $group_info_file

# ldapadd
ldapadd -x -c -w $LDAP_ROOT_PASS -D "cn=Manager,dc=$LDAP_DOMAIN_NAME,dc=$LDAP_DOMAIN_SUFFIX" -f $group_info_file
ldapadd -x -c -w $LDAP_ROOT_PASS -D "cn=Manager,dc=$LDAP_DOMAIN_NAME,dc=$LDAP_DOMAIN_SUFFIX" -f $user_info_file
