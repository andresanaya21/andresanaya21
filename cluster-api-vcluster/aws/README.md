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

kubectl get kubeadmcontrolplane

clusterctl get kubeconfig capi-cluster > capi-cluster.kubeconfig

```

## calico

```
kubectl --kubeconfig=./capi-cluster.kubeconfig \
  apply -f https://raw.githubusercontent.com/projectcalico/calico/v3.24.1/manifests/calico.yaml

kubectl --kubeconfig=./capi-cluster.kubeconfig get nodes

```

## delete cluster
```
kubectl delete cluster capi-cluster

```