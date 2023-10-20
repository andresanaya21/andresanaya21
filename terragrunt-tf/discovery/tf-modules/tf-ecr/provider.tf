terraform {
  required_providers {
    aws = {
      source = "hashicorp/aws"
    }
  }
}

provider "aws" {
   region = "us-east-1"
  profile = "discovery"
  default_tags {
    tags = {
      owner = "david.artunedoguillen@telefonica.com"
      account = "future-network-labs"
    }
  }
  
}