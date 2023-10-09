#################################### 0GPU STANDARD ############################################################

resource "opennebula_virtual_machine" "c2-standard-r8" {
  for_each    = { for i, vm in var.vm_settings : i => vm if vm["instance_type"] == "c2-standard-r8" }
  name        = each.value.name
  cpu         = try(each.value.cpu, "1")
  vcpu        = try(each.value.vcpu, "2")
  memory      = try(each.value.memory, "8192") # 8GB
  template_id = data.opennebula_template.template_0GPU.id
  ### Hay que definir disco y NIC porque si se toma la config de la plantilla, ya no son modificables
  disk {
    image_id = data.opennebula_image.Ubuntu_22_04.id
    size     = try(each.value.size, "51200") # 50GB
  }
  nic {
    network_id = data.opennebula_virtual_network.service_vnet.id
  }
  tags = {
    OWNER = "alvaro.curtomerino@telefonica.com"
    TEAM = "Future Networks Lab"
  }
}

resource "opennebula_virtual_machine" "c4-standard-r16" {
  for_each    = { for i, vm in var.vm_settings : i => vm if vm["instance_type"] == "c4-standard-r16" }
  name        = each.value.name
  cpu         = try(each.value.cpu, "2")
  vcpu        = try(each.value.vcpu, "4")
  memory      = try(each.value.memory, "16384") # 16GB
  template_id = data.opennebula_template.template_0GPU.id
  disk {
    image_id = data.opennebula_image.Ubuntu_22_04.id
    size     = try(each.value.size, "61440") # 60GB
  }
  nic {
    network_id = data.opennebula_virtual_network.service_vnet.id
  }
}

resource "opennebula_virtual_machine" "c8-standard-r32" {
  for_each    = { for i, vm in var.vm_settings : i => vm if vm["instance_type"] == "c8-standard-r32" }
  name        = each.value.name
  cpu         = try(each.value.cpu, "4")
  vcpu        = try(each.value.vcpu, "8")
  memory      = try(each.value.memory, "32768") # 32GB
  template_id = data.opennebula_template.template_0GPU.id
  disk {
    image_id = data.opennebula_image.Ubuntu_22_04.id
    size     = try(each.value.size, "71680") # 70GB
  }
  nic {
    network_id = data.opennebula_virtual_network.service_vnet.id
  }
}

resource "opennebula_virtual_machine" "c16-standard-r64" {
  for_each    = { for i, vm in var.vm_settings : i => vm if vm["instance_type"] == "c16-standard-r64" }
  name        = each.value.name
  cpu         = try(each.value.cpu, "8")
  vcpu        = try(each.value.vcpu, "16")
  memory      = try(each.value.memory, "65536") # 64GB
  template_id = data.opennebula_template.template_0GPU.id
  disk {
    image_id = data.opennebula_image.Ubuntu_22_04.id
    size     = try(each.value.size, "81920") # 80GB
  }
  nic {
    network_id = data.opennebula_virtual_network.service_vnet.id
  }
}

resource "opennebula_virtual_machine" "c32-standard-r128" {
  for_each    = { for i, vm in var.vm_settings : i => vm if vm["instance_type"] == "c32-standard-r128" }
  name        = each.value.name
  cpu         = try(each.value.cpu, "16")
  vcpu        = try(each.value.vcpu, "32")
  memory      = try(each.value.memory, "131072") # 128GB
  template_id = data.opennebula_template.template_0GPU.id
  disk {
    image_id = data.opennebula_image.Ubuntu_22_04.id
    size     = try(each.value.size, "92160") # 90GB
  }
  nic {
    network_id = data.opennebula_virtual_network.service_vnet.id
  }
}

#################################### 0GPU OPTIMIZED ############################################################

resource "opennebula_virtual_machine" "c2-optimized-r8" {
  for_each    = { for i, vm in var.vm_settings : i => vm if vm["instance_type"] == "c2-optimized-r8" }
  name        = each.value.name
  cpu         = try(each.value.cpu, "2")
  vcpu        = try(each.value.vcpu, "2")
  memory      = try(each.value.memory, "8192") # 8GB
  template_id = data.opennebula_template.template_0GPU.id
  disk {
    image_id = data.opennebula_image.Ubuntu_22_04.id
    size     = try(each.value.size, "51200") # 50GB
  }
  nic {
    network_id = data.opennebula_virtual_network.service_vnet.id
  }
}

