# External Secrets
```
# helm repo add external-secrets https://charts.external-secrets.io

helm install external-secrets \
   external-secrets/external-secrets \
    -n external-secrets \
    --create-namespace \
   --set installCRDs=true

# echo -n 'KEYID' > ./access-key
echo -n 'SECRETKEY' > ./secret-access-key
kubectl create secret generic awssm-secret --from-file=./access-key --from-file=./secret-access-key

# create the parameter store/secret manager in aws

#  k apply -f secret-store-parameter-store.yaml

# k apply -f secret-store-secret-manager.yaml

# k apply -f external-secret-parameter-store.yaml

# k apply -f external-secret-secret-manager.yaml

# k apply -f pod.yaml
```
