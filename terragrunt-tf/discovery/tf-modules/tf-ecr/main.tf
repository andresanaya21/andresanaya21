resource "aws_ecrpublic_repository" "example" {
  for_each = toset(var.repository_names)

  repository_name = each.key
  catalog_data {
    about_text     = "This is a short description of the repository."
    operating_systems = ["Linux"]
    architectures     = ["x86"]
    logo_image_blob   = filebase64("./image.png")
    usage_text        = "This is a short description of the repository."
  }
}