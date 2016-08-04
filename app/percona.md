Set up a Percona XtraDB multi-master cluster
=========================
### Summary

[TOC]

### Architecture
Function | Hostname | IP address
-------- | -------- | --------
Percona XtraDB master| node1 |10.98.0.173
Percona XtraDB master   | node2   |10.98.0.174
Arbitrator     | node3|10.98.0.171



### Install on node1 and node2
```bash
# add new Percona repository
yum install http://www.percona.com/downloads/percona-release/redhat/0.1-3/percona-release-0.1-3.noarch.rpm

# install percona and it's dependencies
yum install Percona-XtraDB-Cluster-56
```

### Best practice - LVM partitions
It is a good practice to partition your server in order to isolate database elements.
I choose to use 3 partitions :

 - data partition (mounted on the *datadir* directory) 
 - binlogs partition (mounted on the log-bin directory)
 - logs partition, usually your   system's /var/log partition

### Configure on node1 and node2
####Node 1 /etc/my.cnf
```
[mysqld]

######################
#       GLOBAL       #
######################

user=mysql

datadir=/home/databases/mysql/data
pid-file=/var/run/mysql/mysql.pid
socket=/var/run/mysql/mysql.sock

skip_name_resolve = 1


######################
#       ENGINE       #
######################

# will create one file per table
innodb_file_per_table = 1

# This changes how InnoDB autoincrement locks are managed and is a requirement for Galera
innodb_autoinc_lock_mode=2

# 80% of available RAM (Percona recommendation)
innodb_buffer_pool_size=25G

######################
#       BINLOG       #
######################

log-bin=/home/databases/mysql/binlogs/binlog
expire_logs_days = 3
max_binlog_size = 100M
max_binlog_files = 200

# In order for Galera to work correctly binlog format should be ROW
binlog_format=ROW

# This changes how InnoDB autoincrement locks are managed and is a requirement for Galera
innodb_autoinc_lock_mode=2

######################
#       GALERA       #
######################

# Path to Galera library
wsrep_provider=/usr/lib64/libgalera_smm.so

# Cluster connection URL contains the IPs of node#1, node#2 and node#3
wsrep_cluster_address=gcomm://10.98.0.173,10.98.0.174

# MyISAM storage engine has only experimental support
default_storage_engine=InnoDB

# This changes how InnoDB autoincrement locks are managed and is a requirement for Galera
innodb_autoinc_lock_mode=2

# SST method
wsrep_sst_method=xtrabackup-v2

# Cluster name
wsrep_cluster_name=mycluster

# Authentication for SST method
wsrep_sst_auth="sstuser:tT3B6dflRN"


#####################
#        LOGS       #
#####################

log-error = /home/logs/mysql/error.log
log_warnings = 2
slow_query_log = 1
slow_query_log_file = /home/logs/mysql/slow.log
log_queries_not_using_indexes
long-query-time = 2

[mysqld_safe]
pid-file=/var/run/mysqld/mysqld.pid
```

####Node 2 /etc/my.cnf
```
[mysqld]

######################
#       GLOBAL       #
######################

user=mysql

datadir=/home/databases/mysql/data
pid-file=/var/run/mysql/mysql.pid
socket=/var/run/mysql/mysql.sock

skip_name_resolve = 1


######################
#       ENGINE       #
######################

# will create one file per table
innodb_file_per_table = 1

# This changes how InnoDB autoincrement locks are managed and is a requirement for Galera
innodb_autoinc_lock_mode=2

# 80% of available RAM (Percona recommendation)
innodb_buffer_pool_size=25G

######################
#       BINLOG       #
######################

log-bin=/home/databases/mysql/binlogs/binlog
expire_logs_days = 3
max_binlog_size = 100M
max_binlog_files = 200

# In order for Galera to work correctly binlog format should be ROW
binlog_format=ROW

# This changes how InnoDB autoincrement locks are managed and is a requirement for Galera
innodb_autoinc_lock_mode=2

######################
#       GALERA       #
######################

# Path to Galera library
wsrep_provider=/usr/lib64/libgalera_smm.so

# Cluster connection URL contains the IPs of node#1, node#2 and node#3
wsrep_cluster_address=gcomm://10.98.0.173,10.98.0.174

# MyISAM storage engine has only experimental support
default_storage_engine=InnoDB

# Node #2 address
wsrep_node_address=10.98.0.174

# SST method
wsrep_sst_method=xtrabackup-v2

# Cluster name
wsrep_cluster_name=mycluster

# Authentication for SST method
wsrep_sst_auth="sstuser:tT3B6dflRN"


#####################
#        LOGS       #
#####################

log-error = /home/logs/mysql/error.log
log_warnings = 2
slow_query_log = 1
slow_query_log_file = /home/logs/mysql/slow.log
log_queries_not_using_indexes
long-query-time = 2

[mysqld_safe]
pid-file=/var/run/mysqld/mysqld.pid

```
#### On both nodes 

