# Guía de Ejecución - Azure DevOps Terraform AKS GitOps Lab

## 📋 Propósito del Repositorio

Este repositorio demuestra cómo:
1. **Infraestructura como Código (IaC)**: Crear recursos de Azure (AKS, ACR, VNet) usando Terraform
2. **GitOps**: Implementar Argo CD para automatizar despliegues en Kubernetes
3. **CI/CD**: Desplegar una aplicación Flask en un clúster AKS

---

## 🔧 Prerrequisitos

Antes de comenzar, asegúrate de tener instalado:

```bash
# Verificar instalaciones
terraform --version  # >= 1.6.0
az --version         # Azure CLI
kubectl version --client
helm version
docker --version
```

---

## 📝 Paso 1: Autenticación en Azure

```bash
# Iniciar sesión en Azure
az login

# Configurar la suscripción (reemplaza SUBSCRIPTION_ID con tu ID)
az account set --subscription "SUBSCRIPTION_ID"

# Obtener tu Subscription ID y Tenant ID
az account show --query "{subscriptionId:id, tenantId:tenantId}" -o tsv
```

**Guarda estos valores** (Subscription ID y Tenant ID) para el siguiente paso.

---

## 📝 Paso 2: Configurar Variables de Terraform

Crear un archivo `terraform/terraform.tfvars` con tus valores:

```bash
cd terraform
cat > terraform.tfvars << EOF
subscription_id = "TU_SUBSCRIPTION_ID"
tenant_id       = "TU_TENANT_ID"
resource_group_name = "rg-aks-lab"
location        = "eastus"
vnet_name       = "vnet-aks-lab"
subnet_name     = "subnet-aks"
acr_name_prefix = "acraks"
aks_name        = "aks-lab"
agent_count     = 1
agent_size      = "Standard_B2s"
EOF
```

**O crea el archivo manualmente** con tus valores.

---

## 📝 Paso 3: Inicializar y Aplicar Terraform

```bash
# Desde el directorio terraform/
cd terraform

# Inicializar Terraform (descarga providers)
terraform init

# Validar la configuración
terraform validate

# Ver el plan de ejecución (qué recursos se crearán)
terraform plan

# Aplicar la infraestructura (esto puede tomar 10-15 minutos)
terraform apply

# Confirmar con "yes" cuando se solicite
```

**⚠️ Nota**: Este paso crea:
- Resource Group
- Virtual Network y Subnet
- Azure Container Registry (ACR)
- Cluster AKS
- Argo CD (vía Helm)

**Tiempo estimado**: 10-15 minutos

---

## 📝 Paso 4: Configurar kubectl para Conectarse al AKS

```bash
# Obtener las credenciales del cluster
az aks get-credentials --resource-group rg-aks-lab --name aks-lab

# Verificar conexión
kubectl get nodes

# Verificar que Argo CD esté desplegado
kubectl get pods -n argocd
```

---

## 📝 Paso 5: Obtener Credenciales de Argo CD

```bash
# Esperar a que el servicio LoadBalancer obtenga una IP externa
kubectl get svc -n argocd

# Obtener la contraseña inicial de Argo CD
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d

# Obtener la IP externa de Argo CD
kubectl get svc argocd-server -n argocd
```

**Guarda estos valores**:
- IP externa del servicio `argocd-server`
- Contraseña del admin (username: `admin`)

Accede a Argo CD en: `https://IP_EXTERNA` (puede tardar unos minutos en estar disponible)

---

## 📝 Paso 6: Construir y Publicar la Imagen Docker

```bash
# Volver al directorio raíz
cd ..

# Obtener el nombre del ACR (del output de Terraform o desde Azure)
# O ejecutar: terraform output -raw acr_login_server
ACR_NAME=$(az acr list --resource-group rg-aks-lab --query "[0].name" -o tsv)
ACR_LOGIN_SERVER="${ACR_NAME}.azurecr.io"

# Autenticarse en ACR
az acr login --name $ACR_NAME

# Construir la imagen Docker
cd app
docker build -t flask-api:v1 .

# Etiquetar la imagen para ACR
docker tag flask-api:v1 ${ACR_LOGIN_SERVER}/flask-api:v1

# Publicar la imagen en ACR
docker push ${ACR_LOGIN_SERVER}/flask-api:v1
```

---

## 📝 Paso 7: Actualizar los Manifiestos de GitOps

Actualizar `gitops-manifests/deployment.yaml` con el nombre correcto de tu ACR:

