#!/bin/sh

mkdir -p /service_data/mysql
chown -R mysql:mysql /service_data/mysql
chmod -R 755 /service_data/mysql
mysqld --initialize --datadir=/service_data/mysql
mysqld --init-file=/src/mysql-init.txt --datadir=/service_data/mysql &
sleep 2
python3 manage.py migrate


exec "$@"