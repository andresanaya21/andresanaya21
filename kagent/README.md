```sh
# reference: https://medium.com/techbeatly/integrating-kagent-and-ollama-bringing-agentic-ai-closer-to-kubernetes-995f0b1f6134

sudo kind create cluster -n kagent-ollama
sudo kind get kubeconfig -n kagent-ollama

# git clone
git clone https://github.com/mysticrenji/kagent-llm-integration

# create namespaces
kubectl create namespace ollama-apps
kubectl create namespace kagent

# install Ollama Operators CRDs
kubectl apply --server-side=true -f https://raw.githubusercontent.com/nekomeowww/ollama-operator/v0.10.1/dist/install.yaml

# deploy ollama models
kubectl apply -f kagent-llm-integration/ollama-operator/models/orca-mini.yaml
kubectl apply -f kagent-llm-integration/ollama-operator/models/hermes2.yaml
kubectl apply -f kagent-llm-integration/ollama-operator/models/models/llama3.2.yaml


# install kagent
export OPENAI_API_KEY="your-api-key-here"

## First Option: Download/run the install script
curl https://raw.githubusercontent.com/kagent-dev/kagent/refs/heads/main/scripts/get-kagent | bash

kagent install

kubectl port-forward -n kagent service/kagent 8082:80

## Second Option
helm install kagent-crds oci://ghcr.io/kagent-dev/kagent/helm/kagent-crds --namespace kagent --create-namespace
helm install kagent oci://ghcr.io/kagent-dev/kagent/helm/kagent --namespace kagent --values kagent-llm-integration/kagent/values.yaml

kubectl port-forward svc/kagent -n kagent 59847:80

# using kagent with mcp
kubectl apply -f andresanaya21/kagent/first-agent.yaml
kubectl apply -f andresanaya21/kagent/mcp-server.yaml

```