```bash
# Obtener el nombre del ACR
ACR_LOGIN_SERVER=$(az acr show --resource-group rg-aks-lab --name $ACR_NAME --query loginServer -o tsv)

# Actualizar el deployment.yaml (reemplaza acraksutai.azurecr.io con tu ACR)
# Edita el archivo gitops-manifests/deployment.yaml y cambia:
# image: acraksutai.azurecr.io/flask-api:v2
# Por: image: ${ACR_LOGIN_SERVER}/flask-api:v1
```

**O edita manualmente** el archivo `gitops-manifests/deployment.yaml` y actualiza la línea 19 con tu ACR.

También necesitas actualizar el puerto en `deployment.yaml` de 5000 a 8080 (ya que la app Flask usa 8080).

---

## 📝 Paso 8: Configurar AKS para Acceder a ACR

```bash
# Obtener el ID de la identidad del cluster AKS
AKS_ID=$(az aks show --resource-group rg-aks-lab --name aks-lab --query identity.principalId -o tsv)

# Obtener el ID del ACR
ACR_ID=$(az acr show --resource-group rg-aks-lab --name $ACR_NAME --query id -o tsv)

# Asignar el rol AcrPull al cluster AKS
az role assignment create --assignee $AKS_ID --role AcrPull --scope $ACR_ID
```

---

## 📝 Paso 9: Configurar Argo CD Application

```bash
# Crear una aplicación en Argo CD usando kubectl
cat <<EOF | kubectl apply -f -
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: flask-app
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/TU_USUARIO/azure-devops-terraform-aks-gitops-lab
    targetRevision: master
    path: gitops-manifests
  destination:
    server: https://kubernetes.default.svc
    namespace: default
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
    - CreateNamespace=true
EOF
```

**⚠️ Nota**: Si tu repositorio es privado o estás usando un repo local, necesitarás:
1. Subir los manifiestos a un repositorio Git
2. O configurar Argo CD para usar un repo local/configmap

**Alternativa**: Si prefieres usar el repositorio local, puedes aplicar los manifiestos directamente:

```bash
kubectl apply -f gitops-manifests/
```

---

## 📝 Paso 10: Verificar el Despliegue

```bash
# Ver pods de la aplicación
kubectl get pods

# Ver servicios
kubectl get svc

# Obtener la IP externa del servicio Flask
kubectl get svc flask-service

# Probar la aplicación (reemplaza EXTERNAL_IP con la IP obtenida)
curl http://EXTERNAL_IP
curl http://EXTERNAL_IP/health
```

---

## 📝 Paso 11: Acceder a Argo CD UI

```bash
# Obtener la IP externa de Argo CD
kubectl get svc argocd-server -n argocd

# Acceder a: https://IP_EXTERNA
# Usuario: admin
# Contraseña: (la que obtuviste en el Paso 5)
```

---

## 🧹 Limpieza (Opcional)

Para eliminar todos los recursos creados:

```bash
cd terraform
terraform destroy
```

---

## 🔍 Comandos Útiles de Depuración

```bash
# Ver logs de pods
kubectl logs -l app=flask-api

# Describir un pod
kubectl describe pod <pod-name>

# Ver eventos
kubectl get events --sort-by='.lastTimestamp'

# Verificar configuración de Argo CD
kubectl get applications -n argocd
kubectl describe application flask-app -n argocd
```

---

## 📚 Resumen de Recursos Creados

1. **Azure Resource Group**: `rg-aks-lab`
2. **Virtual Network**: `vnet-aks-lab`
3. **Azure Container Registry**: `acraksXXXX` (nombre único)
4. **AKS Cluster**: `aks-lab`
5. **Argo CD**: Desplegado en el namespace `argocd`
6. **Flask Application**: Desplegada en el namespace `default`

---

## ⚠️ Notas Importantes

1. **Costos**: Este lab crea recursos que generan costos en Azure. Asegúrate de hacer `terraform destroy` cuando termines.

2. **Tiempo**: El despliegue completo puede tomar 15-20 minutos.

3. **ACR Name**: El nombre del ACR debe ser único globalmente en Azure. Terraform genera un sufijo aleatorio.

4. **Argo CD**: Si usas un repositorio privado, necesitarás configurar credenciales SSH o HTTPS en Argo CD.

5. **Puertos**: La aplicación Flask usa el puerto 8080, pero los manifiestos pueden necesitar ajustes.

---

## 🎯 Flujo Completo Resumido

```
1. az login → Autenticación Azure
2. terraform init → Inicializar Terraform
3. terraform apply → Crear infraestructura (AKS, ACR, Argo CD)
4. az aks get-credentials → Conectarse al cluster
5. docker build/push → Construir y publicar imagen
6. Configurar Argo CD → Crear Application
7. Verificar despliegue → kubectl get pods/svc
```

