# Deploy RKE2 using terraform and ansible

## Dependencies
- ansible
- terraform
- AWS Outpost

## Steps:
1. Deploy infrastructure using terraform
2. Deploy RKE2 software in ec2 instances

### 1. Deploy infraestructure using terraform:
- Resources to deploy:
  - EC2 (instances, network load balancer, target groups, listeners)
  - VPC (internet gateway, nat gateway, security groups, rules, subnets)

#### Procedure

- modify the `tf-rke2/vars.tf`. `masters` and `workers` variables are a object dict. If you have:

```
# masters
    rke2-master-0 = {
        private_ip = "10.0.5.10"
    }
    rke2-master-1 = {
        private_ip = "10.0.5.11"
    }
    rke2-worker-0 = {
        private_ip = "10.0.5.12"
    }

# workers
    "rke2-worker-0" = {
      private_ip = "10.0.5.12"
    }
    "rke2-worker-1" = {
      private_ip = "10.0.5.13"
    }
```

Then the code above means you will create four ec2 instances with name: `rke2-master-0, rke2-master-1, rke2-worker-0, rke2-worker-1`.  The `private_ip` depends on the `var.vpc_cidr` and the `var.cidr_block_snet_op_local`. These private ips will be atteched as internal subnet created in AWS Outpost.

- Provides AWS credentials in `tf-rke2/provider.tf`
- Create deployment using terraform

```
$ terraform init
$ terraform plan
$ terraform apply
```

### 2. Deploy RKE2 software in ec2 instances

- RKE2 by default will install however you can disable them in the `/etc/rancher/rke2/config.yaml`:
  - ingress-nginx
  - rke2-canal

#### Prodedure

- Modify the `ansible/inventory` file including the ansible host to each group
- Modify the `ansible/common_vars.yml` file including the DNS to nlb
- Execute

```
$ ansbile-playbook deploy.yaml -i inventory
```