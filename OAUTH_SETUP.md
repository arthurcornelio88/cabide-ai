# OAuth Google Setup Guide

## Passo 1: Criar Credenciais OAuth no Google Cloud Console

1. **Acesse**: https://console.cloud.google.com
2. **Selecione ou crie um projeto** (pode usar o mesmo projeto da service account)
3. **Ative as APIs necessárias**:
   - Google Drive API (já deve estar ativa)
   - Google+ API (para user info)

4. **Crie Credenciais OAuth**:
   - Vá em: **APIs & Services** > **Credentials**
   - Clique em: **Create Credentials** > **OAuth client ID**

5. **Configure a Tela de Consentimento OAuth** (se ainda não fez):
   - Clique em **Configure Consent Screen**
   - Escolha **External** (para contas pessoais Gmail)
   - Preencha:
     - App name: `Cabide AI`
     - User support email: seu email
     - Developer contact: seu email
   - **Scopes**: Clique em "Add or Remove Scopes" e adicione:
     - `https://www.googleapis.com/auth/drive.file`
     - `https://www.googleapis.com/auth/userinfo.email`
     - `https://www.googleapis.com/auth/userinfo.profile`
   - **Test users**: Adicione seu email e o da sua mãe
   - Clique em "Save and Continue" até terminar

6. **Crie o OAuth Client ID**:
   - Volte para **Credentials** > **Create Credentials** > **OAuth client ID**
   - Application type: **Web application** ⚠️ IMPORTANTE: Use Web application para funcionar no Streamlit Cloud!
   - Name: `Cabide AI Web`
   - **Authorized redirect URIs**: Adicione os seguintes URIs:
     - `https://cabide-api-678226806758.southamerica-east1.run.app/oauth/callback` (para produção)
     - `http://localhost:8080` (para desenvolvimento local)
   - Clique em **Create**

   ✅ Pronto! Agora funciona tanto localmente quanto no Streamlit Cloud.

7. **Baixe o arquivo JSON**:
   - Clique no botão **Download JSON** (ícone de download)
   - Renomeie o arquivo para: **`client_secret.json`**
   - Coloque na raiz do projeto: `/home/arthurcornelio/code/arthurcornelio88/cabide-ai/`

## Passo 2: Estrutura Final de Arquivos

```
cabide-ai/
├── client_secret.json          # OAuth credentials (você vai criar)
├── gcp-service-account.json    # Service account (já existe)
├── auth_token.pickle           # Token OAuth (criado automaticamente no login)
├── user_info.json              # Info do usuário (criado automaticamente)
└── .env
```

## Passo 3: Testar

Depois que criar o `client_secret.json`, rode:

```bash
streamlit run src/app.py
```

Na primeira vez, vai aparecer uma UI de login. Siga as instruções!

## Notas Importantes

- **OAuth vs Service Account**:
  - Service Account: Não tem quota própria (causa erro 403)
  - OAuth: Usa a quota do usuário logado ✅

- **Segurança**:
  - `client_secret.json`: ⚠️ NUNCA commite no git (contém client secret que deve ser mantido privado)
  - `auth_token.pickle`: NUNCA commite (contém token de acesso)
  - `user_info.json`: NUNCA commite (contém dados pessoais)

- **Múltiplos Usuários**:
  - Cada pessoa que usar a app precisa fazer login uma vez
  - O token fica salvo localmente
  - Válido por ~1 semana, depois renova automaticamente

## Passo 4: Deploy no Streamlit Cloud

Para fazer deploy no Streamlit Cloud, você precisa configurar o `client_secret.json` como um **Secret**:

1. **No Streamlit Cloud Dashboard**:
   - Vá em: **Your app** > **Settings** > **Secrets**

2. **Adicione o secret `CLIENT_SECRET_JSON`**:
   - Cole o conteúdo completo do arquivo `client_secret.json` como uma string
   - O formato deve ser (note que agora é `"web"` em vez de `"installed"`):
   ```toml
   CLIENT_SECRET_JSON = '{"web":{"client_id":"...","project_id":"...","auth_uri":"...","token_uri":"...","auth_provider_x509_cert_url":"...","client_secret":"...","redirect_uris":["https://...",""http://localhost:8080"]}}'
   ```

3. **Exemplo de configuração**:
   ```toml
   # Em Streamlit Cloud > Settings > Secrets
   CLIENT_SECRET_JSON = '{"web":{"client_id":"YOUR-CLIENT-ID.apps.googleusercontent.com","project_id":"gen-lang-client-0410722440","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_secret":"YOUR-CLIENT-SECRET","redirect_uris":["https://cabide-api-678226806758.southamerica-east1.run.app/oauth/callback","http://localhost:8080"]}}'
   ```

   **Dica**: Abra o arquivo `client_secret.json` local, copie todo o conteúdo, coloque entre aspas simples.

4. **Adicione também o `BACKEND_URL`**:
   ```toml
   BACKEND_URL = "https://cabide-api-678226806758.southamerica-east1.run.app"
   ```
   (Use a URL do seu backend Cloud Run, **sem** a barra final)

5. **Adicione outros secrets necessários** (GEMINI_API_KEY, GDRIVE_FOLDER_ID, etc.)

6. **Salve e reinicie o app**

⚠️ **IMPORTANTE**:
- Copie o JSON completo em uma única linha
- Certifique-se de que está entre aspas simples `'...'`
- Não adicione quebras de linha no meio do JSON

**Como funciona**:
- Localmente: O código lê o arquivo `client_secret.json`
- No Streamlit Cloud: O código lê de `st.secrets['CLIENT_SECRET_JSON']`
- A detecção é automática! 🎉

## Passo 5: Segurança do Backend (Acesso Público para OAuth)

⚠️ **IMPORTANTE**: O backend Cloud Run precisa ter **acesso público** habilitado para que o OAuth funcione.

### Por que o acesso público é necessário?

O fluxo OAuth funciona assim:
1. Usuário clica em "Login com Google" no Streamlit
2. Google redireciona o usuário para `https://seu-backend.run.app/oauth/callback`
3. **O navegador do usuário acessa diretamente esse endpoint** (não o Streamlit)
4. O endpoint retorna o código de autorização para o usuário copiar

Se o backend estiver com autenticação IAM, o navegador do usuário receberá erro 403 Forbidden.

### Como habilitar acesso público:

Se você usou o script `scripts/setup_brazil_infra.sh`, o acesso público já está configurado.

Se não, execute:

```bash
gcloud run services add-iam-policy-binding cabide-api \
  --region=southamerica-east1 \
  --member="allUsers" \
  --role="roles/run.invoker"
```

### Isso é seguro?

✅ **Sim**, desde que você implemente autenticação nos endpoints sensíveis:

- **`/oauth/callback`**: Endpoint público (não processa dados sensíveis, apenas mostra o código)
- **`/generate`**: Protegido com verificação de token OAuth
- **`/health`**: Endpoint público (apenas status)

O código já implementa verificação de token OAuth nos endpoints que processam dados:
- Ver [src/api.py:40-90](src/api.py#L40-L90) para verificação de token
- Ver [src/api.py:141](src/api.py#L141) para uso da proteção no `/generate`

### Alternativa (não recomendado):

Você poderia usar autenticação IAM e fazer o Streamlit chamar o backend com credenciais, mas:
- ❌ Mais complexo de configurar
- ❌ Requer gerenciar chaves de service account no Streamlit
- ❌ OAuth callback ainda precisaria de um endpoint público separado

A solução atual (backend público + autenticação OAuth por endpoint) é mais simples e segura.
