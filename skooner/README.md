kubectl apply -f https://raw.githubusercontent.com/skooner-k8s/skooner/master/kubernetes-skooner.yaml
kubectl apply -f ingress-route-dashboard-http.yaml
kubectl create serviceaccount skooner-sa -n kube-system
kubectl create clusterrolebinding skooner-sa --clusterrole=cluster-admin --serviceaccount=kube-system:skooner-sa
kubectl create token skooner-sa -n kube-system
# You will get an output with the token. type this one in the web http://monitor.sandbox.com to get access in the cluster