module "opennebula-vm" {
    source = "/root/andres/discovery/tf-modules/tf-opennebula-vm"
# source = "git@github.com/repo-tf-opennebula-modules/create-mv?ref=main|tag|release"
    vm_settings = [
     {
       name          = "jordi-terragrunt-0"
       instance_type = "c4-standard-r16"
     }

  ] 
 }
