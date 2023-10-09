module "tf-opennebula-vm" {
    source = "./create-vm"
    vm_settings = var.vm_settings
}