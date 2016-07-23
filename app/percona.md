Set up a Percona XtraDB multi-master cluster
=========================

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

### Configure on node1 and node2
Node 1 /etc/my.cnf
```
[mysqld]

datadir=/var/lib/mysql
user=mysql

# Path to Galera library
wsrep_provider=/usr/lib64/libgalera_smm.so

# Cluster connection URL contains the IPs of node#1, node#2 and node#3
wsrep_cluster_address=gcomm://10.98.0.173,10.98.0.174

# In order for Galera to work correctly binlog format should be ROW
binlog_format=ROW

# MyISAM storage engine has only experimental support
default_storage_engine=InnoDB

# This changes how InnoDB autoincrement locks are managed and is a requirement for Galera
innodb_autoinc_lock_mode=2

# Node #1 address
wsrep_node_address=10.98.0.173

# SST method
wsrep_sst_method=xtrabackup-v2

# Cluster name
wsrep_cluster_name=rexelus_cluster

# Authentication for SST method
wsrep_sst_auth="sstuser:s3cret"

[mysqld_safe]
log-error=/var/log/mysqld.log
pid-file=/var/run/mysqld/mysqld.pid
```

Node 2 /etc/my.cnf
```
[mysqld]

datadir=/var/lib/mysql
user=mysql

# Path to Galera library
wsrep_provider=/usr/lib64/libgalera_smm.so

# Cluster connection URL contains the IPs of node#1, node#2 and node#3
wsrep_cluster_address=gcomm://10.98.0.173,10.98.0.174

# In order for Galera to work correctly binlog format should be ROW
binlog_format=ROW

# MyISAM storage engine has only experimental support
default_storage_engine=InnoDB

# This changes how InnoDB autoincrement locks are managed and is a requirement for Galera
innodb_autoinc_lock_mode=2

# Node #2 address
wsrep_node_address=10.98.0.174

# SST method
wsrep_sst_method=xtrabackup-v2

# Cluster name
wsrep_cluster_name=rexelus_cluster

# Authentication for SST method
wsrep_sst_auth="sstuser:s3cret"

[mysqld_safe]
log-error=/var/log/mysqld.log
pid-file=/var/run/mysqld/mysqld.pid
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