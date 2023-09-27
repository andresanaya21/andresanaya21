resource "aws_security_group" "rke2_cluster_sgs" {
  name        = "rke2_cluster_sgs"
  description = "Security group to the first interface"
  vpc_id      = module.vpc.vpc_id

  ingress {
    description      = "443 TLS"
    from_port        = 443
    to_port          = 443
    protocol         = "tcp"
    cidr_blocks      = [local.vpc_cidr]
  }

  egress {
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  tags = var.tags
}

module "security_group" {
  source  = "terraform-aws-modules/security-group/aws"
  version = "~> 4.0"

  name        = local.vpc_name
  description = "Security group to the lni interface"
  vpc_id      = module.vpc.vpc_id

  ingress_cidr_blocks = ["0.0.0.0/0"]
  ingress_rules       = ["all-all"]
  egress_rules        = ["all-all"]

  tags = var.tags
}