# reference
https://gist.github.com/jakexks/c1de8238cbee247333f8c274dc0d6f0f

# helm repo add jetstack https://charts.jetstack.io

# helm repo update 
 
# helm install \
  cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --create-namespace \
  --version v1.12.0 \
   --set installCRDs=true

# kubectl apply -f cluster-issuer.yaml
