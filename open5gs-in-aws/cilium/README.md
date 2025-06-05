
```sh
# m5.xlarge instance type
# include role with enough permissions -- CiliumRole
# include a EIP in the EC2 instance -- to the eth0 ENI 

sudo mkdir -p /etc/rancher/rke2

sudo tee /etc/rancher/rke2/config.yaml > /dev/null <<EOF
disable:
  - rke2-ingress-nginx
  - rke2-cilium
cloud-provider-name: external
cni: none
tls-san:
  - ip-172-4-39-115.eu-west-3.compute.internal
node-label:
  - "cluster=rke2-cilium"
kube-apiserver-arg:
  - service-node-port-range=2152-40000
EOF

curl -sfL https://get.rke2.io | sudo sh -
#curl -sfL https://get.rke2.io | sudo INSTALL_RKE2_VERSION="v1.31.8+rke2r1" sh -
sudo systemctl enable rke2-server.service
sudo systemctl start rke2-server.service

sudo find / -name kubectl
sudo install /var/lib/rancher/rke2/data/v1.31.8-rke2r1-2b6cfe81cbb5/bin/kubectl /usr/local/bin/kubectl
mkdir .kube
sudo cp -p /etc/rancher/rke2/rke2.yaml .kube/config
sudo chown $(id -u):$(id -g) -R .kube/

sudo journalctl -u rke2-server -f
export KUBECONFIG=/etc/rancher/rke2/rke2.yaml

kubectl patch node ip-172-4-39-115  -p "{\"spec\":{\"providerID\":\"aws:///eu-west-3c/i-0d1008086c231de16\"}}"
kubectl taint nodes ip-172-4-39-115 node.cloudprovider.kubernetes.io/uninitialized=false:NoSchedule- 

kubectl logs -n kube-system -l k8s-app=cilium -f

# delete and modify permission files of kube-proxy
sudo systemctl stop rke2-server
sudo rm /var/lib/rancher/rke2/agent/pod-manifests/kube-proxy.yaml
sudo touch /var/lib/rancher/rke2/agent/pod-manifests/kube-proxy.yaml
sudo chmod 000 /var/lib/rancher/rke2/agent/pod-manifests/kube-proxy.yaml

# install cilium cni
sudo apt update
sudo apt install apt-transport-https curl -y
curl https://baltocdn.com/helm/signing.asc | sudo apt-key add -
echo "deb https://baltocdn.com/helm/stable/debian/ all main" | sudo tee /etc/apt/sources.list.d/helm-stable-debian.list
sudo apt update
sudo apt install helm -y
helm version

helm repo add eks https://aws.github.io/eks-charts
helm repo add cilium https://helm.cilium.io/
helm repo update

helm upgrade --install cilium cilium/cilium \
  --version 1.14.2 \
  --namespace kube-system \
  --set kubeProxyReplacement=strict \
  --set masquerade=true \
  --set externalIPs.enabled=true \
  --set loadBalancer.enabled=true \
  --set loadBalancer.algorithm=maglev \
  --set nodePort.enabled=true \
  --set hubble.enabled=true \
  --set hubble.ui.enabled=true \
  --set hubble.relay.enabled=true \
  --set ipam.mode=eni \
  --set eni.enabled=true \
  --set aws.enabled=true \
  --set tunnel=disabled \
  --set routingMode=native \
  --set operator.replicas=1 \
  --set sctp.enabled=true \
  --set enableIPv4Masquerade=true \
  --set eni.subnet-ids='{subnet-0ddaa67fa7580e39a,subnet-0252c0d024de99979}'

#  --set ipv4-native-routing-cidr="172.4.32.0/20"
# --set cluster.poolIPv4PodCIDRList="{10.244.0.0/16}"
# egress-masquerade-interfaces: "true"
# --set eni.subnet-tags="k8s-cni=enabled"

# wait until cilium pods ready, and rke2-coredns running

# netshoot pod
kubectl run netshoot -i --tty --image nicolaka/netshoot

kubectl -n kube-system get configmap cilium-config -o yaml | grep sctp

# check cilium use its proxy
kubectl -n kube-system exec -ti daemonset/cilium -- cilium status | grep Proxy

# check kube-proxy is not installed
sudo /var/lib/rancher/rke2/data/v1.31.7-rke2r1-7f85e977b85d/bin/crictl --runtime-endpoint unix:///run/k3s/containerd/containerd.sock ps | grep kube-proxy

# restart cilium
kubectl -n kube-system rollout restart daemonset cilium
kubectl -n kube-system get configmap cilium-config -o yaml

# iptables
sudo apt-get install -y iptables-persistent
sudo iptables -t nat -A POSTROUTING -s 172.4.0.0/16 ! -d 172.4.0.0/16 -o enX0 -j SNAT --to-source 172.4.39.115
sudo iptables -t nat -L POSTROUTING -n -v
sudo netfilter-persistent save
kubectl exec -it netshoot -- ping -c 3 8.8.8.8 && ping -c 3 google.com

# examples

kubectl apply -f deployment-nginx.yaml
kubectl apply -f sctp-deploy.yaml

NODE_IP=ec2-13-38-249-26.eu-west-3.compute.amazonaws.com
PORT=$(kubectl get svc/sctp-deployment -o jsonpath='{.spec.ports[0].nodePort}')

# test
sudo apt install ncat -y

# ncat in alpline (netshoot)
apk update
apk add nmap-ncat



kubectl -n kube-system port-forward svc/hubble-relay 4245:80


HUBBLE_VERSION=$(curl -s https://raw.githubusercontent.com/cilium/hubble/master/stable.txt)
HUBBLE_ARCH=amd64
if [ "$(uname -m)" = "aarch64" ]; then HUBBLE_ARCH=arm64; fi

curl -L --fail --remote-name-all \
  https://github.com/cilium/hubble/releases/download/$HUBBLE_VERSION/hubble-linux-${HUBBLE_ARCH}.tar.gz{,.sha256sum}

sudo tar xzvfC hubble-linux-${HUBBLE_ARCH}.tar.gz /usr/local/bin

rm hubble-linux-${HUBBLE_ARCH}.tar.gz{,.sha256sum}

hubble version

# cilium cli
sudo apt  install golang-go  -y
CILIUM_CLI_VERSION=$(curl -s https://raw.githubusercontent.com/cilium/cilium-cli/main/stable.txt)
GOOS=$(go env GOOS)
GOARCH=$(go env GOARCH)

curl -L --remote-name-all \
  https://github.com/cilium/cilium-cli/releases/download/${CILIUM_CLI_VERSION}/cilium-${GOOS}-${GOARCH}.tar.gz{,.sha256sum}

sudo tar xzvf cilium-${GOOS}-${GOARCH}.tar.gz -C /usr/local/bin

rm cilium-${GOOS}-${GOARCH}.tar.gz{,.sha256sum}

cilium version
cilium hubble enable

hubble observe --protocol sctp --follow

hubble observe --port 80 --follow

kubectl apply -f hubble-svc-ui.yaml

# test
sudo ss -pano | grep 9999

hubble observe --protocol sctp --follow

May  5 10:41:15.528: 172.4.32.89:42696 (world) -> default/sctp-deployment-68b98cc666-nxsr5:9999 (ID:12827) to-endpoint FORWARDED (SCTP)
May  5 10:41:15.528: 172.4.32.89:42696 (host) <- default/sctp-deployment-68b98cc666-nxsr5:9999 (ID:12827) to-stack FORWARDED (SCTP)
May  5 10:41:34.486: 172.4.32.89:15328 (world) -> default/sctp-deployment-68b98cc666-nxsr5:9999 (ID:12827) to-endpoint FORWARDED (SCTP)
May  5 10:41:34.486: 172.4.32.89:15328 (host) <- default/sctp-deployment-68b98cc666-nxsr5:9999 (ID:12827) to-stack FORWARDED (SCTP)

In AWS CloudWatch Logs -- Enabling VPC Flow.

2 774986117405 eni-0b0f90af74f3019f1 150.214.47.156 172.4.47.129 0 0 132 6 568 1746441325 1746441343 ACCEPT OK
2 774986117405 eni-0b0f90af74f3019f1 172.4.47.129 150.214.47.156 0 0 132 7 648 1746441325 1746441343 ACCEPT OK

| Field                   | Value                          | Meaning                                                                                                                     |
| ----------------------- | ------------------------------ | --------------------------------------------------------------------------------------------------------------------------- |
| `2`                     | 2                              | Version of the flow log format.                                                                                             |
| `774986117405`          | (Your AWS Account ID)          | Account ID that owns the network interface.                                                                                 |
| `eni-0b0f90af74f3019f1` | (Elastic Network Interface ID) | The ENI associated with the traffic.                                                                                        |
| `150.214.47.156`        | Source IP                      | **Source IP address** (public IP or private IP of sender).                                                                  |
| `172.4.47.129`          | Destination IP                 | **Destination IP address** (likely your instance or pod inside the VPC).                                                    |
| `0`                     | Source port                    | Source port — **0 usually means it's an ICMP packet or the protocol doesn’t use ports**, but sometimes can be missing data. |
| `0`                     | Destination port               | Same as above — port **0 means no port** (or not applicable).                                                               |
| `132`                   | Protocol                       | **132 = SCTP** (Stream Control Transmission Protocol).                                                                      |
| `6`                     | Packets                        | **6 packets** observed during this flow.                                                                                    |
| `568`                   | Bytes                          | **568 bytes** transferred.                                                                                                  |
| `1746441325`            | Start time                     | **Flow start time (epoch)** — `1746441325` → Tue,  6 May 2025 10:35:25 GMT *(you can convert using an epoch converter)*.    |
| `1746441343`            | End time                       | **Flow end time (epoch)** — Tue,  6 May 2025 10:35:43 GMT.                                                                  |
| `ACCEPT`                | Action                         | The traffic was **accepted** by security groups and NACLs.                                                                  |
| `OK`                    | Log status                     | Logging was successful.                                                                                                     |

```

