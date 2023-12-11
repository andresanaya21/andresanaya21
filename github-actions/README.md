# GitHub Actions

```
# https://www.velotio.com/engineering-blog/how-to-deploy-github-actions-self-hosted-runners-on-kubernetes

$ export GITHUB_TOKEN=XXXxxxXXXxxxxXYAVNa 
$ kubectl create ns actions-runner-system
$ kubectl create secret generic controller-manager  -n actions-runner-system \
--from-literal=github_token=${GITHUB_TOKEN}

$ helm repo add actions-runner-controller https://actions-runner-controller.github.io/actions-runner-controller
$ helm repo update
$ helm upgrade --install --namespace actions-runner-system \
--create-namespace --wait actions-runner-controller \
actions-runner-controller/actions-runner-controller --set \
syncPeriod=1m

$ kubectl --namespace actions-runner-system get all

# runner deployment
$ kubectl create -f runner.yaml
$ kubectl get pod -n actions-runner-system | grep -i "k8s-action-runner"

```
