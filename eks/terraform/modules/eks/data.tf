data "tls_certificate" "oicd" {
    url = aws_eks_cluster.cluster.identity[0].oidc[0].issuer
}