resource "opennebula_virtual_machine" "c4-optimized-r16" {
  for_each    = { for i, vm in var.vm_settings : i => vm if vm["instance_type"] == "c4-optimized-r16" }
  name        = each.value.name
  cpu         = try(each.value.cpu, "4")
  vcpu        = try(each.value.vcpu, "4")
  memory      = try(each.value.memory, "16384") # 16GB
  template_id = data.opennebula_template.template_0GPU.id
  disk {
    image_id = data.opennebula_image.Ubuntu_22_04.id
    size     = try(each.value.size, "61440") # 60GB
  }
  nic {
    network_id = data.opennebula_virtual_network.service_vnet.id
  }
}

resource "opennebula_virtual_machine" "c8-optimized-r32" {
  for_each    = { for i, vm in var.vm_settings : i => vm if vm["instance_type"] == "c8-optimized-r32" }
  name        = each.value.name
  cpu         = try(each.value.cpu, "8")
  vcpu        = try(each.value.vcpu, "8")
  memory      = try(each.value.memory, "32768") # 32GB
  template_id = data.opennebula_template.template_0GPU.id
  disk {
    image_id = data.opennebula_image.Ubuntu_22_04.id
    size     = try(each.value.size, "71680") # 70GB
  }
  nic {
    network_id = data.opennebula_virtual_network.service_vnet.id
  }
}

resource "opennebula_virtual_machine" "c16-optimized-r64" {
  for_each    = { for i, vm in var.vm_settings : i => vm if vm["instance_type"] == "c16-optimized-r64" }
  name        = each.value.name
  cpu         = try(each.value.cpu, "16")
  vcpu        = try(each.value.vcpu, "16")
  memory      = try(each.value.memory, "65536") # 64GB
  template_id = data.opennebula_template.template_0GPU.id
  disk {
    image_id = data.opennebula_image.Ubuntu_22_04.id
    size     = try(each.value.size, "81920") # 80GB
  }
  nic {
    network_id = data.opennebula_virtual_network.service_vnet.id
  }
}

resource "opennebula_virtual_machine" "c32-optimized-r128" {
  for_each    = { for i, vm in var.vm_settings : i => vm if vm["instance_type"] == "c32-optimized-r128" }
  name        = each.value.name
  cpu         = try(each.value.cpu, "32")
  vcpu        = try(each.value.vcpu, "32")
  memory      = try(each.value.memory, "131072") # 128GB
  template_id = data.opennebula_template.template_0GPU.id
  disk {
    image_id = data.opennebula_image.Ubuntu_22_04.id
    size     = try(each.value.size, "92160") # 90GB
  }
  nic {
    network_id = data.opennebula_virtual_network.service_vnet.id
  }
}

#################################### 1GPU STANDARD ############################################################

resource "opennebula_virtual_machine" "g1-c4-standard-r16" {
  for_each    = { for i, vm in var.vm_settings : i => vm if vm["instance_type"] == "g1-c4-standard-r16" }
  name        = var.vm_settings[each.key].name
  cpu         = try(each.value.cpu, "2")
  vcpu        = try(each.value.vcpu, "4")
  memory      = try(each.value.memory, "16384") # 16GB
  template_id = data.opennebula_template.template_1GPU.id

  disk {
    image_id = data.opennebula_image.Ubuntu_22_04.id
    size     = try(each.value.size, "131072") # 128GB
  }
  nic {
    network_id = data.opennebula_virtual_network.service_vnet.id
  }
}

resource "opennebula_virtual_machine" "g1-c8-standard-r32" {
  for_each    = { for i, vm in var.vm_settings : i => vm if vm["instance_type"] == "g1-c8-standard-r32" }
  name        = var.vm_settings[each.key].name
  cpu         = try(each.value.cpu, "4")
  vcpu        = try(each.value.vcpu, "8")
  memory      = try(each.value.memory, "32768") # 32GB
  template_id = data.opennebula_template.template_1GPU.id

  disk {
    image_id = data.opennebula_image.Ubuntu_22_04.id
    size     = try(each.value.size, "131072") # 128GB
  }
  nic {
    network_id = data.opennebula_virtual_network.service_vnet.id
  }
}

