## clusterctl
```
curl -L https://github.com/kubernetes-sigs/cluster-api/releases/download/v1.5.0/clusterctl-linux-amd64 -o clusterctl

sudo install -o root -g root -m 0755 clusterctl /usr/local/bin/clusterctl

clusterctl version```


## clusterawsadm 
```
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
clusterawsadm bootstrap iam create-cloudformation-stack

# Create the base64 encoded credentials using clusterawsadm.
# This command uses your environment variables and encodes
# them in a value to be stored in a Kubernetes Secret.
export AWS_B64ENCODED_CREDENTIALS=$(clusterawsadm bootstrap credentials encode-as-profile)

# Finally, initialize the management cluster
clusterctl init --infrastructure aws
```

```
export AWS_REGION=eu-west-3
export AWS_SSH_KEY_NAME=discovery-ec2
# Select instance types
export AWS_CONTROL_PLANE_MACHINE_TYPE=t3.large
export AWS_NODE_MACHINE_TYPE=t3.large

clusterctl generate cluster capi-cluster \
  --kubernetes-version v1.27.3 \
  --control-plane-machine-count=1 \
  --worker-machine-count=1 \
  > capi-cluster.yaml

kubectl apply -f capi-cluster.yaml

kubectl get cluster

clusterctl describe cluster capi-cluster
clusterctl describe cluster capi-cluster --echo
clusterctl describe cluster capi-cluster --show-conditions KubeadmControlPlane

kubectl get kubeadmcontrolplane
kubectl describe kubeadmconfigtemplate
kubectl get machine

clusterctl get kubeconfig capi-cluster > capi-cluster.kubeconfig

kubectl get machine

```

## calico

```
kubectl --kubeconfig=./capi-cluster.kubeconfig \
  apply -f https://raw.githubusercontent.com/projectcalico/calico/v3.24.1/manifests/calico.yaml

kubectl taint nodes --all node.cluster.x-k8s.io/uninitialized- --kubeconfig ./capi-cluster.kubeconfig
kubectl taint nodes --all node.cloudprovider.kubernetes.io/uninitialized- --kubeconfig ./capi-cluster.kubeconfig
kubectl --kubeconfig=./capi-cluster.kubeconfig get nodes
```

## delete cluster
```
kubectl delete cluster capi-cluster

```


```
$ curl -o iam-policy.json https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/v2.4.7/docs/install/iam_policy.json

$ aws iam create-policy \
    --policy-name AWSLoadBalancerControllerIAMPolicy \
    --policy-document file://iam-policy.json

# attach policy to role attached on instances cluster


# aws load balancer controller

$ helm repo add eks https://aws.github.io/eks-charts

# install cert-manager

# install targetgroupbinding crds
$ kubectl apply -k "github.com/aws/eks-charts/stable/aws-load-balancer-controller//crds?ref=master"

# install aws load balancer controller

$ helm upgrade -i aws-load-balancer-controller eks/aws-load-balancer-controller -n kube-system --set clusterName=capi-cluster

```