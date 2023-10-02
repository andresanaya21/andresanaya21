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
    description = "instances"
    default = {
        rke2-master-0 = {
            private_ip = "10.0.5.10"
        }
        rke2-master-1 = {
            private_ip = "10.0.5.11"
        }
    }
}
variable "tags" {
    type = map(string)
    description = "set of tags"
    default = {
      "owner" = "andres",
      "region" = "outpost"
    }
  
}