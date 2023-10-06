# RKE2 Server
## ssm install
- Add SSMRoleInstance (mazonSSMManagedInstanceCore policy)
- Install ssm-aget (if needed). It is installed by default in ubuntu version 22.
```
sudo snap install amazon-ssm-agent --classic
sudo snap list amazon-ssm-agent
sudo snap start amazon-ssm-agent
sudo snap services amazon-ssm-agent
```

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

mkdir -p /etc/rancher/rke2/  && vim /etc/rancher/rke2/config.yaml
token: my-shared-secret
tls-san:
  - my-cluster-domain.com
  - 10.0.130.239
  - ip-10-0-130-239.eu-west-3.compute.internal

# add in /etc/hosts if not DNS
10.0.130.239 my-cluster-domain.com

# download rke2 in master mode
curl -sfL https://get.rke2.io | sh -

# start and enable for restarts
systemctl enable --now rke2-server.service

# simlink all the things - kubectl
ln -s $(find /var/lib/rancher/rke2/data/ -name kubectl) /usr/local/bin/kubectl

# add kubectl conf
export KUBECONFIG=/etc/rancher/rke2/rke2.yaml
# check node status
kubectl  get node

# to add more than one master
curl -sfL https://get.rke2.io | INSTALL_RKE2_TYPE="server" sh -

mkdir -p /etc/rancher/rke2/  && vim /etc/rancher/rke2/config.yaml

server: https://my-cluster-domain.com:9345
token: [token from /var/lib/rancher/rke2/server/node-token on server node 1]
tls-san:
  - my-cluster-domain.com

# add in /etc/hosts if not DNS
10.0.130.239 my-cluster-domain.com

# to add rke2 compatible with aws load balanacer
curl -sfL https://get.rke2.io | INSTALL_RKE2_TYPE="server" INSTALL_RKE2_EXEC="--token secret --kubelet-arg="cloud-provider=external" --kubelet-arg="provider-id=aws:///$provider_id" --write-kubeconfig-mode=644 --node-name=$(hostname -f)" sh -

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

apiVersion: metallb.io/v1beta1
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
  namespace: metallb-system
 
kubectl apply -f  ~/metallb/ipaddress_pools.yaml

# ingress controller nginx
$ helm upgrade --install ingress-nginx ingress-nginx -n ingress-nginx --create-namespace --repo https://kubernetes.github.io/ingress-nginx --set rbac.create=true --set controller.service.type=NodePort --set controller.service.nodePorts.http=32080 --set controller.service.nodePorts.https=32443 --set controller.extraArgs."enable-ssl-passthrough=true"
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
server: https://my-cluster-domain.com:9345
token: [token from /var/lib/rancher/rke2/server/node-token on server node 1]
EOF

curl -sfL https://get.rke2.io | INSTALL_RKE2_TYPE="agent" sh -
systemctl enable --now rke2-agent.service
```

## AWS Load Balancer Controller

```
# reference: https://aws.amazon.com/blogs/containers/exposing-kubernetes-applications-part-3-nginx-ingress-controller/

# download iam policy
$ curl -o iam-policy.json https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/v2.4.7/docs/install/iam_policy.json

$ aws iam create-policy \
    --policy-name AWSLoadBalancerControllerIAMPolicy \
    --policy-document file://iam-policy.json

# attach policy to role attached on instances cluster - manual but can be automated
# aws load balancer controller
$ helm repo add eks https://aws.github.io/eks-charts

# install cert-manager, go to cert-manager folder to read installation in README.md
# install targetgroupbinding crds
$ kubectl apply -k "github.com/aws/eks-charts/stable/aws-load-balancer-controller//crds?ref=master" --kubeconfig capi-cluster.kubeconfig
# if not working the command above, use:
$ kubectl apply -f crds.yaml --kubeconfig capi-cluster.kubeconfig

# install aws load balancer controller

$ helm upgrade -i aws-load-balancer-controller eks/aws-load-balancer-controller -n kube-system --set clusterName=capi-cluster --kubeconfig capi-cluster.kubeconfig

# example using aws load controller

$ SERVICE_NAME=first SERVICE_TYPE=NodePort NS=apps envsubst < aws-examples/deploy-using-alb.yaml | kubectl --kubeconfig capi-cluster.kubeconfig  apply -f -
$ SERVICE_NAME=second SERVICE_TYPE=NodePort NS=apps envsubst < aws-examples/deploy-using-alb.yaml | kubectl--kubeconfig capi-cluster.kubeconfig  apply -f -
$ SERVICE_NAME=error SERVICE_TYPE=NodePort NS=apps envsubst < aws-examples/deploy-using-alb.yaml | kubectl --kubeconfig capi-cluster.kubeconfig  apply -f -
$ SERVICE_NAME=first SERVICE_TYPE=NodePort NS=apps envsubst < aws-examples/ingress-alb.yaml  | kubectl --kubeconfig rke2.yaml apply -f -

$ kubectl logs -n kube-system --tail -1 -l app.kubernetes.io/name=aws-load-balancer-controller --kubeconfig capi-cluster.kubeconfig
```
