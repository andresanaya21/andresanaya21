```
kubectl apply -f https://raw.githubusercontent.com/skooner-k8s/skooner/master/kubernetes-skooner.yaml
kubectl apply -f ingress-route-dashboard-http.yaml
kubectl create serviceaccount skooner-sa -n kube-system
kubectl create clusterrolebinding skooner-sa --clusterrole=cluster-admin --serviceaccount=kube-system:skooner-sa
kubectl create token skooner-sa -n kube-system

# You will get an output with the token. type this one in the web http://monitor.sandbox.com to get access in the cluster

# troubleshoot
# if skooner cannot open logs. Execute in all nodes the next commands:

sudo sysctl -w fs.inotify.max_user_watches=2099999999
sudo sysctl -w fs.inotify.max_user_instances=2099999999
sudo sysctl -w fs.inotify.max_queued_events=2099999999
```
