data "external" "current_ip" {
  program = ["bash", "-c", "curl -s 'https://api.ipify.org?format=json'"]
}

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}
data "aws_availability_zones" "available" {}

locals {
  account_id          = data.aws_caller_identity.current.account_id
  region              = data.aws_region.current.name
  azs      = slice(data.aws_availability_zones.available.names, 0, 3)
  vpc_cidr = "10.0.0.0/16"
  vpc_name = "tf-vpc-outpost"
  ami = "ami-05b5a865c3579bbc4"
  instance_type = "c6id.2xlarge"
}