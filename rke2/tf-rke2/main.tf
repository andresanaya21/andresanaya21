module "ec2_instance" { 
  source = "terraform-aws-modules/ec2-instance/aws"
  version = "5.5.0"
  
  timeouts = {
    create = "1h30m"
    update = "2h"
    delete = "20m"
  }

  for_each = toset(var.instance_names)

  ami = local.ami
  name = each.key
  instance_type = var.instance_type
  key_name = var.key_name
  monitoring = var.monitoring
  vpc_security_group_ids = [aws_security_group.rke2_cluster_sgs.id]
  subnet_id = aws_subnet.tf_outpost_subnet.id
  associate_public_ip_address = false
  iam_role_description = "IAM Role to EC2 intances"
  iam_role_policies = {
    AmazonSSMManagedInstanceCore = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
  }

  tags = var.tags
}