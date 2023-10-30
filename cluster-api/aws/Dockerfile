FROM ubuntu:22.04

SHELL [ "/bin/bash", "-c" ]
ENV VERSION_ARGOCD_AUTOPILOT=v0.4.17

RUN apt update && apt install wget curl -y
RUN echo "### install yq ###" 
RUN wget -qO /usr/local/bin/yq https://github.com/mikefarah/yq/releases/latest/download/yq_linux_amd64
RUN chmod a+x /usr/local/bin/yq && yq --version

RUN echo "### install jq ###"
RUN apt install jq -y && jq --version

RUN echo "## install gh ###"
RUN type -p curl >/dev/null || ( apt update &&  apt install curl -y)
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg |  dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
    && chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" |  tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
    && apt update \
    && apt install gh -y

RUN echo "### get the latest version or change to a specific version ###"
#RUN VERSION=$(curl --silent "https://api.github.com/repos/argoproj-labs/argocd-autopilot/releases/latest" | grep '"tag_name"' | sed -E 's/.*"([^"]+)".*/\1/')
RUN echo "### download and extract the binary ###"
RUN curl -L --output - https://github.com/argoproj-labs/argocd-autopilot/releases/download/$VERSION_ARGOCD_AUTOPILOT/argocd-autopilot-linux-amd64.tar.gz | tar zx
RUN echo "### move the binary to your $PATH ###"
RUN mv ./argocd-autopilot-* /usr/local/bin/argocd-autopilot && argocd-autopilot version

RUN echo "### argocd ###"
RUN curl -sSL -o argocd-linux-amd64 https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
RUN install -m 555 argocd-linux-amd64 /usr/local/bin/argocd && rm argocd-linux-amd64
