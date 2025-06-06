```sh

export OPENAI_API_KEY="your-api-key-here"
# Download/run the install script
curl https://raw.githubusercontent.com/kagent-dev/kagent/refs/heads/main/scripts/get-kagent | bash

kagent install

kubectl port-forward -n kagent service/kagent 8082:80

kubectl apply -f andresanaya21/kagent/first-agent.yaml
kubectl apply -f andresanaya21/kagent/mcp-server.yaml

```
