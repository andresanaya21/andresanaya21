locals {
  multiple_instances = {
    rke2-master-0 = {
        private_ip = "10.0.5.10"
    }
    rke2-master-1 = {
        private_ip = "10.0.5.11"
    }
  }

  list_ec2 = [ for v in values(module.ec2_instance): v.id ]
  list_private_ips = [ for p in values(local.multiple_instances): p.private_ip ]
#  list_private_ips = [ for p in values(var.multiple_instances): p.private_ip ]
}
