Cluster API and Vcluster

- Using RKE2 as management cluster. 

```
# install cluster-api
curl -L https://github.com/kubernetes-sigs/cluster-api/releases/download/v1.4.4/clusterctl-linux-amd64 -o clusterctl
sudo install -o root -g root -m 0755 clusterctl /usr/local/bin/clusterctl
clusterctl version

# install vcluster
curl -L -o vcluster "https://github.com/loft-sh/vcluster/releases/latest/download/vcluster-linux-amd64" && sudo install -c -m 0755 vcluster /usr/local/bin && rm -f vcluster

# using provider vcluster
clusterctl init --infrastructure vcluster

# export variables

git clone https://github.com/loft-sh/vcluster.git
export CLUSTER_NAME=my-cluster
export CLUSTER_NAMESPACE=vcluster
export KUBERNETES_VERSION=1.27.3
#choosing default distro and using loadbalacer type to virtual cluster
#export HELM_VALUES="service:\n  type: LoadBalancer"
# choose k8s distro doing advanced options but it doesn't work when try to generate cluster
export HELM_VALUES=$(cat vcluster/charts/k8s/values.yaml | python3 -c 'import yaml,sys; print(yaml.dump(sys.stdin.read()).strip()[1:-1])')

kubectl create namespace ${CLUSTER_NAMESPACE}
clusterctl generate cluster ${CLUSTER_NAME} \
    --infrastructure vcluster \
    --kubernetes-version ${KUBERNETES_VERSION} \
    --target-namespace ${CLUSTER_NAMESPACE} | kubectl apply -f -

# the creating of cluster-api takes less more than 1 minute (using the default setup, it means
# k3s and no replicas nodes, no ingress, no pvc...)

kubectl get cluster -n vcluster
clusterctl describe cluster my-cluster -n vcluster
kubectl -n vcluster get pods

# get kubeconfig
clusterctl get kubeconfig my-cluster -n vcluster > my-cluster.kubeconfig
kubectl get pods -A--kubeconfig my-cluster.kubeconfig

# delete cluster
kubectl delete cluster my-cluster -n vcluster
```