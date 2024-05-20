```
# rke2 cluster
$ kubectl --kubeconfig cluster-west.kubeconfig apply -f rke2-calico-config.yaml
$ DATASTORE_TYPE=kubernetes KUBECONFIG=cluster-west.kubeconfig calicoctl create -f cluster-west-pod-svc.yaml
$ DATASTORE_TYPE=kubernetes KUBECONFIG=cluster-east.kubeconfig calicoctl create -f cluster-east-pod-svc.yaml

# subctl - submariner
$ subctl deploy-broker --kubeconfig broker.kubeconfig

$ subctl join --kubeconfig cluster-west.kubeconfig broker-info.subm --clusterid east --check-broker-certificate=false --coredns-custom-configmap=kube-system/rke2-coredns-rke2-coredns --operator-debug --pod-debug

$ subctl join --kubeconfig cluster-east.kubeconfig broker-info.subm --clusterid east --check-broker-certificate=false --coredns-custom-configmap=kube-system/rke2-coredns-rke2-coredns --operator-debug --pod-debug

$ export KUBECONFIG=cluster-west.kubeconfig:cluster-east.kubeconfig
$ subctl verify --context west --tocontext east --only connectivity --verbose

# kubectl

# uninstall

$ subctl uninstall --kubeconfig cluster-west.kubeconfig
$ subectl uninstall --kubeconfig cluster-east.kubeconfig
$ subectl uninstall --kubeconfig broker.kubeconfig

```


## Notas
- service CIDR y cluster CIDR deben ser diferentes en todos los clusteres implicados, para envitar problemas de routing
- usa un broker para concetar los demás clusteres
    - este broker puede estar en un cluster separado o en uno de los clusteres que se desean intercomunicar
- se crea un gateway en los workers de cada cluster, y cada nodo de cada cluster debe estar expuesto en un IP:PORT
  específico. Esto puede ser un contra, aunque subctl acepta que sea un loadbalancer que esté expuesto y luego que
  que los backend sean los nodos
- subctl está integrado con calico cni
- el deployment (pods) se crean en uno de los cluster, luego subctl exporta el service en todos los clusters implicados
  y se puede acceder a ese servicio internamente (con la ip de service) desde cualquier cluster.
- si se crean dos services/deployments en mismo namespace pero en diferentes clusteres. subctl expondrá 
  ambos servicios (ej: nginx-svc - cluster-east, nginx-svc - cluster-west). Y dependiendo de donde provenga (round-robin)
  la petición, subctl escogerá a qué cluster enviar la petición.
- subctl también funciona con stateless and headless services