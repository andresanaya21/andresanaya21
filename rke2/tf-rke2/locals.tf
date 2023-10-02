locals {

  list_ec2 = [ for v in values(module.ec2_instance): v.id ]
  list_private_ips = [ for p in values(var.multiple_instances): p.private_ip ]
  
}
