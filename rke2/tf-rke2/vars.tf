variable "instance_names" {
    type = list(string)
    description = "list of instances names"
#    default = ["rke2-master-0","rk2-master-1","rke2-worker-0","rke2-worker-1"]
    default = ["rke2-master-0"]
  
}

variable "instance_type" {
    type = string
    description = "instance type"
    default = "c6id.2xlarge"
  
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

variable "vpc_security_group_ids" {
    type = list(string)
    description = "list of sgs"
    default = [""]
  
}

variable "subnet_id" {
    type = string
    description = "subnet_id (outpost)"
    default = "subnet-0690f473ec5d974e6"
  
}

variable "tags" {
    type = map(string)
    description = "set of tags"
    default = {
      "owner" = "andres",
      "region" = "outpost"
    }
  
}

variable "iam_role_name" {
    type = string
    description = "ssm role name to instance"
    default = "SSMRoleInstance"
  
}

variable "vpc_id" {
    type = string
    description = "vpc id"
    default = "vpc-09dfbdee1025dc45e"
  
}
