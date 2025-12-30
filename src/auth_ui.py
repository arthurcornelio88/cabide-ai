"""
Authentication UI components for Streamlit.
Provides login, logout, and user info display.
"""
import streamlit as st
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
    st.info("Para usar o Google Drive e a API, você precisa fazer login com sua conta Google.")

    # Initialize session state for OAuth flow
    if "oauth_flow" not in st.session_state:
        st.session_state.oauth_flow = None

    # Step 1: Show login button
    if st.session_state.oauth_flow is None:
        if st.button("🔑 Login com Google", use_container_width=True, type="primary"):
            # Generate auth URL
            auth_url, flow = oauth_helper.get_auth_url()
            st.session_state.oauth_flow = flow

            # Show instructions
            st.markdown("### Instruções:")
            st.markdown(f"1. **[Clique aqui para autorizar]({auth_url})**")
            st.markdown("2. Faça login com sua conta Google")
            st.markdown("3. Copie o código de autorização")
            st.markdown("4. Cole o código abaixo e clique em 'Confirmar'")

            st.rerun()

    # Step 2: Show code input after user clicks login
    if st.session_state.oauth_flow is not None:
        st.markdown("### Cole o código de autorização:")

        code = st.text_input(
            "Código:",
            placeholder="Cole aqui o código que você copiou",
            key="auth_code"
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button("✅ Confirmar", use_container_width=True, disabled=not code):
                try:
                    with st.spinner("Autenticando..."):
                        # Exchange code for credentials
                        creds = oauth_helper.save_credentials_from_code(
                            st.session_state.oauth_flow,
                            code.strip()
                        )

                        # Clear the flow
                        st.session_state.oauth_flow = None

                        st.success("✅ Login realizado com sucesso!")
                        st.balloons()
                        st.rerun()

                except Exception as e:
                    st.error(f"❌ Erro ao fazer login: {e}")
                    st.error("Verifique se você copiou o código corretamente e tente novamente.")

        with col2:
            if st.button("❌ Cancelar", use_container_width=True):
                st.session_state.oauth_flow = None
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