```bash
# edit /etc/my-client.cnf to contains root connection to the database
cat <<EOF >> /etc/my-client.cnf
[client]
user            = root
password        = <root-password>
socket          = /var/run/mysql/mysql.sock
EOF

# protect the file 
chmod 600 /etc/my-client.cnf

# symlink to /root/.my.cnf to allow root user to connect without password
ln -s /etc/my-client.cnf /root/.my.cnf
```


### Bootstrap
Bootstrap when no cluster is running. 
```bash
# on one node (ex. node1) start the database cluster
/etc/init.d/mysql bootstrap-pxc

# on other nodes (here node2) start database normally
/etc/init.d/mysql start
```

### Install garbd node (galera arbitrator)
```bash
# add new Percona repository
yum install http://www.percona.com/downloads/percona-release/redhat/0.1-3/percona-release-0.1-3.noarch.rpm

# install percona's garbd package and it's dependencies
yum install Percona-XtraDB-Cluster-garbd-3-3.9-1.3494.rhel6.x86_64
```

### Configure garbd
//todo

### Backup and restore
#### Set up backups

Percona comes with its own backup solution [XtraBackup](https://www.percona.com/doc/percona-xtrabackup/2.4/how_xtrabackup_works.html). Basically it creates 2 threads. The first one runs in the background and record every actions in a log file from the beginning of the backup process till the end. The second one copies the database to the backup directory using InnoDB.

The tool is really powerful and allow to create full backups, incremental backups, partial backups. Sadly it doesn't come with the ability to automate itself like AutoMySQLBackups. This is why we are going to write a simple bash script that create one full backup per week, one incremental backup per day and 2 weeks retention (2 full and 12 incremental).

Edit script /home/databases/mysql/backups/xtrabackup.sh (cron every day at 3am)
```bash
#!/bin/bash
#
# Just a small script to manage percona xtrabackup's full and incremental backups.
# We will perform a full backup if it's Sunday or an incremental backup otherwise
#
# Need to be cron every night.
#
# Author: Baptiste Bonnaudet
#
############

PATH=/usr/local/sbin:/sbin:/bin:/usr/sbin:/usr/bin


# take a full backup function
function full_backup {
        echo -e "**********************************************************"
        echo -e "** FULL BACKUP OF $(date)"
        echo -e "**********************************************************\n"

        # do one full backup
        xtrabackup --backup --datadir=/home/databases/mysql/data/ \
        --target-dir=/home/databases/mysql/backups/full-weekly/backup_$(date +%Y%m%d_%H%M%S)_full

        # remove previous *last* symlink
        rm -f /home/databases/mysql/backups/full-weekly/last

        # link last full backup to *last*
        cd /home/databases/mysql/backups/full-weekly/ && \
        ln -s -f `ls -t /home/databases/mysql/backups/full-weekly/ | grep backup | head -n1` last

        # remove backups older than 2 weeks
        /usr/bin/find /home/databases/mysql/backups/full-weekly/ -name "backup*" -mtime +15 -exec rm {} \;
}

# take an incremental backup function
function incremental_backup {
        echo -e "**********************************************************"
        echo -e "** INCREMENTAL BACKUP OF $(date)"
        echo -e "**********************************************************\n"

        # do one incremental backup
        xtrabackup --backup --target-dir=/home/databases/mysql/backups/incremental-daily/backup_$(date +%Y%m%d_%H%M%S)_inc \
        --incremental-basedir=/home/databases/mysql/backups/full-weekly/last/ --datadir=/home/databases/mysql/data/

        # remove backups older than 7 days
        /usr/bin/find /home/databases/mysql/backups/incremental-daily/ -name "backup*" -mtime +7 -exec rm {} \;
}

# script
if [ "$(date +"%A")" == "Sunday" ];
then
        # it's sunday, time for a full backup
        full_backup
else
        # it's working days we do a quick incremental backup, except if no base backup is present then we do a full backup
        if [ -f /home/databases/mysql/backups/full-weekly/last/xtrabackup_checkpoints ]
        then
                incremental_backup
        else
                full_backup
        fi
fi
```

#### Restore
#####Restore a full backup
```bash
xtrabackup --prepare --target-dir=/data/backups/mysql/
#TODO rm datadir + rsync restore
```
#####Restore an incremental backup
Restoring an incremental backup means preparing the base backup + adding the incremental backup to the base backup.
```bash
# Restore base backup (last full) with --apply-log-only option to prevent the rollback phase
xtrabackup --prepare --apply-log-only --target-dir=/data/backups/base
# To apply the first incremental backup to the full backup, you should use the following command:
xtrabackup --prepare --apply-log-only --target-dir=/data/backups/base \
--incremental-dir=/data/backups/inc1
#TODO rm datadir + rsync restore
```