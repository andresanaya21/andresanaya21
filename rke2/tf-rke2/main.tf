module "ec2_instance" { 
  source = "terraform-aws-modules/ec2-instance/aws"
  version = "5.5.0"
  
  timeouts = {
    create = "1h30m"
    update = "2h"
    delete = "20m"
  }

  for_each = var.multiple_instances

  ami = local.ami
  name = each.key
  instance_type = local.instance_type
  key_name = var.key_name
  monitoring = var.monitoring
  vpc_security_group_ids = [aws_security_group.rke2_cluster_sgs.id]
  subnet_id = aws_subnet.tf_outpost_subnet.id
  associate_public_ip_address = false
  iam_role_description = "IAM Role to EC2 intances"
  create_iam_instance_profile = true
  iam_role_policies = {
    AmazonSSMManagedInstanceCore = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
  }

  tags = var.tags
}

output "ec2_length" {
  value = length(module.ec2_instance)
  
}

output "ec2_name" {
  value = element(keys(module.ec2_instance),0)
  
}

output "ec2_ami" {
  value = [ for v in values(module.ec2_instance): v.ami ]
  
}

output "private_ips" {
  value = [ for p in values(var.multiple_instances): p.private_ip ]  
}