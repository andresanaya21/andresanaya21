terraform {
  required_providers {
    aws = {
      source = "hashicorp/aws"
    }
  }
}

provider "aws" {
  region = "eu-west-3"
  profile = "upv"
  default_tags {
    tags = {
      subject = "terraform to deploy RKE2 cluster in AWS Outpost"
    }
  }
  
}