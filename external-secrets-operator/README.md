# External Secrets
```
$ helm repo add external-secrets https://charts.external-secrets.io

helm install external-secrets \
   external-secrets/external-secrets \
    -n external-secrets \
    --create-namespace \
   --set installCRDs=true

# KEYID AND SECRETKEY are the credentials of the aws user. This user must be rigt permissions
# to list secrets/parameter store. "secretsmanager:ListSecrets" "secretsmanager:GetSecretValue"
# https://blog.container-solutions.com/tutorial-how-to-set-external-secrets-with-aws

$ echo -n 'AKIA2KIFHGHS' > ./access-key
$ echo -n '1NL2ipVpUk7rFghjfshshrhnd' > ./secret-access-key
kubectl create secret generic awssm-secret --from-file=./access-key --from-file=./secret-access-key

# create the parameter store secret in aws
$ aws ssm put-parameter --name "/oneke/user" --value "admin" --type "String" --tier "Standard" --region "eu-west-3"

# create the secret manager in aws
$ aws secretsmanager create-secret --name "oneke/creds" --secret-string '{"USER":"adminsecret", "PASSWORD":"123secrect"}' --region "eu-west-3"

# create the parameter store/secret manager in aws

## creates the secretStore to use secrets in parameter store
$  k apply -f secret-store-parameter-store.yaml
$ k get secretstore

## creates the secretStore to use secrets in secrets manager aws
$ k apply -f secret-store-secret-manager.yaml
$ k get externalsecret

## creates the externalSecret to use in parameter store aws
$ k apply -f external-secret-parameter-store.yaml

## creates the externalSecret to use in secret manager
$ k apply -f external-secret-secret-manager.yaml

# create a pod
$ k apply -f pod.yaml
```
