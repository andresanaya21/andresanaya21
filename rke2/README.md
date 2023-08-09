# RKE2 Server
## Ubuntu instructions

```
# stop the software firewall
systemctl stop ufw
systemctl disable ufw

# get updates, install nfs, and apply
apt update
apt install nfs-common -y
apt upgrade -y

# clean up
apt autoremove -y

curl -sfL https://get.rke2.io | sh -
# start and enable for restarts

systemctl enable rke2-server.service
systemctl start rke2-server.service

# simlink all the things - kubectl
ln -s $(find /var/lib/rancher/rke2/data/ -name kubectl) /usr/local/bin/kubectl

# add kubectl conf
export KUBECONFIG=/etc/rancher/rke2/rke2.yaml
# check node status
kubectl  get node

# helm
curl -L https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# longhorn
# get charts
helm repo add longhorn https://charts.longhorn.io
# update
helm repo update
# install
helm upgrade -i longhorn longhorn/longhorn --namespace longhorn-system --create-namespace

# metalLB
MetalLB_RTAG=$(curl -s https://api.github.com/repos/metallb/metallb/releases/latest|grep tag_name | cut -d '"' -f 4|sed 's/v//')
mkdir ~/metallb
cd ~/metallb
wget https://raw.githubusercontent.com/metallb/metallb/v$MetalLB_RTAG/config/manifests/metallb-native.yaml
kubectl apply -f metallb-native.yaml

vim ~/metallb/ipaddress_pools.yaml

```apiVersion: metallb.io/v1beta1
kind: IPAddressPool
metadata:
  name: production
  namespace: metallb-system
spec:
  addresses:
  - 192.168.1.30-192.168.1.50
---
apiVersion: metallb.io/v1beta1
kind: L2Advertisement
metadata:
  name: l2-advert
  namespace: metallb-system```
 
kubectl apply -f  ~/metallb/ipaddress_pools.yaml
```

## ssm install
- Add SSMRoleInstance (mazonSSMManagedInstanceCore policy)
```
sudo snap install amazon-ssm-agent --classic
sudo snap list amazon-ssm-agent
sudo snap start amazon-ssm-agent
sudo snap services amazon-ssm-agent
```

## RKE2 agent
```
# stop the software firewall
systemctl stop ufw
systemctl disable ufw

# get updates, install nfs, and apply
apt update
apt install nfs-common -y
apt upgrade -y

# clean up
apt autoremove -y

# config.yaml
cat > /etc/rancher/rke2/config.yaml << EOF
server: https://my-cluster.rke2.int:9345
token: K10ca0c38d4ff90d8b80319ab34092e315a8b732622e6adf97bc9eb0536REDACTED::server:ec0308000b8a6b595da000efREDACTED
EOF

curl -sfL https://get.rke2.io | INSTALL_RKE2_TYPE="agent" sh -



```