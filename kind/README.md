Kind
----

```sh

# install kind
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.11.1/kind-linux-amd64
chmod +x ./kind
mv ./kind /usr/local/bin/kind

# create configuration file
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
  - role: control-plane
  - role: worker
    extraMounts:
      - hostPath: /path/on/host
        containerPath: /path/in/container
    extraPortMappings:
      - containerPort: 80
        hostPort: 8080
  - role: worker
    extraMounts:
      - hostPath: /path/on/host
        containerPath: /path/in/container
    extraPortMappings:
      - containerPort: 80
        hostPort: 9080

# create a cluster
kind create cluster --config kind-config.yaml

# configure nodes
apiVersion: apps/v1
kind: Deployment
metadata:
  name: worker-deployment
spec:
  replicas: 2
  selector:
    matchLabels:
      app: worker
  template:
    metadata:
      labels:
        app: worker
    spec:
      containers:
      - name: worker-container
        image: your-worker-image
        resources:
          limits:
            cpu: "4"
            memory: "4Gi"
          requests:
            cpu: "4"
            memory: "4Gi"

# apply deployment

kubectl apply -f worker-deployment.yaml


# install longhorn
kubectl apply -f https://raw.githubusercontent.com/longhorn/longhorn/v1.2.4/deploy/longhorn.yaml


```


