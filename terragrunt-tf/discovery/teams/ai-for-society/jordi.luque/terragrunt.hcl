include {
  path = find_in_parent_folders()
  expose = true
}

terraform {
    source = "./"
#  source = "tf-modules/${path_relative_from_include()}/create-vm"
}

inputs = {}