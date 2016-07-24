Set up a CoreOS cluster
====================

### Discovery
We use the discovery service discovery.etcd.io. Alternatively you can use static bootstrap configuration or another etcd cluster for dynamic discovery .

On one node:
```bash
curl -w "\n" "https://discovery.etcd.io/new?size=3"
https://discovery.etcd.io/780e3118df0e8c7550008882a66e76e2
```

Note the address you will use it on next configuration.

### Configure cloud-config

On all nodes edit /home/core/cloud-config.yaml

```bash
#cloud-config

coreos:
  etcd2:
    # generate a new token for each unique cluster from https://discovery.etcd.io/new:
    discovery: https://discovery.etcd.io/780e3118df0e8c7550008882a66e76e2
    # multi-region deployments, multi-cloud deployments, and Droplets without
    # private networking need to use $public_ipv4:
    advertise-client-urls: http://$private_ipv4:2379,http://$private_ipv4:4001
    initial-advertise-peer-urls: http://$private_ipv4:2380
    # listen on the official ports 2379, 2380 and one legacy port 4001:
    listen-client-urls: http://0.0.0.0:2379,http://0.0.0.0:4001
    listen-peer-urls: http://$private_ipv4:2380
  fleet:
    public-ip: $private_ipv4   # used for fleetctl ssh command
  units:
    - name: etcd2.service
      command: start
    - name: fleet.service
      command: start
```
>The variable $private_ipv4 is compatible with AWS AMI. You can replace it with the private IP of the machine.
 
### Init cluster

```bash
coreos-cloudinit --from-file=/home/core/cloud-config.yaml
```

```bash
fleetctl list-machines                                                                                                                                             
MACHINE         IP              METADATA
0a75bfd7...     10.0.1.84       -
5a1775e1...     10.0.1.82       -
a469077e...     10.0.1.83       -
```


