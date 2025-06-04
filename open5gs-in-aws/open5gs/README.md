Open5gs
--------

```sh
# deploy open5gs
helm install open5gs oci://registry-1.docker.io/gradiantcharts/open5gs --values open5gs-values.yaml -n open5gs --create-namespace
kubectl -n open5gs delete svc open5gs-amf-ngap && kubectl apply -f open5gs-amf-ngap.yaml 
kubectl -n open5gs delete svc open5gs-upf-gtpu && kubectl apply -f open5gs-upf-gtpu.yaml 
kubectl -n open5gs delete svc open5gs-webui && kubectl apply -f open5gs-webui.yaml 

kubectl apply -f skoopbundle.yaml

kubectl -n kubeskoop get pods -o wide

curl http://ec2-15-236-113-156.eu-west-3.compute.amazonaws.com:30080
admin/kubeskoop
```