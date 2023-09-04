```
# aws cli

curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# clusterctl

curl -L https://github.com/kubernetes-sigs/cluster-api/releases/download/v1.5.0/clusterctl-linux-amd64 -o clusterctl

sudo install -o root -g root -m 0755 clusterctl /usr/local/bin/clusterctl

clusterctl version
```

```
# clusterawsadm 

curl -L https://github.com/kubernetes-sigs/cluster-api-provider-aws/releases/download/v2.2.1/clusterawsadm-linux-amd64 -o clusterawsadm

chmod +x clusterawsadm

install clusterawsadm /usr/local/bin/clusterawsadm

export AWS_REGION=eu-west-3 # This is used to help encode your environment variables
export AWS_ACCESS_KEY_ID=<your-access-key>
export AWS_SECRET_ACCESS_KEY=<your-secret-access-key>
export AWS_SESSION_TOKEN=<session-token> # If you are using Multi-Factor Auth.

# The clusterawsadm utility takes the credentials that you set as environment
# variables and uses them to create a CloudFormation stack in your AWS account
# with the correct IAM resources.
clusterawsadm bootstrap iam create-cloudformation-stack --region eu-west-3

# Create the base64 encoded credentials using clusterawsadm.
# This command uses your environment variables and encodes
# them in a value to be stored in a Kubernetes Secret.
export AWS_B64ENCODED_CREDENTIALS=$(clusterawsadm bootstrap credentials encode-as-profile)

# Finally, initialize the management cluster
clusterctl init --infrastructure aws
```

```
# export variables

export AWS_REGION=eu-west-3
export AWS_SSH_KEY_NAME=discovery-ec2
# Select instance types
export AWS_CONTROL_PLANE_MACHINE_TYPE=t3.large
export AWS_NODE_MACHINE_TYPE=t3.large

# generate cluster
clusterctl generate cluster capi-cluster \
  --kubernetes-version v1.27.3 \
  --control-plane-machine-count=1 \
  --worker-machine-count=1 \
  > capi-cluster.yaml

# create cluster
kubectl apply -f capi-cluster.yaml

kubectl get cluster

clusterctl describe cluster capi-cluster --v 10
clusterctl describe cluster capi-cluster --echo
clusterctl describe cluster capi-cluster --show-conditions KubeadmControlPlane

kubectl get kubeadmcontrolplane
kubectl describe kubeadmconfigtemplate
kubectl get machine
kubectl get machinedeployment
ktail -n capi-kubeadm-bootstrap-system -sT
ktail -n capi-kubeadm-control-plane-system -sT
ktail -n capi-system -sT

clusterctl get kubeconfig capi-cluster > capi-cluster.kubeconfig

# get ip bastion host - if configured -
kubectl get awscluster


```

```
# calico
kubectl --kubeconfig=./capi-cluster.kubeconfig \
  apply -f https://raw.githubusercontent.com/projectcalico/calico/v3.24.1/manifests/calico.yaml

kubectl taint nodes --all node.cluster.x-k8s.io/uninitialized- --kubeconfig ./capi-cluster.kubeconfig
kubectl taint nodes --all node.cloudprovider.kubernetes.io/uninitialized- --kubeconfig ./capi-cluster.kubeconfig
kubectl --kubeconfig=./capi-cluster.kubeconfig get nodes
```
```
# delete cluster
# before delete, firstly ensure ingress controller deleted in cluster
kubectl delete cluster capi-cluster

```

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

# install aws load balancer controller

$ helm upgrade -i aws-load-balancer-controller eks/aws-load-balancer-controller -n kube-system --set clusterName=capi-cluster --kubeconfig capi-cluster.kubeconfig

# install nginx ingress controller, modify the health check of https

$ helm upgrade -i ingress-nginx ingress-nginx/ingress-nginx \
    --version 4.2.3 \
    --namespace kube-system \
    --values values.yaml --kubeconfig capi-cluster.kubeconfig

 # example using aws load balancer

$ SERVICE_NAME=first NS=apps envsubst < deploy-using-alb.yaml | kubectl --kubeconfig capi-cluster.kubeconfig  apply -f -
$ SERVICE_NAME=second NS=apps envsubst < deploy-using-alb.yaml | kubectl--kubeconfig capi-cluster.kubeconfig  apply -f -
$ SERVICE_NAME=error NS=apps envsubst < deploy-using-alb.yaml | kubectl --kubeconfig capi-cluster.kubeconfig  apply -f -
$ NS=apps envsubst < ingress.yaml | kubectl --kubeconfig capi-cluster.kubeconfig apply -f -
$ export NLB_URL=$(kubectl get -n kube-system service/ingress-nginx-controller \
    -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

$ kubectl logs -n kube-system --tail -1 -l app.kubernetes.io/name=aws-load-balancer-controller --kubeconfig capi-cluster.kubeconfig
```