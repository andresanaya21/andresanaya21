# OpenNebula & Submariner Deployment Guide

## Overview
This document provides a step-by-step guide for deploying a **multi-cluster RKE2 environment** using **OpenNebula** as the infrastructure layer and **Submariner** for inter-cluster networking.

The setup includes:
- **Three clusters:** `broker`, `west`, and `east`.
- **RKE2 installation** on all clusters.
- **Calico CNI** configuration.
- **Submariner** deployment for cross-cluster communication.
- **Service discovery and connectivity verification**.

---
## **Cluster Information**
### OpenNebula Cluster Details
| Cluster Name | URL | IP Address |
|-------------|------------------------------------|--------------|
| **Broker**  | [OneFlow Broker](https://one.discovery.hi.inet/#oneflow-services-tab/245) | `10.95.82.208` |
| **West**    | [OneFlow West](https://one.discovery.hi.inet/#oneflow-services-tab/244)  | `10.95.82.209` |
| **East**    | [OneFlow East](https://one.discovery.hi.inet/#oneflow-services-tab/243)  | `10.95.82.210` |

### Access Credentials
- **Cluster SSH Access:**
  - `User: root`
  - `Password: labpassword`

---
## **Network Topology Diagram**
The following `.drawio` file provides a visual representation of the network topology and cluster connectivity.

**[Topology Diagram](opennebula/multicluster.drawio)**

![Topology](opennebula/multicluster.png)


---

## **1. Install RKE2 on All Clusters**
### **1.1 Pre-Installation Setup**
Run these commands on `broker`, `west`, and `east` clusters:
```sh
systemctl stop ufw
systemctl disable ufw
apt update && apt install nfs-common -y
apt upgrade -y
apt autoremove -y
```

### **1.2 Configure RKE2**
Create the RKE2 config directory and edit the configuration file:
```sh
mkdir -p /etc/rancher/rke2/
vim /etc/rancher/rke2/config.yaml
```

Add the following configuration to cluster-broker:
```yaml
disable:
  - rke2-ingress-nginx
tls-san:
  - rke2-mc-broker
  - 10.95.82.208
cni: calico
cluster-cidr: "10.42.0.0/16"
service-cidr: "10.43.0.0/16"
```

Add the following configuration to cluster-west:
```yaml
disable:
  - rke2-ingress-nginx
tls-san:
  - rke2-mc-west
  - 10.95.82.209
cni: calico
cluster-cidr: "10.44.0.0/16"
service-cidr: "10.45.0.0/16"
```

Add the following configuration to cluster-east:
```yaml
disable:
  - rke2-ingress-nginx
tls-san:
  - rke2-mc-east
  - 10.95.82.210
cni: calico
cluster-cidr: "10.98.0.0/16"
service-cidr: "10.99.0.0/16"
```

### **1.3 Update `/etc/hosts` (if no DNS available)**
```sh
echo "10.95.82.208 rke2-mc-broker" >> /etc/hosts
echo "10.95.82.209 rke2-mc-east" >> /etc/hosts
echo "10.95.82.210 rke2-mc-west" >> /etc/hosts
```

### **1.4 Install RKE2 and Start the Service**
```sh
curl -sfL https://get.rke2.io | sh -
systemctl enable --now rke2-server.service
```

### **1.5 Set Up kubectl Access**
```sh
ln -s $(find /var/lib/rancher/rke2/data/ -name kubectl) /usr/local/bin/kubectl
export KUBECONFIG=/etc/rancher/rke2/rke2.yaml
kubectl get nodes
```

### **1.6 Configure Cluster-Specific Kubeconfig Files**
Modify the context for each cluster in the `.kubeconfig` files:
```yaml
context: west   # for cluster-west.kubeconfig
context: east   # for cluster-east.kubeconfig
```

---
## **2. Configure Calico CNI**

The next procedure can be done in local.

### **2.1 Install Calicoctl**
```sh
curl -L https://github.com/projectcalico/calico/releases/download/v3.29.2/calicoctl-linux-amd64 -o calicoctl
chmod +x calicoctl
install calicoctl /usr/local/bin/calicoctl
```

### **2.2 Apply Calico Configuration to Clusters**
```sh
kubectl --kubeconfig cluster-west.kubeconfig apply -f rke2-calico-config.yaml
DATASTORE_TYPE=kubernetes KUBECONFIG=cluster-west.kubeconfig calicoctl create -f cluster-west-pod-svc.yaml --allow-version-mismatch
DATASTORE_TYPE=kubernetes KUBECONFIG=cluster-east.kubeconfig calicoctl create -f cluster-east-pod-svc.yaml --allow-version-mismatch
```

---
## **3. Install and Configure Submariner**

The next procedure can be done in local.

### **3.1 Install Subctl**
```sh
curl -Ls https://get.submariner.io | bash
export PATH=$PATH:~/.local/bin
echo "export PATH=$PATH:~/.local/bin" >> ~/.profile
sudo install ~/.local/bin/subctl /usr/local/bin/subctl
```

### **3.2 Deploy Submariner Broker**
```sh
subctl deploy-broker --kubeconfig cluster-broker.kubeconfig
```

### **3.3 Label Nodes for Submariner Gateway Deployment**
```sh
kubectl --kubeconfig cluster-west.kubeconfig label node rke2-mc-west submariner.io/gateway=true
kubectl --kubeconfig cluster-east.kubeconfig label node rke2-mc-east submariner.io/gateway=true
```

### **3.4 Join Clusters to Submariner Broker**
```sh
subctl join --kubeconfig cluster-west.kubeconfig broker-info.subm --clusterid west --check-broker-certificate=false --coredns-custom-configmap=kube-system/rke2-coredns-rke2-coredns --operator-debug --pod-debug --globalnet

subctl join --kubeconfig cluster-east.kubeconfig broker-info.subm --clusterid east --check-broker-certificate=false --coredns-custom-configmap=kube-system/rke2-coredns-rke2-coredns --operator-debug --pod-debug --globalnet
```

### **3.5 Verify Submariner Deployment**
```sh
export KUBECONFIG=cluster-west.kubeconfig:cluster-east.kubeconfig
subctl verify --context west --tocontext east --only connectivity --verbose

subctl diagnose all --context west
subctl show connections --context east
subctl show gateways --context west
```
---
## **4. Configure CoreDNS for Service Discovery**

Submariner update the CoreDNS configMap autmatically once the clusters have been joinned, however, ensure CoreDNS is properly configured to forward queries for `clusterset.local` to Lighthouse.

### **4.1 Update CoreDNS ConfigMap**
Modify the CoreDNS ConfigMap in the `kube-system` namespace:
```yaml
apiVersion: v1
data:
  Corefile: |-
    .:53 {
        errors
        health {
            lameduck 5s
        }
        ready
        kubernetes cluster.local cluster.local in-addr.arpa ip6.arpa {
            pods insecure
            fallthrough in-addr.arpa ip6.arpa
            ttl 30
        }
        prometheus 0.0.0.0:9153
        forward . /etc/resolv.conf
        cache 30
        loop
        reload
        loadbalance
    }

    clusterset.local:53 {
        forward . <LIGHTHOUSE_DNS_IP>
    }
```
Replace `<LIGHTHOUSE_DNS_IP>` with the correct IP address of the Lighthouse DNS service.

### **4.2 Restart CoreDNS**
```sh
kubectl rollout restart deployment -n kube-system rke2-coredns
```

This ensures that service discovery across clusters functions properly using Submariner's Lighthouse component.

---
## **5. Testing Cross-Cluster Connectivity**
### **5.1 Deploy Nginx in West Cluster**
```sh
kubectl --kubeconfig cluster-west.kubeconfig create namespace nginx-test
kubectl --kubeconfig cluster-west.kubeconfig -n nginx-test create deployment nginx --image=nginxinc/nginx-unprivileged:stable-alpine
kubectl --kubeconfig cluster-west.kubeconfig -n nginx-test apply -f nginx-west-svc.yaml

kubectl --kubeconfig cluster-east.kubeconfig create namespace nginx-test
kubectl --kubeconfig cluster-broker.kubeconfig create namespace nginx-test
```

### **5.2 Export the Service Across Clusters**
```sh
kctx west
subctl export service --namespace nginx-test nginx
```

### **5.3 Verify Service Discovery**
```sh
kubectl get -n nginx-test serviceimport
kubectl -n nginx-test describe serviceexports
```

### **5.4 Test Connectivity from East Cluster**
```sh
kubectl --kubeconfig cluster-east.kubeconfig run -n nginx-test tmp-shell --rm -i --tty --image quay.io/submariner/nettest -- nslookup nginx.nginx-test.svc.clusterset.local

Server:         10.45.0.10
Address:        10.45.0.10#53

Name:   nginx.nginx-test.svc.clusterset.local
Address: 10.45.160.84

kubectl run -n nginx-test tmp-shell --rm -i --tty --image quay.io/submariner/nettest -- /bin/bash

tmp-shell-pod$ wget --spider http://nginx.nginx-test.svc.clusterset.local:8080

Connecting to nginx.nginx-test.svc.clusterset.local:8080 (10.45.160.84:8080)

```

### **5.5 Test Connectivity from East Cluster using LoxiLB**

```sh
kctx west
k apply -f loxilb/loxi-nobgp.yaml
k apply -f loxilb/kube-loxilb.yaml
k apply -f loxilb/iperf3-server-loxilb.yaml
subctl export service --namespace nginx-test nginx

kctx east
k apply -f iperf3-client.yaml
k exec -it iperf3-client-5f47757b5f-mfsnl -- iperf3 -c iperf3-server.default.svc.clusterset.local -p 5201
Connecting to host 10.95.82.149, port 5201
[  5] local 10.98.23.121 port 38434 connected to 10.95.82.149 port 5201
[ ID] Interval           Transfer     Bitrate         Retr  Cwnd
[  5]   0.00-1.00   sec   994 MBytes  8.33 Gbits/sec   92   2.86 MBytes       
[  5]   1.00-2.00   sec  1.43 GBytes  12.3 Gbits/sec    3   2.87 MBytes       
[  5]   2.00-3.00   sec  1.77 GBytes  15.2 Gbits/sec    0   2.92 MBytes       
[  5]   3.00-4.00   sec  1.77 GBytes  15.2 Gbits/sec    0   2.92 MBytes       
[  5]   4.00-5.00   sec  1.86 GBytes  16.0 Gbits/sec    0   2.92 MBytes       
[  5]   5.00-6.00   sec  1.50 GBytes  12.9 Gbits/sec    0   2.92 MBytes       
[  5]   6.00-7.00   sec  2.01 GBytes  17.3 Gbits/sec    0   2.93 MBytes       
[  5]   7.00-8.00   sec  2.28 GBytes  19.6 Gbits/sec   58   2.95 MBytes       
[  5]   8.00-9.00   sec  1.70 GBytes  14.6 Gbits/sec    0   2.95 MBytes       
[  5]   9.00-10.00  sec  1.70 GBytes  14.6 Gbits/sec    0   2.95 MBytes       
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bitrate         Retr
[  5]   0.00-10.00  sec  17.0 GBytes  14.6 Gbits/sec  153             sender
[  5]   0.00-10.00  sec  17.0 GBytes  14.6 Gbits/sec                  receiver

```

### **5.6 Test Connectivity from East Cluster using iperf3**

```sh
kctx west
k apply -f iperf3-server-loxilb.yaml
subctl export service --namespace default iperf3-server

kctx east
k apply -f iperf3-client.yaml
k exec -it iperf3-client-5f47757b5f-mfsnl -- iperf3 -c iperf3-server.default.svc.clusterset.local -p 5201
Connecting to host iperf3-server.default.svc.clusterset.local, port 5201
[  5] local 10.98.23.121 port 51798 connected to 10.45.71.190 port 5201
[ ID] Interval           Transfer     Bitrate         Retr  Cwnd
[  5]   0.00-1.03   sec  32.4 MBytes   265 Mbits/sec   19    200 KBytes       
[  5]   1.03-2.00   sec  34.3 MBytes   294 Mbits/sec    0    226 KBytes       
[  5]   2.00-3.03   sec  37.1 MBytes   302 Mbits/sec   20    264 KBytes       
[  5]   3.03-4.00   sec  41.9 MBytes   363 Mbits/sec    1    346 KBytes       
[  5]   4.00-5.00   sec  45.2 MBytes   379 Mbits/sec    1    423 KBytes       

[  5]   5.00-6.00   sec  49.4 MBytes   414 Mbits/sec   26    467 KBytes       
[  5]   6.00-7.01   sec  39.9 MBytes   333 Mbits/sec    3    472 KBytes       
[  5]   7.01-8.02   sec  57.6 MBytes   478 Mbits/sec    2    479 KBytes       
[  5]   8.02-9.02   sec  53.0 MBytes   446 Mbits/sec    2    494 KBytes       
[  5]   9.02-10.00  sec  53.8 MBytes   457 Mbits/sec    0    494 KBytes       
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bitrate         Retr
[  5]   0.00-10.00  sec   444 MBytes   373 Mbits/sec   74             sender
[  5]   0.00-10.01  sec   444 MBytes   373 Mbits/sec                  receiver

```


---
## **6. Uninstall Submariner**
```sh
subctl uninstall --kubeconfig cluster-west.kubeconfig
subctl uninstall --kubeconfig cluster-east.kubeconfig
subctl uninstall --kubeconfig broker.kubeconfig
```

---
## **Additional Notes**
- Service CIDR and Cluster CIDR must be **different across clusters** to avoid routing conflicts.
- A **broker cluster** connects other clusters and can be a separate cluster or one of the participating clusters.
- **Subctl supports round-robin service distribution** across multiple clusters.

---
### **References**
- [Submariner Documentation](https://submariner.io/operations/usage/)

