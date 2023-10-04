# Deploy RKE2 using terraform and ansible

## Dependencies
- ansible
- terraform
- Outpost

## Steps:
1. Deploy infraestructure using terraform:
2. Deploy RKE2 software in ec2 instances

### 1. Deploy infraestructure using terraform:
- Resources to deploy:
  - EC2 (instances, network load balancer, target groups, listeners)
  - VPC (internet gateway, nat gateway, security groups, rules, subnets)

#### Procedure

- modify the `tf-rke2/vars.tf`. `multiple_instances` variable is a object dict. If you have:

```
        rke2-master-0 = {
            private_ip = "10.0.5.10"
        }
        rke2-master-1 = {
            private_ip = "10.0.5.11"
        }
        rke2-worker-0 = {
            private_ip = "10.0.5.12"
        }
```

The code above means you will create three ec2 instances with name: `rke2-master-0, rke2-master-1, rke2-worker-0`.  The `privat_ip` dependes on the `locals.vpc_cidr` and the `aws_subnet.tf_outpost_subnet_lni`. These private ips will be atteched as internal subnet created in aws Outpost.

- Provides aws credentials in `tf-rke2/provider.tf`
- Create deployment using terraform

```
$ terraform init
$ terraform plan
$ terraform apply
```

### 2. Deploy RKE2 software in ec2 instances

#### Prodedure

- Modify the `ansible/inventory` file including the ansible host to each group
- Modify the `ansible/common_vars.yml` file including the DNS to nlb
- Execute

```
$ ansbile-playbook deploy.yaml -i inventory
```