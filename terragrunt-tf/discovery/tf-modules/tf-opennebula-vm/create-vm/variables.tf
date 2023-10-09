variable "endpoint" {
  type    = string
  default = "http://192.168.24.12:2633/RPC2"
}
variable "oneuser" {
  type    = string
  default = "bot"
}
variable "onepasswd" {
  type    = string
  default = "L4bpassword"
}

variable "vm_settings" {
  type    = list(map(string))
  default = [
    {
        name          = ""
        instance_type = ""
        cpu           = ""
        size          = ""
    }  
  ]
}

