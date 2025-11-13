# 🔐 Configuración de Secretos para GitHub Actions

Esta guía explica cómo configurar todos los secretos necesarios para el workflow de GitHub Actions.

## 📋 Secretos Requeridos

Necesitas configurar los siguientes secretos en tu repositorio de GitHub:

1. `AZURE_CREDENTIALS` ⚠️ **CRÍTICO** - Credenciales de Azure (Service Principal)
2. `REGISTRY_NAME` - Nombre del Azure Container Registry
3. `RESOURCE_GROUP` - Nombre del Resource Group
4. `AKS_CLUSTER` - Nombre del cluster AKS
5. `ACR_LOGIN_SERVER` - Servidor de login del ACR

---

## 🔑 Paso 1: Crear un Service Principal para Azure

El secreto `AZURE_CREDENTIALS` debe ser un JSON con las credenciales de un Service Principal. Sigue estos pasos:

### 1.1 Crear el Service Principal

```bash
# Configurar variables (ajusta según tus valores)
SUBSCRIPTION_ID=""  # Tu subscription ID
RESOURCE_GROUP="rg-aks-lab"
APP_NAME="github-actions-sp"  # Nombre para el Service Principal

# Crear el Service Principal
az ad sp create-for-rbac \
  --name $APP_NAME \
  --role contributor \
  --scopes /subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP \
  --sdk-auth
```

**⚠️ IMPORTANTE**: El comando `--sdk-auth` genera el JSON en el formato correcto. Copia toda la salida JSON.

### 1.2 Formato del JSON de AZURE_CREDENTIALS

El JSON debe tener este formato:

```json
{
  "clientId": "xxxx-xxxx-xxxx-xxxx",
  "clientSecret": "xxxx-xxxx-xxxx-xxxx",
  "subscriptionId": "856eda9f-88e9-431a-8fc7-f21c3290f493",
  "tenantId": "4102c976-cd88-4b70-9f99-58cf51409524",
  "activeDirectoryEndpointUrl": "https://login.microsoftonline.com",
  "resourceManagerEndpointUrl": "https://management.azure.com/",
  "activeDirectoryGraphResourceId": "https://graph.windows.net/",
  "sqlManagementEndpointUrl": "https://management.core.windows.net:8443/",
  "galleryEndpointUrl": "https://gallery.azure.com/",
  "managementEndpointUrl": "https://management.core.windows.net/"
}
```

**Nota**: Si usas `--sdk-auth`, el JSON ya viene en este formato. Solo copia y pega.

### 1.3 Asignar permisos adicionales (si es necesario)

Si el Service Principal necesita permisos adicionales para ACR:

```bash
# Obtener el ID del Service Principal
SP_ID=$(az ad sp list --display-name $APP_NAME --query "[0].id" -o tsv)

# Obtener el ID del ACR
ACR_NAME=$(az acr list --resource-group $RESOURCE_GROUP --query "[0].name" -o tsv)
ACR_ID=$(az acr show --resource-group $RESOURCE_GROUP --name $ACR_NAME --query id -o tsv)

# Asignar rol AcrPush al Service Principal
az role assignment create \
  --assignee $SP_ID \
  --role AcrPush \
  --scope $ACR_ID
```

---

## 📝 Paso 2: Obtener los Valores de los Secretos

### 2.1 Obtener valores desde Terraform (si ya aplicaste la infraestructura)

```bash
cd terraform

# Obtener Resource Group
terraform output resource_group
# Resultado: rg-aks-lab

# Obtener AKS Cluster name
terraform output aks_name
# Resultado: aks-lab

# Obtener ACR Login Server
terraform output acr_login_server
# Resultado: acraksXXXX.azurecr.io
```

### 2.2 Obtener valores desde Azure CLI

```bash
RESOURCE_GROUP="rg-aks-lab"

# Obtener nombre del ACR
ACR_NAME=$(az acr list --resource-group $RESOURCE_GROUP --query "[0].name" -o tsv)
echo "REGISTRY_NAME: $ACR_NAME"

# Obtener ACR Login Server
ACR_LOGIN_SERVER=$(az acr show --resource-group $RESOURCE_GROUP --name $ACR_NAME --query loginServer -o tsv)
echo "ACR_LOGIN_SERVER: $ACR_LOGIN_SERVER"

# Obtener nombre del AKS
AKS_CLUSTER=$(az aks list --resource-group $RESOURCE_GROUP --query "[0].name" -o tsv)
echo "AKS_CLUSTER: $AKS_CLUSTER"
```

---

## ⚙️ Paso 3: Configurar Secretos en GitHub

### 3.1 Ir a la configuración de secretos

1. Ve a tu repositorio en GitHub
2. Click en **Settings** (Configuración)
3. En el menú lateral, click en **Secrets and variables** → **Actions**
4. Click en **New repository secret**

### 3.2 Agregar cada secreto

Configura los siguientes secretos uno por uno:

