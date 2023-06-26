# get the latest version or change to a specific version
VERSION=$(curl --silent "https://api.github.com/repos/argoproj-labs/argocd-autopilot/releases/latest" | grep '"tag_name"' | sed -E 's/.*"([^"]+)".*/\1/')

# download and extract the binary
curl -L --output - https://github.com/argoproj-labs/argocd-autopilot/releases/download/$VERSION/argocd-autopilot-linux-amd64.tar.gz | tar zx

# move the binary to your $PATH
mv ./argocd-autopilot-* /usr/local/bin/argocd-autopilot

# check the installation
argocd-autopilot version

# export GIT TOKEN (create the new one in github repo)
export GIT_TOKEN=ghp_PcZ...IP0
export GIT_REPO=https://github.com/andresanaya21/deployment-apps

# create repo bootstrap, it creates a folders in GIT_REPO to argocd autopilot and gitops
argocd-autopilot repo bootstrap --provider github 

# create project to the app
argocd-autopilot project create argocd-ingress

# create app
argocd-autopilot app create argocd-ingress --app github.com/andresanaya21/andresanaya21/argocd -p argocd-ingress --type kustomize