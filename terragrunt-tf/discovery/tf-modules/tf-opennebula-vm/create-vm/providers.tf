terraform {
  required_providers {
    opennebula = {
      source  = "OpenNebula/opennebula"
      version = "1.3.1"
    }
  }
}

provider "opennebula" {
  endpoint = var.endpoint
  username = var.oneuser
  password = var.onepasswd
}
