#!/bin/sh

mkdir /data/mysql
chown -R mysql:mysql /data/mysql
chmod -R 755 /data/mysql
mysqld --initialize --datadir=/data/mysql
mysqld --init-file=/src/mysql-init.txt --datadir=/data/mysql &
python manage.py migrate


exec "$@"