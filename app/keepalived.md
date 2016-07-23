
Set up a floating virtual ip with Keepalived
=========================

### Introduction
This document will go through the installation of keepalived for seting up a floating IP using the VRRP protocol.

####What keepalived is
>Keepalived is a routing software written in C. The main goal of this project is to provide simple and robust facilities for loadbalancing and high-availability to Linux system and Linux based infrastructures.
#### What VRRP is
>The Virtual Router Redundancy Protocol (VRRP) is a computer networking protocol that provides for automatic assignment of available Internet Protocol (IP) routers to participating hosts. This increases the availability and reliability of routing paths via automatic default gateway selections on an IP subnetwork.

#### Why not using Pacemaker/Corosync/Heartbeat cluster?

VRRP is a lower level network protocol and keepalived's VRRP stack is pluged to kernel networking components and is articulated around a central I/O multiplexer that provide realtime networking design.

Compared to Pacemaker for setting-up VIP it's much more simpler to use and configure but you won't have the same flexibility as with Pacemaker for linking services (like a DRBD-NFS-VIP Pacemaker cluster).

#### Architecture
Function | Hostname | Interface | IP address
-------- | -------- | -------- | --------
Keepalived master| node1 |eth0 |10.98.0.173
Keepalived backup| node2   |eth0|10.98.0.174

#### Install on all nodes
```bash
# time to get dirty

# install kernel headers and dev dependencies
yum -y install gcc kernel-headers kernel-devel openssl-devel

# download the package
wget http://www.keepalived.org/software/keepalived-1.2.23.tar.gz

# extract 
tar -zxvf keepalived-1.2.23.tar.gz && cd keepalived-1.2.23

# build 
./configure --with-kernel-dir=/lib/modules/$(uname -r)/build
make && make install
```

#### Plug configuration files with you system 
We are using CentOS 6, it's compatible with CentOS 7 but it will be better to have a systemd unit file for that.

```bash
# main configuration file
cd /etc/sysconfig && ln -s /usr/local/etc/sysconfig/keepalived .

# rc.d script
cd /etc/rc3.d/ && ln -s /usr/local/etc/rc.d/init.d/keepalived S100keepalived

# init script
cd /etc/init.d/ && ln -s /usr/local/etc/rc.d/init.d/keepalived .

# add PATH to init script, edit /etc/init.d/keepalived and add at the beginning:
PATH=/usr/local/sbin/:/sbin:/bin:/usr/sbin:/usr/bin:/usr/local/sbin/


```

#### Configure
We choose here to configure VRRP using unicast which will work on all kind of networks.

Node1 is set as MASTER, it will start as master and if another master join it will have the priority 150. Node2 will start as BACKUP but will become master if no master is present, if a new master join it will have priority 100.

Both nodes share the same password *auth_pass s3cr3t*  .


#####Node1 /etc/keepalived/keepalived.conf

```bash
vrrp_instance VI_1 {
    state MASTER
    interface eth0
    virtual_router_id 51
    priority 150
    advert_int 1
    authentication {
        auth_type PASS
        auth_pass s3cr3t
    }

    unicast_src_ip 10.98.0.173
    unicast_peer {
        10.98.0.174
    }

    virtual_ipaddress {
        10.98.0.175/24 dev eth0
    }
}
```

#####Node2 /etc/keepalived/keepalived.conf

```bash
vrrp_instance VI_1 {
    state BACKUP
    interface eth0
    virtual_router_id 51
    priority 100
    advert_int 1
    authentication {
        auth_type PASS
        auth_pass yL0y1nkncK
    }

    unicast_src_ip 10.98.0.174
    unicast_peer {
        10.98.0.173
    }

    virtual_ipaddress {
        10.98.0.175/24 dev eth0
    }
}
```

#### Start keepalived on both nodes
```bash
# start the service
/etc/init.d/keepalived start
# take a look at /var/log/messages
tail -f /var/log/messages
```