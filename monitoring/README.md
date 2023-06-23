# Tobs:
---------

# helm repo add timescale https://charts.timescale.com/
# helm repo update

# prometheus, grafana, altermanager:
-------------------------------------
# https://github.com/prometheus-community/helm-charts/tree/main/charts/kube-prometheus-stack

# helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
# helm repo update

# helm install monitoring prometheus-community/kube-prometheus-stack

# k apply -f ingress-route-web.yaml

# to check the grafana password
# k get secret --namespace monitoring monitoring-grafana -o jsonpath="{.data.admin-password}" | base64 --decode ; echo
