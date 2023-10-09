data "opennebula_image" "Ubuntu_22_04" {
  name = "Ubuntu 22.04"
}

data "opennebula_virtual_network" "service_vnet" {
  name = "SRV"
}

data "opennebula_virtual_network" "management_vnet" {
  name = "MGMT"
}

data "opennebula_template" "template_0GPU" {
  name = "Ubuntu 22.04 Valladolid 0GPU"
}

data "opennebula_template" "template_1GPU" {
  name = "Ubuntu 22.04 Valladolid 1GPU"
}

data "opennebula_template" "template_2GPU" {
  name = "Ubuntu 22.04 Valladolid 2GPU"
}