resource "opennebula_virtual_machine" "g1-c12-standard-r48" {
  for_each    = { for i, vm in var.vm_settings : i => vm if vm["instance_type"] == "g1-c12-standard-r48" }
  name        = var.vm_settings[each.key].name
  cpu         = try(each.value.cpu, "6")
  vcpu        = try(each.value.vcpu, "12")
  memory      = try(each.value.memory, "49152") # 48GB
  template_id = data.opennebula_template.template_1GPU.id

  disk {
    image_id = data.opennebula_image.Ubuntu_22_04.id
    size     = try(each.value.size, "131072") # 128GB
  }
  nic {
    network_id = data.opennebula_virtual_network.service_vnet.id
  }
}

resource "opennebula_virtual_machine" "g1-c16-standard-r64" {
  for_each    = { for i, vm in var.vm_settings : i => vm if vm["instance_type"] == "g1-c16-standard-r64" }
  name        = var.vm_settings[each.key].name
  cpu         = try(each.value.cpu, "8")
  vcpu        = try(each.value.vcpu, "16")
  memory      = try(each.value.memory, "65536") # 64GB
  template_id = data.opennebula_template.template_1GPU.id

  disk {
    image_id = data.opennebula_image.Ubuntu_22_04.id
    size     = try(each.value.size, "131072") # 128GB
  }
  nic {
    network_id = data.opennebula_virtual_network.service_vnet.id
  }
}

resource "opennebula_virtual_machine" "g1-c32-standard-r128" {
  for_each    = { for i, vm in var.vm_settings : i => vm if vm["instance_type"] == "g1-c32-standard-r128" }
  name        = var.vm_settings[each.key].name
  cpu         = try(each.value.cpu, "16")
  vcpu        = try(each.value.vcpu, "32")
  memory      = try(each.value.memory, "131072") # 128GB
  template_id = data.opennebula_template.template_1GPU.id

  disk {
    image_id = data.opennebula_image.Ubuntu_22_04.id
    size     = try(each.value.size, "131072") # 128GB
  }
  nic {
    network_id = data.opennebula_virtual_network.service_vnet.id
  }
}

#################################### 2GPU STANDARD ############################################################

resource "opennebula_virtual_machine" "g2-c24-standard-r96" {
  for_each    = { for i, vm in var.vm_settings : i => vm if vm["instance_type"] == "g2-c24-standard-r96" }
  name        = var.vm_settings[each.key].name
  cpu         = try(each.value.cpu, "12")
  vcpu        = try(each.value.vcpu, "24")
  memory      = try(each.value.memory, "98304") # 96GB
  template_id = data.opennebula_template.template_2GPU.id

  disk {
    image_id = data.opennebula_image.Ubuntu_22_04.id
    size     = try(each.value.size, "131072") # 128GB
  }
  nic {
    network_id = data.opennebula_virtual_network.service_vnet.id
  }
}

resource "opennebula_virtual_machine" "g2-c32-standard-r128" {
  for_each    = { for i, vm in var.vm_settings : i => vm if vm["instance_type"] == "g2-c32-standard-r128" }
  name        = var.vm_settings[each.key].name
  cpu         = try(each.value.cpu, "16")
  vcpu        = try(each.value.vcpu, "32")
  memory      = try(each.value.memory, "131072") # 128GB
  template_id = data.opennebula_template.template_2GPU.id

  disk {
    image_id = data.opennebula_image.Ubuntu_22_04.id
    size     = try(each.value.size, "131072") # 128GB
  }
  nic {
    network_id = data.opennebula_virtual_network.service_vnet.id
  }
}

#################################### 1GPU OPTIMIZED ############################################################

resource "opennebula_virtual_machine" "g1-c4-optimized-r16" {
  for_each    = { for i, vm in var.vm_settings : i => vm if vm["instance_type"] == "g1-c4-optimized-r16" }
  name        = var.vm_settings[each.key].name
  cpu         = try(each.value.cpu, "4")
  vcpu        = try(each.value.vcpu, "4")
  memory      = try(each.value.memory, "16384") # 16GB
  template_id = data.opennebula_template.template_1GPU.id

  disk {
    image_id = data.opennebula_image.Ubuntu_22_04.id
    size     = try(each.value.size, "131072") # 128GB
  }
  nic {
    network_id = data.opennebula_virtual_network.service_vnet.id
  }
}

