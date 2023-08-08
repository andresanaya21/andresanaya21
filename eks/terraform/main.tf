provider "kubernetes" {
  host                   = module.cluster.endpoint
  cluster_ca_certificate = base64decode(module.cluster.kubeconfig_certificate_authority_data)

  exec {
    api_version = "client.authentication.k8s.io/v1beta1"
    command     = "aws"
    # This requires the awscli to be installed locally where Terraform is executed
    args = ["eks", "get-token", "--cluster-name", var.cluster_name]
  }
}

provider "helm" {
  kubernetes {
    host                   = module.cluster.endpoint
    cluster_ca_certificate = base64decode(module.cluster.kubeconfig_certificate_authority_data)

    exec {
      api_version = "client.authentication.k8s.io/v1beta1"
      command     = "aws"
      # This requires the awscli to be installed locally where Terraform is executed
      args = ["eks", "get-token", "--cluster-name", var.cluster_name]
    }
  }
}

module "network" {
  source = "./modules/networking"

  vpc_name       = "main"
  vpc_cidr_block = "10.0.0.0/16"

  public_subnets = {
    "eu-west-1a" = "10.0.1.0/24"
    "eu-west-1b" = "10.0.2.0/24"
    "eu-west-1c" = "10.0.3.0/24"
  }

  private_subnets = {
    "eu-west-1a" = "10.0.11.0/24"
    "eu-west-1b" = "10.0.12.0/24"
    "eu-west-1c" = "10.0.13.0/24"
  }
}

module "cluster" {
  source = "./modules/eks"

  cluster_name      = var.cluster_name
  nodegroup_name    = var.nodegroup_name
  vpc_id            = module.network.vpc_id
  worker_subnet_ids = module.network.private_subnet_ids
}

module "eks_blueprints_addons" {
  source = "aws-ia/eks-blueprints-addons/aws"
  cluster_name = var.cluster_name
  cluster_endpoint  = module.cluster.endpoint
  cluster_version   = module.cluster.version
  oidc_provider_arn = module.cluster.oidc_provider_arn
  eks_addons = {
    aws-ebs-csi-driver = {
    most_recent = true
    }
    coredns = {
      most_recent = true
    }
    vpc-cni = {
      most_recent = true
    }
    kube-proxy = {
      most_recent = true
    }
  }
  
  enable_kube_prometheus_stack           = true

  tags = {
    Owner = "andres"
  }
}