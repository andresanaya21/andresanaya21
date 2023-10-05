variable "vpc_cidr" {
    type = string
    description = "cird to vpc"
    default = "10.0.0.0/16"
  
}

variable "vpc_name" {
    type = string
    description = "name of vpc"
    default = "tf-vpc-outpost"
  
}

variable "cidr_block_snet_op_region" {
    type = string
    description = "value of the cidr to the subnet created in the outpost. This subnet will be used to connect the instances to region. Please keep in mind the var.vpc_cidr variable"
    default = "10.0.4.0/24"
  
}

variable "cidr_block_snet_op_local" {
    type = string
    description = "value of the cidr to the subnet created in the outpost. This subnet will be used to connect the instances to on-premise. Please keep in mind the var.vpc_cidr variable"
    default = "10.0.5.0/24"
  
}
variable "key_name" {
    type = string
    description = "name of key"
    default = "outpost-key"
  
}

variable "monitoring" {
    type = bool
    description = "true/false enabling monitoring"
    default = true
}

variable "multiple_instances" {
    type = map(object({
      private_ip = string
    }))
    description = "include ec2 instances as the defautl format"
    default = {
        rke2-master-0 = {
            private_ip = "10.0.5.10"
        }
        rke2-master-1 = {
            private_ip = "10.0.5.11"
        }
        rke2-worker-0 = {
            private_ip = "10.0.5.12"
        }
    }
}
variable "tags" {
    type = map(string)
    description = "set of tags"
    default = {
        environment = "Outpost"
    }
  
}