resource "opennebula_virtual_machine" "g1-c8-optimized-r32" {
  for_each    = { for i, vm in var.vm_settings : i => vm if vm["instance_type"] == "g1-c8-optimized-r32" }
  name        = var.vm_settings[each.key].name
  cpu         = try(each.value.cpu, "8")
  vcpu        = try(each.value.vcpu, "8")
  memory      = try(each.value.memory, "32768") # 32GB
  template_id = data.opennebula_template.template_1GPU.id

  disk {
    image_id = data.opennebula_image.Ubuntu_22_04.id
    size     = try(each.value.size, "131072") # 128GB
  }
  nic {
    network_id = data.opennebula_virtual_network.service_vnet.id
  }
}

resource "opennebula_virtual_machine" "g1-c12-optimized-r48" {
  for_each    = { for i, vm in var.vm_settings : i => vm if vm["instance_type"] == "g1-c12-optimized-r48" }
  name        = var.vm_settings[each.key].name
  cpu         = try(each.value.cpu, "12")
  vcpu        = try(each.value.vcpu, "12")
  memory      = try(each.value.memory, "49152") # 48GB
  template_id = data.opennebula_template.template_1GPU.id

  disk {
    image_id = data.opennebula_image.Ubuntu_22_04.id
    size     = try(each.value.size, "131072") # 128GB
  }
  nic {
    network_id = data.opennebula_virtual_network.service_vnet.id
  }
}

resource "opennebula_virtual_machine" "g1-c16-optimized-r64" {
  for_each    = { for i, vm in var.vm_settings : i => vm if vm["instance_type"] == "g1-c16-optimized-r64" }
  name        = var.vm_settings[each.key].name
  cpu         = try(each.value.cpu, "16")
  vcpu        = try(each.value.vcpu, "16")
  memory      = try(each.value.memory, "65536") # 64GB
  template_id = data.opennebula_template.template_1GPU.id

  disk {
    image_id = data.opennebula_image.Ubuntu_22_04.id
    size     = try(each.value.size, "131072") # 128GB
  }
  nic {
    network_id = data.opennebula_virtual_network.service_vnet.id
  }
}

resource "opennebula_virtual_machine" "g1-c32-optimized-r128" {
  for_each    = { for i, vm in var.vm_settings : i => vm if vm["instance_type"] == "g1-c32-optimized-r128" }
  name        = var.vm_settings[each.key].name
  cpu         = try(each.value.cpu, "32")
  vcpu        = try(each.value.vcpu, "32")
  memory      = try(each.value.memory, "131072") # 128GB
  template_id = data.opennebula_template.template_1GPU.id

  disk {
    image_id = data.opennebula_image.Ubuntu_22_04.id
    size     = try(each.value.size, "131072") # 128GB
  }
  nic {
    network_id = data.opennebula_virtual_network.service_vnet.id
  }
}

#################################### 2GPU STANDARD ############################################################

resource "opennebula_virtual_machine" "g2-c24-optimized-r96" {
  for_each    = { for i, vm in var.vm_settings : i => vm if vm["instance_type"] == "g2-c24-optimized-r96" }
  name        = var.vm_settings[each.key].name
  cpu         = try(each.value.cpu, "24")
  vcpu        = try(each.value.vcpu, "24")
  memory      = try(each.value.memory, "98304") # 96GB
  template_id = data.opennebula_template.template_2GPU.id

  disk {
    image_id = data.opennebula_image.Ubuntu_22_04.id
    size     = try(each.value.size, "131072") # 128GB
  }
  nic {
    network_id = data.opennebula_virtual_network.service_vnet.id
  }
}

resource "opennebula_virtual_machine" "g2-c32-optimized-r128" {
  for_each    = { for i, vm in var.vm_settings : i => vm if vm["instance_type"] == "g2-c32-optimized-r128" }
  name        = var.vm_settings[each.key].name
  cpu         = try(each.value.cpu, "32")
  vcpu        = try(each.value.vcpu, "32")
  memory      = try(each.value.memory, "131072") # 128GB
  template_id = data.opennebula_template.template_2GPU.id

  disk {
    image_id = data.opennebula_image.Ubuntu_22_04.id
    size     = try(each.value.size, "131072") # 128GB
  }
  nic {
    network_id = data.opennebula_virtual_network.service_vnet.id
  }
}