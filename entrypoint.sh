#!/bin/sh

mkdir -p /service_data/mysql
chown -R mysql:mysql /service_data/mysql
chmod -R 755 /service_data/mysql
mysqld --initialize --datadir=/service_data/mysql
mysqld --init-file=/src/mysql-init.txt --datadir=/service_data/mysql &
sleep 2
python3 manage.py migrate
chown -R $USER_ID:$GROUP_ID /service_data/media
chmod -R 755 /service_data/media
exec gosu $USER_ID:$GROUP_ID "$@"