```sh
# good to know:
the ncat was done in a opennebula vm in UMA datacenter

root@dis-andres-origami-bridge:/home/researcher# ncat --sctp ec2-15-236-113-156.eu-west-3.compute.amazonaws.com 9999
Howdy! What's your name?
andres
Thanks for calling, andres. Bye, now.
root@dis-andres-origami-bridge:/home/researcher#

# iperf
sudo apt update
sudo apt install iperf3 -y

# server
iperf3 -s -B 10.45.0.11 
iperf3 -s --bind-dev uesimtun0

# client
iperf3 -c 10.45.0.11
iperf3 -c 10.45.0.11 -B 10.45.0.12
iperf3 -c 10.45.0.11 --bind-dev uesimtun0

# using nc
# using nc in mode server tcp
nc -l -s 10.45.0.16 -p 8080

# using nc in mode client tcp
nc 10.45.0.16 8080

# using nc in mode server udp
nc -u -l -s 10.45.0.17 -p 8080

# using cn in mode client udp
nc -u 10.45.0.17 8080
```

```sh
# uninstall rke2
sudo /usr/local/bin/rke2-uninstall.sh 
```

```sh
# aws commands

# primary subnet public interface
aws ec2 describe-network-interfaces \
  --network-interface-ids eni-0b6571c74a7cce1db \
  --query 'NetworkInterfaces[0].PrivateIpAddresses[*].PrivateIpAddress' \
  --output text

# unassing secudary private ips
aws ec2 unassign-private-ip-addresses \
  --network-interface-id eni-0f57e044ec206c5ac \
  --private-ip-addresses 172.2.48.251 172.2.48.184 172.2.48.15

# second subnet private interface
aws ec2 describe-network-interfaces \
  --network-interface-ids eni-0b6571c74a7cce1db \
  --query 'NetworkInterfaces[0].PrivateIpAddresses[*].PrivateIpAddress' \
  --output text

```