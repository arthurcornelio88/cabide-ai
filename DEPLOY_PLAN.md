# Plano de Deploy: Migração para Streamlit Cloud + Cloud Run

## 📋 Resumo Executivo

**Objetivo:** Migrar a arquitetura atual (dual Cloud Run) para uma arquitetura híbrida:
- **Frontend:** Streamlit Cloud (gratuito, simples)
- **Backend API:** Cloud Run no GCP (pago, mas necessário)
- **Projeto GCP:** `gen-lang-client-0410722440`
- **Região:** `southamerica-east1` (São Paulo)

## 🎯 Decisões do Usuário

1. ✅ Frontend no Streamlit Cloud (ao invés de Cloud Run)
2. ✅ Expandir `setup_brazil_infra.sh` para setup completo
3. ✅ Remover todas as referências a GCS (Google Cloud Storage)
4. ✅ Renomear branch `master` → `main`
5. ✅ Projeto GCP: `gen-lang-client-0410722440`

## 🏗️ Arquitetura Atual vs Nova

### Atual (Problemático)
```
┌─────────────────────────────────────┐
│   GitHub Actions (não funciona)     │
│   Trigger: push to "main"           │
│   Repo Branch: "master" ❌          │
└─────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│    Cloud Run (São Paulo)            │
│  ┌───────────┐    ┌──────────────┐  │
│  │ Frontend  │    │   Backend    │  │
│  │ cabide-ui │───▶│  cabide-api  │  │
│  │ (pago 💰) │    │   (pago 💰)  │  │
│  └───────────┘    └──────────────┘  │
└─────────────────────────────────────┘
```

### Nova (Otimizada)
```
┌─────────────────────────────────────┐
│      GitHub (branch: main)          │
└──────┬──────────────────┬───────────┘
       │                  │
       │                  │
       ▼                  ▼
┌──────────────┐   ┌─────────────────┐
│  Streamlit   │   │ GitHub Actions  │
│    Cloud     │   │  Auto Deploy    │
│  (FREE 🎉)   │   └────────┬────────┘
│              │            │
│  Frontend    │            ▼
│   Deploy     │   ┌─────────────────┐
│ Automático   │   │   Cloud Run     │
└──────┬───────┘   │  (São Paulo)    │
       │           │                 │
       │           │  Backend API    │
       └──────────▶│  cabide-api     │
         HTTPS     │  (pago 💰)      │
                   └─────────────────┘
```

## 📝 Mudanças Necessárias

### 1. GitHub Actions Workflow

**Arquivo:** `.github/workflows/deploy.yml`

**Mudanças:**
- ✏️ Mudar trigger de `"main"` para `"main"` (OK, já será main depois do rename)
- ❌ Remover todo o job de build/deploy do frontend
- ❌ Remover variáveis `GCS_BUCKET`, `STORAGE_MODE=prod`
- ✏️ Atualizar `PROJECT_ID` para usar `gen-lang-client-0410722440`
- ✏️ Simplificar para deploy apenas do backend

**Novo fluxo:**
1. Checkout do código
2. Autenticação no GCP
3. Build da imagem Docker do backend
4. Push para Artifact Registry
5. Deploy no Cloud Run (cabide-api)

### 2. Script de Infraestrutura

**Arquivo:** `src/setup_brazil_infra.sh`

**Expandir para incluir:**
- ✅ Enable de todas as APIs necessárias
- ✅ Criação do Artifact Registry
- ✅ Criação do serviço Cloud Run inicial
- ✅ Configuração de IAM bindings
- ✅ Validação de permissões

**Novo conteúdo:**
```bash
#!/bin/bash
# Complete setup script for Cabide AI infrastructure

PROJECT_ID="gen-lang-client-0410722440"
REGION="southamerica-east1"
REPO_NAME="cabide-repo"
SERVICE_NAME="cabide-api"

# 1. Set project
gcloud config set project $PROJECT_ID

# 2. Enable APIs
gcloud services enable \
    artifactregistry.googleapis.com \
    run.googleapis.com \
    drive.googleapis.com \
    aiplatform.googleapis.com

# 3. Create Artifact Registry
gcloud artifacts repositories create $REPO_NAME \
    --repository-format=docker \
    --location=$REGION \
    --description="Docker repository for Cabide AI Backend"

# 4. Create Cloud Run service (initial placeholder)
gcloud run deploy $SERVICE_NAME \
    --image=us-docker.pkg.dev/cloudrun/container/hello \
    --region=$REGION \
    --platform=managed \
    --allow-unauthenticated

echo "✅ Infrastructure setup complete!"
echo "Registry: $REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME"
echo "Service: https://console.cloud.google.com/run?project=$PROJECT_ID"
```

