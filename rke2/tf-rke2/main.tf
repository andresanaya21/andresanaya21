resource "aws_iam_policy" "aws_lb_controller" {
  name        = "AWSLoadBalancerControllerIAMPolicy"
  description = "AWS load balancer controller policy"
  policy      = file("./policies/iam-aws-lb-controller.json")
}

resource "aws_iam_policy" "rke2_policy" {
  name        = "AWSRKE2Policy"
  description = "AWS RKE2 cluster policy"
  policy      = file("./policies/iam-rke2-policy.json")
}

module "ec2_instance" { 
  source = "terraform-aws-modules/ec2-instance/aws"
  version = "5.5.0"
  
  timeouts = {
    create = "1h30m"
    update = "2h"
    delete = "20m"
  }

  for_each = var.masters

  ami = local.ami
  name = each.key
  instance_type = "${var.control_plane_edge ? local.instance_type_outpost : local.instance_type_region}"
  key_name = var.key_name
  monitoring = var.monitoring
  vpc_security_group_ids = [aws_security_group.rke2_cluster_sgs.id]
  subnet_id = "${var.control_plane_edge ? aws_subnet.tf_outpost_subnet.id: module.vpc.private_subnets[0]}"
  associate_public_ip_address = false
  iam_role_description = "IAM Role to EC2 intances"
  create_iam_instance_profile = true
  user_data =  <<-EOF
               sudo snap install amazon-ssm-agent --classic
               sudo snap list amazon-ssm-agent
               sudo snap start amazon-ssm-agent
               sudo snap services amazon-ssm-agent
               EOF
  iam_role_policies = {
    AmazonSSMManagedInstanceCore = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
    AWSLoadBalancerControllerIAMPolicy = aws_iam_policy.aws_lb_controller.arn
    AWSRKE2Policy = aws_iam_policy.rke2_policy.arn
  }

  instance_tags = {
    "kubernetes.io/cluster/cluster-mgmt": "shared"
  }
  tags = {
    "kubernetes.io/cluster/cluster-mgmt": "shared"
  }
}

module "ec2_instance_workers" { 
  source = "terraform-aws-modules/ec2-instance/aws"
  version = "5.5.0"
  
  timeouts = {
    create = "1h30m"
    update = "2h"
    delete = "20m"
  }

  for_each = var.workers

  ami = local.ami
  name = each.key
  instance_type = local.instance_type_outpost
  key_name = var.key_name
  monitoring = var.monitoring
  vpc_security_group_ids = [aws_security_group.rke2_cluster_sgs.id]
  subnet_id = aws_subnet.tf_outpost_subnet.id
  associate_public_ip_address = false
  iam_role_description = "IAM Role to EC2 intances"
  create_iam_instance_profile = true
  user_data =  <<-EOF
               sudo snap install amazon-ssm-agent --classic
               sudo snap list amazon-ssm-agent
               sudo snap start amazon-ssm-agent
               sudo snap services amazon-ssm-agent
               EOF
  iam_role_policies = {
    AmazonSSMManagedInstanceCore = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
    AWSLoadBalancerControllerIAMPolicy = aws_iam_policy.aws_lb_controller.arn
    AWSRKE2Policy = aws_iam_policy.rke2_policy.arn
  }
  instance_tags = {
    "kubernetes.io/cluster/cluster-mgmt": "shared"
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
  value = [ for p in values(var.masters): p.private_ip ]  
}

output "username" {
  value = local.username
}