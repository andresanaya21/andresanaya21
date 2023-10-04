resource "aws_security_group" "rke2_cluster_sgs" {
  name        = "rke2_cluster_sgs"
  description = "Security group to the first interface"
  vpc_id      = module.vpc.vpc_id

  ingress {
    description      = "9345 TCP RKE2 supervisor API"
    from_port        = 9345
    to_port          = 9345
    protocol         = "tcp"
    cidr_blocks      = [local.vpc_cidr]
  }
  ingress {
    description      = "6443 TCP Kubernetes API"
    from_port        = 6443
    to_port          = 6443
    protocol         = "tcp"
    cidr_blocks      = [local.vpc_cidr]
  }
  ingress {
    description      = "8472 UDP Required only for Flannel VXLAN, Canal CNI with VXLAN, Cilium CNI VXLAN, Canal CNI with VXLAN"
    from_port        = 8472
    to_port          = 8472
    protocol         = "udp"
    cidr_blocks      = [local.vpc_cidr]
  }
  ingress {
    description      = "10250 TCP kubelet metrics"
    from_port        = 10250
    to_port          = 10250
    protocol         = "tcp"
    cidr_blocks      = [local.vpc_cidr]
  }
  ingress {
    description      = "2379 TCP etcd client port"
    from_port        = 2379
    to_port          = 2379
    protocol         = "tcp"
    cidr_blocks      = [local.vpc_cidr]
  }
  ingress {
    description      = "2380 TCP etcd peer port"
    from_port        = 2380
    to_port          = 2380
    protocol         = "tcp"
    cidr_blocks      = [local.vpc_cidr]
  }
  ingress {
    description      = "2381 TCP etcd metrics port"
    from_port        = 2381
    to_port          = 2381
    protocol         = "tcp"
    cidr_blocks      = [local.vpc_cidr]
  }
  ingress {
    description      = "30000-32767 TCP NodePort port range"
    from_port        = 30000
    to_port          = 32767
    protocol         = "tcp"
    cidr_blocks      = [local.vpc_cidr]
  }
  ingress {
    description      = "4240 TCP Cilium CNI health checks"
    from_port        = 4240
    to_port          = 4240
    protocol         = "tcp"
    cidr_blocks      = [local.vpc_cidr]
  }
  ingress {
    description      = "ICMP Cilium CNI health checks"
    from_port        = -1
    to_port          = -1
    protocol         = "icmp"
    cidr_blocks      = [local.vpc_cidr]
  }
  ingress {
    description      = "179 TCP Calico CNI with BGP"
    from_port        = 179
    to_port          = 179
    protocol         = "tcp"
    cidr_blocks      = [local.vpc_cidr]
  }
  ingress {
    description      = "4789 UDP Calico CNI with VXLAN"
    from_port        = 4789
    to_port          = 4789
    protocol         = "udp"
    cidr_blocks      = [local.vpc_cidr]
  }
  ingress {
    description      = "5473 TCP Calico CNI with Typha"
    from_port        = 5473
    to_port          = 5473
    protocol         = "tcp"
    cidr_blocks      = [local.vpc_cidr]
  }
  ingress {
    description      = "9098 TCP Calico Typha health checks"
    from_port        = 9098
    to_port          = 9098
    protocol         = "tcp"
    cidr_blocks      = [local.vpc_cidr]
  }
  ingress {
    description      = "9099 TCP Calico health checks, Canal CNI health checks"
    from_port        = 9099
    to_port          = 9099
    protocol         = "tcp"
    cidr_blocks      = [local.vpc_cidr]
  }
  ingress {
    description      = "51820 UDP Canal CNI with WireGuard IPv4"
    from_port        = 51820
    to_port          = 51820
    protocol         = "udp"
    cidr_blocks      = [local.vpc_cidr]
  }
  ingress {
    description      = "51821 UDP Canal CNI with WireGuard IPv6/dual-stack"
    from_port        = 51821
    to_port          = 51821
    protocol         = "udp"
    cidr_blocks      = [local.vpc_cidr]
  }
  ingress {
    description      = "443 TLS"
    from_port        = 443
    to_port          = 443
    protocol         = "tcp"
    cidr_blocks      = [local.vpc_cidr]
  }
  ingress {
    description      = "22 SSH"
    from_port        = 22
    to_port          = 22
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