#### 🔐 `AZURE_CREDENTIALS`
- **Name**: `AZURE_CREDENTIALS`
- **Value**: El JSON completo que obtuviste del comando `az ad sp create-for-rbac --sdk-auth`
- **Ejemplo**:
```json
{
  "clientId": "12345678-1234-1234-1234-123456789012",
  "clientSecret": "abc123...",
  "subscriptionId": "856eda9f-88e9-431a-8fc7-f21c3290f493",
  "tenantId": "4102c976-cd88-4b70-9f99-58cf51409524",
  ...
}
```

#### 📦 `REGISTRY_NAME`
- **Name**: `REGISTRY_NAME`
- **Value**: Solo el nombre del ACR, sin `.azurecr.io`
- **Ejemplo**: `acraks8vng`

#### 🏢 `RESOURCE_GROUP`
- **Name**: `RESOURCE_GROUP`
- **Value**: `rg-aks-lab` (o el nombre que uses)

#### ☸️ `AKS_CLUSTER`
- **Name**: `AKS_CLUSTER`
- **Value**: `aks-lab` (o el nombre que uses)

#### 🌐 `ACR_LOGIN_SERVER`
- **Name**: `ACR_LOGIN_SERVER`
- **Value**: El login server completo con `.azurecr.io`
- **Ejemplo**: `acraks8vng.azurecr.io`

---

## ✅ Paso 4: Verificar la Configuración

### 4.1 Verificar que todos los secretos estén configurados

En GitHub: **Settings** → **Secrets and variables** → **Actions**

Debes ver estos 5 secretos:
- ✅ `AZURE_CREDENTIALS`
- ✅ `REGISTRY_NAME`
- ✅ `RESOURCE_GROUP`
- ✅ `AKS_CLUSTER`
- ✅ `ACR_LOGIN_SERVER`

### 4.2 Probar el workflow

1. Haz un push a la rama `main`, o
2. Ve a **Actions** → Selecciona el workflow → **Run workflow**

---

## 🔍 Solución de Problemas

### Error: "Not all values are present. Ensure 'client-id' and 'tenant-id' are supplied"

**Causa**: El secreto `AZURE_CREDENTIALS` no está en el formato correcto o está incompleto.

**Solución**:
1. Verifica que el JSON esté completo (debe incluir `clientId`, `clientSecret`, `subscriptionId`, `tenantId`)
2. Asegúrate de copiar TODO el JSON del comando `az ad sp create-for-rbac --sdk-auth`
3. No agregues saltos de línea adicionales
4. Verifica que no haya caracteres especiales mal escapados

### Error: "Authentication failed"

**Causa**: El Service Principal no tiene los permisos necesarios.

**Solución**:
```bash
# Verificar que el Service Principal tenga el rol Contributor
az role assignment list \
  --assignee <SP_CLIENT_ID> \
  --scope /subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP
```

### Error: "ACR login failed"

**Causa**: El Service Principal no tiene permisos en el ACR.

**Solución**:
```bash
# Asignar rol AcrPush
SP_ID=$(az ad sp list --display-name github-actions-sp --query "[0].id" -o tsv)
ACR_ID=$(az acr show --resource-group $RESOURCE_GROUP --name $ACR_NAME --query id -o tsv)

az role assignment create \
  --assignee $SP_ID \
  --role AcrPush \
  --scope $ACR_ID
```

---

## 📚 Resumen de Valores

Basándote en tu configuración actual (`terraform.tfvars`):

| Secreto | Valor Esperado | Cómo Obtenerlo |
|---------|---------------|----------------|
| `AZURE_CREDENTIALS` | JSON del Service Principal | `az ad sp create-for-rbac --sdk-auth` |
| `REGISTRY_NAME` | `acraksXXXX` (sin .azurecr.io) | `terraform output` o `az acr list` |
| `RESOURCE_GROUP` | `rg-aks-lab` | De `terraform.tfvars` |
| `AKS_CLUSTER` | `aks-lab` | De `terraform.tfvars` |
| `ACR_LOGIN_SERVER` | `acraksXXXX.azurecr.io` | `terraform output acr_login_server` |

---

## 🎯 Comandos Rápidos de Referencia

```bash
# 1. Crear Service Principal y obtener AZURE_CREDENTIALS
az ad sp create-for-rbac \
  --name github-actions-sp \
  --role contributor \
  --scopes /subscriptions/856eda9f-88e9-431a-8fc7-f21c3290f493/resourceGroups/rg-aks-lab \
  --sdk-auth

# 2. Obtener todos los valores necesarios
cd terraform
echo "RESOURCE_GROUP: $(terraform output -raw resource_group)"
echo "AKS_CLUSTER: $(terraform output -raw aks_name)"
echo "ACR_LOGIN_SERVER: $(terraform output -raw acr_login_server)"
ACR_LOGIN_SERVER=$(terraform output -raw acr_login_server)
echo "REGISTRY_NAME: ${ACR_LOGIN_SERVER%.azurecr.io}"
```

