KubeAI
----

```sh
kind create cluster -n kubeai # OR: minikube start

helm repo add kubeai https://www.kubeai.org
helm repo update
helm install kubeai kubeai/kubeai --wait --timeout 10m --kubeconfig kubeai.kubeconfig

cat <<EOF > kubeai-models.yaml
catalog:
  dpsek-r1:
    enabled: true
    features: [TextGeneration]
    url: 'ollama://deepseek-r1:1.5b'
    engine: OLlama
    minReplicas: 1
    resourceProfile: 'cpu:1'
  gemma2-2b-cpu:
    enabled: true
    minReplicas: 1
    resourceProfile: 'cpu:1'
#  qwen2-500m-cpu:
#    enabled: true
#  nomic-embed-text-cpu:
#    enabled: true
EOF

helm upgrade --install kubeai-models kubeai/models -f ./kubeai-models.yaml --kubeconfig kubeai.kubeconfig


kubectl get models dpsek-r1 --kubeconfig kubeai.kubeconfig 

k --kubeconfig kind-kubeconfig.yaml port-forward svc/open-webui 8000:80 

[Lambda Example](https://docs.lambda.ai/education/large-language-models/kubeai-hermes-3/)
```

LangChain using KubeAI
----------
```sh

cat <<EOF > models-helm-values.yaml
catalog:
  gemma2-2b-cpu:
    enabled: true
    minReplicas: 1
EOF


helm upgrade --install kubeai-models kubeai/models \
    -f ./models-helm-values.yaml --kubeconfig kubeai.kubeconfig


pip install langchain_openai

kubectl port-forward svc/kubeai 8100:80

python test-langchain.py

```

LangTrace using KubeAI
----------

```sh
helm repo add langtrace https://Scale3-Labs.github.io/langtrace-helm-chart 
helm repo update
helm install langtrace langtrace/langtrace --kubeconfig kubeai.kubeconfig

cat <<EOF > kubeai-models.yaml
catalog:
  gemma2-2b-cpu:
    enabled: true
    minReplicas: 1
EOF

helm install kubeai-models kubeai/models \
    -f ./kubeai-models.yaml --kubeconfig kubeai.kubeconfig

python3 -m venv .venv
source .venv/bin/activate
pip install langtrace-python-sdk openai


k --kubeconfig kind-kubeconfig.yaml port-forward svc/langtrace-svc 3000:3000
# ADMIN_EMAIL
user: admin@langtrace.ai
# ADMIN_PASSWORD
pwd: langtraceadminpw

# create a project and get the API keys for your langtrace project.

# execute 
python3 langtrace-example.py
```