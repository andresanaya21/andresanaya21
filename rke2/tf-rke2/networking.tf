module "vpc" {
  source = "terraform-aws-modules/vpc/aws"

  name = local.vpc_name
  cidr = local.vpc_cidr

  azs             = local.azs
  private_subnets =  [for k, v in local.azs : cidrsubnet(local.vpc_cidr, 8, k)]
  public_subnets  =  [for k, v in local.azs : cidrsubnet(local.vpc_cidr, 8, k + 48)]

  enable_nat_gateway = true
  single_nat_gateway = true

  tags = var.tags
}

resource "aws_subnet" "tf_outpost_subnet" {
  vpc_id     = module.vpc.vpc_id
  cidr_block = "10.0.4.0/24"
  outpost_arn = "arn:aws:outposts:eu-west-3:050107717205:outpost/op-066d526775d892a1f"
  availability_zone = "eu-west-3a"

  tags = {
  Name: "tf-outpost-${local.region}"
  region: "outpost"
  }
}

# Create a route table
resource "aws_route_table" "rtb" {
  vpc_id = module.vpc.vpc_id

  # Create a route to the Internet gateway
  route {
    cidr_block = "0.0.0.0/0"
    nat_gateway_id  = module.vpc.natgw_ids[0]
  }
}

# Associate the route table with the subnet
resource "aws_route_table_association" "rta" {
  subnet_id      = aws_subnet.tf_outpost_subnet.id
  route_table_id = aws_route_table.rtb.id
}

resource "aws_subnet" "tf_outpost_subnet_lni" {
  vpc_id     = module.vpc.vpc_id
  cidr_block = "10.0.5.0/24"
  outpost_arn = "arn:aws:outposts:eu-west-3:050107717205:outpost/op-066d526775d892a1f"
  availability_zone = "eu-west-3a"

  tags = {
    Name =  "tf-outpost-${local.region}-lni"
    region = "outpost"
  }
}

resource "aws_network_interface" "second_nic" {
  count = length(local.list_private_ips)
  subnet_id = aws_subnet.tf_outpost_subnet_lni.id
  private_ip  = local.list_private_ips[count.index]
  security_groups = [ module.security_group.security_group_id ]
  tags = var.tags
  
}

resource "aws_network_interface_attachment" "attach_second_nic" {
  count = length(local.list_ec2)
  instance_id          = local.list_ec2[count.index]
  network_interface_id = aws_network_interface.second_nic[count.index].id
  device_index         = 1

  depends_on = [ module.ec2_instance ]
}