### 3. Limpeza de GCS

**Arquivos afetados:**
- `.github/workflows/deploy.yml` - Remover env vars `GCS_BUCKET_NAME`, `STORAGE_MODE`
- `src/config.py` - Já está limpo (força local mode na linha 62)
- `deploy.md` - Atualizar documentação

**Variáveis a remover do deploy:**
```yaml
# ❌ REMOVER:
STORAGE_MODE=prod
GCS_BUCKET_NAME=${{ env.GCS_BUCKET }}
```

### 4. Configuração Streamlit Cloud

**Não requer mudança de código**, mas precisará de configuração manual:

**Secrets no Streamlit Cloud:**
```
BACKEND_URL=https://cabide-api-XXXXX-rj.a.run.app
GEMINI_API_KEY=<from GitHub secrets>
GCP_SERVICE_ACCOUNT_JSON=<from GitHub secrets>
GDRIVE_FOLDER_ID=<from GitHub secrets>
```

**Arquivo a criar (opcional):** `.streamlit/config.toml`
```toml
[server]
port = 8501
enableCORS = false

[theme]
primaryColor = "#FF6B6B"
backgroundColor = "#FFFFFF"
```

### 5. Renomear Branch master → main

**Comandos Git:**
```bash
# Local
git branch -m master main

# Push e set upstream
git push -u origin main

# Deletar master remoto
git push origin --delete master

# Atualizar default branch no GitHub UI
# Settings → Branches → Default branch → main
```

### 6. Atualização do deploy.md

**Arquivo:** `deploy.md`

**Mudanças:**
- ✏️ Item #2: Atualizar PROJECT_ID para `gen-lang-client-0410722440`
- ✏️ Item #2: Marcar script como expandido
- ✅ Item #11: Marcar como completo (Streamlit Cloud)
- ➕ Adicionar seção "Streamlit Cloud Setup"

## 🔧 Arquivos Críticos a Modificar

### 1. `.github/workflows/deploy.yml`
**Linha 5:** `branches: [ "main" ]` (já está correto, manterá após rename)
**Linha 8:** `PROJECT_ID: "gen-lang-client-0410722440"` (hardcoded, não secret)
**Linhas 47-56:** ❌ Deletar job de build frontend
**Linhas 73-87:** ❌ Deletar job de deploy frontend
**Linhas 68-71:** ❌ Remover `STORAGE_MODE` e `GCS_BUCKET_NAME`

### 2. `src/setup_brazil_infra.sh`
**Completo rewrite** - Expandir de 27 linhas para ~50 linhas

### 3. `deploy.md`
**Linha 27-28:** Atualizar status do script
**Linha 32:** Marcar item #11 como completo
**Final do arquivo:** Adicionar seção Streamlit Cloud

### 4. `.github/workflows/ci.yml`
**Linha 4:** Verificar se também precisa mudar de `main` para `main` ou `master`

### 5. `Dockerfile.frontend`
**Ação:** Manter no repo (não deletar) para referência, mas não será mais usado pelo CI/CD

## 📦 GitHub Secrets Necessários

### Já Configurados (verificar se corretos):
- `GCP_PROJECT_ID` → Atualizar para `gen-lang-client-0410722440`
- `GCP_SA_KEY` → Service Account JSON com roles corretas
- `GEMINI_API_KEY` → API Key do AI Studio
- `GCP_SERVICE_ACCOUNT_JSON` → Same as GCP_SA_KEY
- `GDRIVE_FOLDER_ID` → ID da pasta no Drive

### Roles Necessárias para Service Account:
- `Cloud Run Admin`
- `Artifact Registry Writer`
- `Service Account User`
- `Storage Admin` (se reativar GCS no futuro)

## 🧪 Plano de Teste

