# ArgoCD AutoPilot

```
# get the latest version or change to a specific version
VERSION=$(curl --silent "https://api.github.com/repos/argoproj-labs/argocd-autopilot/releases/latest" | grep '"tag_name"' | sed -E 's/.*"([^"]+)".*/\1/')

# download and extract the binary
curl -L --output - https://github.com/argoproj-labs/argocd-autopilot/releases/download/$VERSION/argocd-autopilot-linux-amd64.tar.gz | tar zx

# move the binary to your $PATH
mv ./argocd-autopilot-* /usr/local/bin/argocd-autopilot

# check the installation
argocd-autopilot version

# create valid token and export - https://argocd-autopilot.readthedocs.io/en/stable/Getting-Started/
export GIT_TOKEN=ghp_PcZ...IP0

# export git repo
export GIT_REPO=https://github.com/andresanaya21/provisioning.git

# create bootstrap
argocd-autopilot repo bootstrap

# port-forward
INFO argocd initialized. password: pfrDVRJZtHYZKzBv 
INFO run:

    kubectl port-forward -n argocd svc/argocd-server 8080:80

# create ingress to argocd-autopilot in repo provisioning, follow next steps

# /bootstrap/argo-cd/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
namespace: argocd
resources:
- github.com/argoproj-labs/argocd-autopilot/manifests/base?ref=v0.4.10
# Added new resources:
- ./ingress.yaml
- ./argogrpc.service.yaml

```

## creating app

```
# create project

export GIT_TOKEN=<YOUR_TOKEN>
export GIT_REPO=https://github.com/andresanaya21/provisioning.git

argocd-autopilot project create cluster-addons

# craete app
argocd-autopilot app create cert-manager --app github.com/andresanaya21/andresanaya21/cert-manager/ -p cluster-addons --type kustomize

# if no used kustomize, type dir will execute all manifiest in the folder. You can exclude files and folder using config.json (provisioning repo)
argocd-autopilot app create cert-manager --app github.com/andresanaya21/andresanaya21/cert-manager/ -p cluster-addons --type dir

```

## uninstall argocd-autopilot
```
argocd-autopilot repo uninstall
```