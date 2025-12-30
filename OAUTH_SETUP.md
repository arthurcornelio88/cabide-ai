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
   - Application type: **Desktop app** ⚠️ IMPORTANTE: tem que ser Desktop app!
   - Name: `Cabide AI Desktop`
   - **Authorized domains**: deixe vazio (ou adicione só `localhost` sem http://)
   - Clique em **Create**

   ✅ Pronto! O tipo "Desktop app" já permite usar `http://localhost` automaticamente.
   ❌ NÃO precisa adicionar redirect URIs manualmente!

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
  - `client_secret.json`: Pode commitar no git (é público em desktop apps)
  - `auth_token.pickle`: NUNCA commite (contém token de acesso)
  - `user_info.json`: NUNCA commite (contém dados pessoais)

- **Múltiplos Usuários**:
  - Cada pessoa que usar a app precisa fazer login uma vez
  - O token fica salvo localmente
  - Válido por ~1 semana, depois renova automaticamente
