resource "helm_release" "argocd" {
  name             = "argocd"
  repository       = "argo-cd"
  chart            = "argo-cd"
  namespace        = "argocd"
  create_namespace = true

  values = [
    yamlencode({
      server = {
        service = {
          type = "LoadBalancer" # exposes Argo CD externally
        }
      }
    })
  ]
}