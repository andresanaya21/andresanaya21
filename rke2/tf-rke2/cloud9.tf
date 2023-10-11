resource "aws_cloud9_environment_ec2" "bastion" {
    count = (var.bastion_host ? 1 : 0)
    name = "bastion-telefonica"
    description = "bastion to telefonica"
    instance_type = "t3.medium"
    image_id = "ubuntu-18.04-x86_64"
    subnet_id = module.vpc.private_subnets[0]
    connection_type = "CONNECT_SSM"
    tags = var.tags   
    
#    timeouts {
#     create = "60m"
#     delete = "2h"
#    }
}