### Fase 1: Infraestrutura
1. ✅ Executar `bash src/setup_brazil_infra.sh`
2. ✅ Verificar Artifact Registry criado
3. ✅ Verificar Cloud Run service placeholder criado

### Fase 2: Branch Rename
1. ✅ Renomear local `master` → `main`
2. ✅ Push para origin
3. ✅ Deletar `master` remoto
4. ✅ Atualizar default branch no GitHub

### Fase 3: Backend Deploy
1. ✅ Fazer pequena mudança no código
2. ✅ Git push para `main`
3. ✅ Verificar GitHub Actions executou
4. ✅ Verificar imagem no Artifact Registry
5. ✅ Verificar serviço rodando no Cloud Run
6. ✅ Testar endpoint: `curl https://cabide-api-XXXXX.a.run.app/health`

### Fase 4: Streamlit Cloud
1. ✅ Conectar repo no Streamlit Cloud
2. ✅ Configurar secrets
3. ✅ Apontar para `src/app.py`
4. ✅ Deploy automático
5. ✅ Testar conexão com backend

### Fase 5: Integração E2E
1. ✅ Fazer upload de imagem pelo Streamlit
2. ✅ Verificar API processa
3. ✅ Verificar imagem aparece no Google Drive
4. ✅ Verificar resposta retorna ao frontend

## ⚠️ Rollback Plan

### Se deploy falhar:

**Backend:**
```bash
# Reverter para versão anterior
gcloud run services update cabide-api \
  --image=southamerica-east1-docker.pkg.dev/gen-lang-client-0410722440/cabide-repo/backend:PREVIOUS_SHA \
  --region=southamerica-east1
```

**Frontend:**
- Streamlit Cloud tem versionamento automático
- Usar UI para rollback para commit anterior

**Branch:**
```bash
# Se precisar reverter master→main
git branch -m main master
git push -f origin master
git push origin --delete main
```

## 🗑️ Limpeza Pós-Migração

**Após confirmação que tudo funciona:**

1. ❌ Deletar serviço Cloud Run `cabide-ui` (frontend antigo):
   ```bash
   gcloud run services delete cabide-ui --region=southamerica-east1
   ```

2. ❌ Remover imagens antigas do frontend no Artifact Registry:
   ```bash
   gcloud artifacts docker images delete \
     southamerica-east1-docker.pkg.dev/gen-lang-client-0410722440/cabide-repo/frontend:latest
   ```

3. 📝 Atualizar README.md com nova arquitetura

## 🚀 Ordem de Execução Recomendada

```
1. Renomear branch (master → main)
2. Atualizar GitHub Secrets (PROJECT_ID)
3. Executar setup_brazil_infra.sh (criar infra)
4. Modificar .github/workflows/deploy.yml (remover frontend)
5. Limpar referências GCS
6. Commit + Push (trigger deploy do backend)
7. Configurar Streamlit Cloud
8. Testar integração completa
9. Limpar recursos antigos (cabide-ui)
10. Atualizar documentação
```

## 📊 Impacto de Custos

### Antes:
- Cloud Run Backend: ~$5-15/mês
- Cloud Run Frontend: ~$5-10/mês
- **Total: ~$10-25/mês**

### Depois:
- Cloud Run Backend: ~$5-15/mês
- Streamlit Cloud: **$0/mês** ✨
- **Total: ~$5-15/mês** (economia de 40-50%)

## ✅ Checklist Final

- [ ] Branch renomeado (master → main)
- [ ] GitHub Secret PROJECT_ID atualizado
- [ ] setup_brazil_infra.sh expandido e executado
- [ ] deploy.yml modificado (sem frontend, sem GCS)
- [ ] ci.yml atualizado (branches corretas)
- [ ] Backend deployado com sucesso
- [ ] Streamlit Cloud configurado
- [ ] Secrets configurados no Streamlit Cloud
- [ ] Teste E2E passou
- [ ] Serviço cabide-ui deletado
- [ ] deploy.md atualizado
- [ ] TODO.md item #11 marcado como completo

---

**Duração Estimada:** 1-2 horas
**Risco:** Baixo (temos rollback para tudo)
**Benefício:** Deploy automático + economia de custos + simplicidade
