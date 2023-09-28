variable "instance_names" {
    type = list(string)
    description = "list of instances names"
#    default = ["rke2-master-0","rk2-master-1","rke2-worker-0","rke2-worker-1"]
    default = ["rke2-master-0","rk2-master-1"]
  
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

#variable "multiple_instances" {
#    type = map(object({
#      private_ip = string
#    }))
#    description = "instances"
#    default = {
#        rke2-master-0 = {
#            private_ip = "10.0.5.10"
#        }
#        rke2-worker-0 = {
#            private_ip = "10.0.5.11"
#        }
#    }
#}
variable "tags" {
    type = map(string)
    description = "set of tags"
    default = {
      "owner" = "andres",
      "region" = "outpost"
    }
  
}