# Kustomization

## tree of folders:

```
tree
.
├── base
│   ├── kustomization.yaml
│   └── deployment.yaml
│   └── configmap.yaml
└── overlays
    ├── dev
    │   ├── kustomization.yaml
    │   └── patch-pod.yaml
    └── prod
        ├── kustomization.yaml
        └── patch-pod.yaml
```
`base - `  Used by all resources k8s (deployments, configmap...).  
`overlays -` Used for specific environments (dev, prod, sandbox...)

```
# execution
$ kubectl apply -k kustomize/base

# or
$ kustomize build
```

```
# set values using CLI
kustomize edit set image app=app:$(git rev-parse --short HEAD)

images:
- name: app
  newName: app
  newTag: 68b4c528

# kustomize/overlays/prod
$ kustomize edit add secret another-app --from-literal=db-password=ohmypassword

```

## setting variables dynamically

```
IMAGE_TAG=$(git rev-parse HEAD)
sed "s/IMAGE_TAG/$/g" \
    overlays/prod/kustomization.template.yaml \
    > overlays/prod/kustomization.yaml
```

### using `envsubst`

```
export IMAGE_TAG=$(git rev-parse HEAD)
envsubst < overlays/dev/kustomization.template.yaml > overlays/dev/kustomization.yaml
```

Ref: 
- https://www.innoq.com/en/blog/kustomize-introduction/
- https://polarsquad.com/blog/loading-dynamic-configurations-in-kubernetes-kustomize
