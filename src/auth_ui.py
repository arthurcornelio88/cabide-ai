"""
Authentication UI components for Streamlit.
Provides login, logout, and user info display.
"""

import streamlit as st

from src.config import get_settings
from src.oauth_helper import UnifiedOAuthHelper


def show_login_ui(oauth_helper: UnifiedOAuthHelper):
    """
    Display login UI and handle OAuth flow.

    Args:
        oauth_helper: OAuth helper instance

    Returns:
        True if user is authenticated, False otherwise
    """
    st.markdown("---")
    st.subheader("🔐 Login Necessário")
    st.info(
        "Para usar o Google Drive e a API, você precisa fazer login com sua conta Google."
    )

    # Initialize session state for auth URL
    if "oauth_auth_url" not in st.session_state:
        st.session_state.oauth_auth_url = None
    if "oauth_redirect_uri" not in st.session_state:
        st.session_state.oauth_redirect_uri = None

    # Step 1: Generate and show auth URL
    if st.session_state.oauth_auth_url is None:
        if st.button(
            "🔑 Gerar Link de Login", use_container_width=True, type="primary"
        ):
            try:
                # Get backend URL from settings
                settings = get_settings()
                redirect_uri = None
                if settings.backend_url:
                    redirect_uri = f"{settings.backend_url}/oauth/callback"

                # Generate auth URL with appropriate redirect
                auth_url, _ = oauth_helper.get_auth_url(redirect_uri=redirect_uri)
                st.session_state.oauth_auth_url = auth_url
                st.session_state.oauth_redirect_uri = redirect_uri
                st.rerun()
            except Exception as e:
                st.error(f"❌ Erro ao gerar link: {e}")

    # Step 2: Show URL and wait for user to authorize
    if st.session_state.oauth_auth_url is not None:
        st.markdown("### 📋 Instruções:")
        st.markdown("1. **Clique no link abaixo** para abrir o Google:")

        # Show clickable link
        st.markdown(
            f"### 🔗 [{st.session_state.oauth_auth_url}]({st.session_state.oauth_auth_url})"
        )

        st.markdown("2. **Faça login** com sua conta Google")
        st.markdown("3. **Autorize** o acesso ao Cabide AI")

        # Different instructions based on redirect URI
        if (
            st.session_state.oauth_redirect_uri
            and "oauth/callback" in st.session_state.oauth_redirect_uri
        ):
            st.markdown("4. Você verá uma página com um **código de autorização**")
            st.markdown("5. **Copie o código** e cole abaixo:")
            placeholder_text = "4/0ATX87lO2i..."
            input_label = "Cole o código aqui:"
        else:
            st.markdown(
                "4. Você será redirecionado para uma página de erro (isso é normal!)"
            )
            st.markdown("5. **Copie a URL completa** da barra de endereço")
            st.markdown("6. **Cole abaixo**:")
            placeholder_text = "http://localhost:8080/?code=4/0A...&scope=..."
            input_label = "Cole a URL completa aqui:"

        # Input for code or URL
        user_input = st.text_input(
            input_label,
            placeholder=placeholder_text,
            key="auth_input",
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button(
                "✅ Confirmar", use_container_width=True, disabled=not user_input
            ):
                try:
                    with st.spinner("Autenticando..."):
                        # Check if input is a URL or just a code
                        if user_input.startswith("http"):
                            # Extract code from URL
                            import urllib.parse

                            parsed = urllib.parse.urlparse(user_input)
                            params = urllib.parse.parse_qs(parsed.query)

                            if "code" not in params:
                                st.error(
                                    "❌ URL inválida. Certifique-se de copiar a URL completa!"
                                )
                                return
                            code = params["code"][0]
                        else:
                            # Assume it's just the code
                            code = user_input.strip()

                        # Create new flow and exchange code
                        _, flow = oauth_helper.get_auth_url(
                            redirect_uri=st.session_state.oauth_redirect_uri
                        )
                        oauth_helper.save_credentials_from_code(flow, code)

                        # Clear session state
                        st.session_state.oauth_auth_url = None
                        st.session_state.oauth_redirect_uri = None

                        st.success("✅ Login realizado com sucesso!")
                        st.balloons()
                        st.rerun()

                except Exception as e:
                    st.error(f"❌ Erro ao fazer login: {e}")
                    st.error("Verifique se você copiou o código/URL corretamente.")

        with col2:
            if st.button("❌ Cancelar", use_container_width=True):
                st.session_state.oauth_auth_url = None
                st.session_state.oauth_redirect_uri = None
                st.rerun()

    return False


def show_user_info(oauth_helper: UnifiedOAuthHelper):
    """
    Display logged-in user info in sidebar.

    Args:
        oauth_helper: OAuth helper instance
    """
    user_info = oauth_helper.get_user_info()

    if user_info:
        with st.sidebar:
            st.markdown("---")
            st.markdown("### 👤 Usuário")

            # Show profile picture if available
            if "picture" in user_info:
                st.image(user_info["picture"], width=60)

            st.markdown(f"**{user_info.get('name', 'Usuário')}**")
            st.markdown(f"`{user_info.get('email', '')}`")

            if st.button("🚪 Logout", use_container_width=True):
                oauth_helper.revoke_authentication()
                st.rerun()


def require_authentication(oauth_helper: UnifiedOAuthHelper) -> bool:
    """
    Check if user is authenticated and show login UI if not.

    Args:
        oauth_helper: OAuth helper instance

    Returns:
        True if authenticated, False otherwise
    """
    if oauth_helper.is_authenticated():
        show_user_info(oauth_helper)
        return True
    else:
        # Show login UI
        st.title("👗 Cabide AI")
        show_login_ui(oauth_helper)
        st.stop()  # Stop execution until user is authenticated
        return False
