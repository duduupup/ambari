#!/bin/bash
set -e errexit

# env variable
basepath=$(cd `dirname $0`; pwd)
source $basepath/../openldap.conf

# ldap dir
mkdir -p /var/lib/ldap

cp /usr/share/openldap-servers/DB_CONFIG.example /var/lib/ldap/DB_CONFIG
chown ldap. /var/lib/ldap/DB_CONFIG

systemctl restart slapd
systemctl enable slapd

ldap_secret_ciphertext=`slappasswd -s $LDAP_ROOT_PASS`

# temp dir
mkdir -p $basepath/../temp

# chrootpw
cp $basepath/../templates/chrootpw.ldif.template $basepath/../temp/chrootpw.ldif
sed -i "s|^olcRootPW.*|olcRootPW: $ldap_secret_ciphertext|g" $basepath/../temp/chrootpw.ldif
ldapadd -Y EXTERNAL -H ldapi:/// -f $basepath/../temp/chrootpw.ldif

# import schemas
ldapadd -Y EXTERNAL -H ldapi:/// -f /etc/openldap/schema/cosine.ldif
ldapadd -Y EXTERNAL -H ldapi:/// -f /etc/openldap/schema/nis.ldif
ldapadd -Y EXTERNAL -H ldapi:/// -f /etc/openldap/schema/inetorgperson.ldif

# chdomain
cp $basepath/../templates/chdomain.ldif.template $basepath/../temp/chdomain.ldif
sed -i "s|^olcRootPW.*|olcRootPW: $ldap_secret_ciphertext|g" $basepath/../temp/chdomain.ldif
sed -i -e "s/xinsight/$LDAP_DOMAIN_NAME/g" -e "s/com/$LDAP_DOMAIN_SUFFIX/g" $basepath/../temp/chdomain.ldif
ldapmodify -Y EXTERNAL -H ldapi:/// -f $basepath/../temp/chdomain.ldif

# init basedomain
cp $basepath/../templates/basedomain.ldif.template $basepath/../temp/basedomain.ldif
sed -i "s|^UserPassword.*|UserPassword: $ldap_secret_ciphertext|g" $basepath/../temp/basedomain.ldif
sed -i -e "s/xinsight/$LDAP_DOMAIN_NAME/g" -e "s/com/$LDAP_DOMAIN_SUFFIX/g" $basepath/../temp/basedomain.ldif
ldapadd -x -D cn=Manager,dc=$LDAP_DOMAIN_NAME,dc=$LDAP_DOMAIN_SUFFIX -f $basepath/../temp/basedomain.ldif -w $LDAP_ROOT_PASS

# clear temp file
rm -rf $basepath/../temp/*

firewall-cmd --add-service=ldap --permanent || true
firewall-cmd --reload || true

