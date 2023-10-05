locals {

  list_ec2 = [ for v in values(module.ec2_instance): v.id ]
  list_private_ips = [ for p in values(var.multiple_instances): p.private_ip ]
  account_id          = data.aws_caller_identity.current.account_id
  region              = data.aws_region.current.name
  azs      = slice(data.aws_availability_zones.available.names, 0, 3)
  username = data.aws_caller_identity.current.user_id
  ami = "ami-05b5a865c3579bbc4"
  instance_type = "c6id.2xlarge"
  outpost_arn = "arn:aws:outposts:eu-west-3:050107717205:outpost/op-066d526775d892a1f"
  
}