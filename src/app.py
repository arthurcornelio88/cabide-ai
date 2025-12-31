import io
import os

import requests
import streamlit as st

from src.api_client import CabideAPIClient
from src.auth_ui import require_authentication
from src.config import Settings, get_settings
from src.driver_service import DriveService
from src.engine import FashionEngine
from src.oauth_helper import UnifiedOAuthHelper

# --- Page Configuration ---
st.set_page_config(
    page_title="Cabide AI - Professional Catalog", page_icon="👗", layout="centered"
)


# --- Singleton-style Initialization ---
@st.cache_resource
def get_engine(_version="1.3.0-feedback"):
    return FashionEngine()


@st.cache_resource
def get_oauth_helper():
    """Initialize OAuth helper singleton."""
    return UnifiedOAuthHelper()


@st.cache_resource
def get_drive_manager(_settings: Settings, _oauth_helper: UnifiedOAuthHelper):
    """
    Initializes DriveService using OAuth credentials.
    The underscore prefix tells Streamlit not to hash this object.
    """
    if _settings.gdrive_folder_id:
        try:
            creds = _oauth_helper.get_credentials()
            if creds:
                return DriveService(creds, _settings.gdrive_folder_id)
            else:
                print("Warning: GDRIVE_FOLDER_ID set but no OAuth credentials found")
        except Exception as e:
            st.error(f"Failed to initialize Drive Service: {e}")
    return None


# Load Resources
settings = get_settings()
oauth_helper = get_oauth_helper()

# Require authentication before proceeding
require_authentication(oauth_helper)

# Initialize resources with OAuth
engine = get_engine()
drive_manager = get_drive_manager(settings, oauth_helper)

# Initialize API client if backend URL is configured
api_client = None
if settings.backend_url:
    try:
        # Get OAuth access token for API authentication
        access_token = oauth_helper.get_access_token()
        api_client = CabideAPIClient(settings.backend_url, access_token=access_token)
        api_status = api_client.health_check()
        st.sidebar.success(f"✅ API Connected: v{api_status.get('version', 'unknown')}")
    except Exception as e:
        st.sidebar.warning(f"⚠️ API unavailable: {e}\nUsing direct engine mode")
        api_client = None

# --- UI Header ---
st.title("👗 Cabide AI")
st.markdown("### Gerador de Catálogo Profissional para o Cabide da Ieié")

# --- UI Controls ---
with st.expander("🎨 Scene Customization", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        # Map PT labels to values for the engine
        env_labels = {
            "Praia (Beach)": "beach",
            "Floresta (Forest)": "forest",
            "Cidade (Urban Street)": "urban street",
            "Parque (Park)": "park",
            "Festa (Party)": "luxury party ballroom",
            "Escritório (Office)": "office",
            "Congresso (Congress Hall)": "congress hall",
            "Consultório (Medical Office)": "medical office",
        }
        selected_env_label = st.selectbox("Select Environment", list(env_labels.keys()))
        env_value = env_labels[selected_env_label]

    with col2:
        # Activity selection
        activity_labels = {
            "Caminhando (Walking)": "walking",
            "Lendo (Reading)": "reading",
            "Tomando Café (Coffee)": "holding a coffee",
            "Posando (Posing)": "posing elegantly",
            "No Celular (On Phone)": "checking phone",
            "Fazendo Apresentação (Presenting)": "standing and presenting to an audience with confident body language",
            "Atendendo Cliente (Attending Client)": "attending to a client",
        }
        selected_act_label = st.selectbox(
            "Model Activity", list(activity_labels.keys())
        )
        act_value = activity_labels[selected_act_label]

# --- Garment Metadata Section ---
with st.expander("📋 Dados da Peça", expanded=True):
    col_num, col_type, col_position = st.columns(3)
    with col_num:
        garment_number = st.text_input(
            "Número da Peça *",
            placeholder="Ex: 100",
            help="Número único da peça para o catálogo",
        )
    with col_type:
        garment_type = st.selectbox(
            "Tipo da Peça *",
            [
                "",
                "Vestido",
                "Vestido de Festa",
                "Calça",
                "Camisa",
                "Saia",
                "Sapato",
                "Écharpe",
                "Bracelete",
                "Veste",
                "Conjunto",
                "Vestido com Modelo",
            ],
            help="Selecione o tipo de roupa. 'Vestido com Modelo' = trocar apenas o fundo",
        )
    with col_position:
        if garment_type == "Vestido com Modelo":
            position = "Frente"  # Default, not used for background replacement
            st.text_input(
                "Posição",
                value="N/A",
                disabled=True,
                help="Não aplicável para troca de fundo",
            )
        else:
            position = st.selectbox(
                "Posição (Opcional)",
                ["Frente", "Costas", "Ambos"],
                help="Útil para vestidos e peças com frente/costas diferentes. Se não enviar costas, usamos a frente.",
            )

# --- Conjunto Composition (Conditional) ---
piece1_type = None
piece2_type = None
piece3_type = None
if garment_type == "Conjunto":
    with st.expander("👔 Composição do Conjunto", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            piece1_type = st.selectbox(
                "Peça Superior *",
                ["", "Camisa", "Blusa"],
                help="Parte de cima do conjunto (obrigatório)",
            )
        with col2:
            piece2_type = st.selectbox(
                "Peça Inferior *",
                ["", "Calça", "Saia"],
                help="Parte de baixo do conjunto (obrigatório)",
            )
        with col3:
            piece3_type = st.selectbox(
                "Peça Adicional (Opcional)",
                ["", "Veste", "Sapato", "Écharpe", "Bracelete", "Colar"],
                help="Veste, sapato, acessório ou complemento (opcional)",
            )

# --- Model Attributes (Optional) ---
model_height = None
model_body_type = None
model_skin_tone = None
model_hair_length = None
model_hair_texture = None
model_hair_color = None
model_hair_style = None

with st.expander("👤 Características da Modelo (Opcional)", expanded=False):
    st.caption(
        "Personalize a aparência da modelo virtual. Se não preencher, usaremos características aleatórias."
    )

    col1, col2 = st.columns(2)
    with col1:
        model_height = st.selectbox(
            "Altura", ["", "Baixa", "Média", "Alta"], help="Estatura da modelo"
        )
        model_body_type = st.selectbox(
            "Tipo Físico",
            ["", "Esguia", "Média", "Plus Size"],
            help="Biotipo da modelo",
        )
        model_skin_tone = st.selectbox(
            "Tom de Pele",
            [
                "",
                "Pele Clara",
                "Pele Média",
                "Pele Morena",
                "Pele Escura",
                "Pele Negra",
            ],
            help="Tonalidade de pele",
        )

    with col2:
        model_hair_length = st.selectbox(
            "Cabelo - Comprimento",
            ["", "Curto", "Médio", "Longo"],
            help="Comprimento do cabelo",
        )
        model_hair_texture = st.selectbox(
            "Cabelo - Textura",
            ["", "Liso", "Ondulado", "Cacheado", "Crespo"],
            help="Textura natural do cabelo",
        )
        model_hair_color = st.selectbox(
            "Cabelo - Cor",
            ["", "Loiro", "Castanho", "Ruivo", "Preto", "Grisalho"],
            help="Cor do cabelo",
        )
        model_hair_style = st.selectbox(
            "Cabelo - Estilo",
            ["", "Solto", "Preso", "Coque", "Rabo de Cavalo"],
            help="Estilo do penteado",
        )

# --- File Upload Section ---
# Multi-file upload for Front/Back support or Conjunto pieces
if garment_type == "Conjunto":
    num_pieces = 2 if not piece3_type else 3
    st.info(
        f"📸 Envie {num_pieces} fotos separadas na ordem: 1) {piece1_type or 'Peça Superior'}, 2) {piece2_type or 'Peça Inferior'}"
        + (f", 3) {piece3_type}" if piece3_type else "")
    )
elif garment_type == "Vestido com Modelo":
    st.info(
        "📸 Envie 1 foto do vestido já vestido na modelo. O sistema irá trocar apenas o fundo/ambiente."
    )
else:
    upload_help_text = {
        "Frente": "Envie 1 ou mais fotos da frente",
        "Costas": "Envie 1 ou mais fotos das costas",
        "Ambos": "Envie 2 fotos: frente e costas (recomendado para vestidos)",
    }
    st.info(
        f"📸 {upload_help_text.get(position, 'Envie as fotos da peça')} • Se não tiver foto das costas, usamos a frente."
    )

uploaded_files = st.file_uploader(
    "Envie fotos da peça (1 ou 2 fotos)",
    type=["png", "jpg", "jpeg", "heic", "heif"],
    accept_multiple_files=True,
)

if st.button("✨ Gerar foto profissional", use_container_width=True):
    if uploaded_files:
        # Validate metadata
        if not garment_number or not garment_number.strip():
            st.error("⚠️ Por favor, preencha o Número da Peça")
        elif not garment_type:
            st.error("⚠️ Por favor, selecione o Tipo da Peça")
        elif garment_type == "Conjunto" and (not piece1_type or not piece2_type):
            st.error(
                "⚠️ Por favor, selecione a Peça Superior e Peça Inferior do conjunto"
            )
        elif garment_type == "Conjunto":
            expected_photos = 2 if not piece3_type else 3
            if len(uploaded_files) != expected_photos:
                st.error(
                    f"⚠️ Por favor, envie exatamente {expected_photos} fotos para o conjunto ({len(uploaded_files)} enviada(s))"
                )
            else:
                # Conjunto validation passed - proceed with generation
                with st.spinner("Banana Pro is generating your image..."):
                    try:
                        # Determine mode: API or Direct Engine
                        use_api = api_client is not None and settings.backend_url

                        if use_api:
                            # API MODE: Call backend
                            # Save temp files for feedback regeneration
                            temp_paths = []
                            for idx, uploaded_file in enumerate(uploaded_files):
                                temp_name = f"temp_{idx}_{uploaded_file.name}"
                                with open(temp_name, "wb") as f:
                                    f.write(uploaded_file.getbuffer())
                                temp_paths.append(temp_name)

                            # Prepare conjunto metadata (for session state)
                            conjunto_data = None
                            if garment_type == "Conjunto":
                                conjunto_data = {
                                    "piece1_type": piece1_type,
                                    "piece2_type": piece2_type,
                                    "piece3_type": piece3_type,
                                }

                            # Prepare model attributes (for session state)
                            model_attrs = {
                                "height": model_height,
                                "body_type": model_body_type,
                                "skin_tone": model_skin_tone,
                                "hair_length": model_hair_length,
                                "hair_texture": model_hair_texture,
                                "hair_color": model_hair_color,
                                "hair_style": model_hair_style,
                            }
                            # Filter out empty values
                            model_attrs = {k: v for k, v in model_attrs.items() if v}

                            # Prepare all files for API
                            image_files = []
                            for uploaded_file in uploaded_files:
                                image_buffer = io.BytesIO(uploaded_file.getbuffer())
                                image_buffer.seek(0)
                                image_files.append((uploaded_file.name, image_buffer))

                            result = api_client.generate_photo(
                                image_files=image_files,
                                environment=env_value,
                                activity=act_value,
                                garment_number=garment_number.strip(),
                                garment_type=garment_type,
                                position=position,
                                piece1_type=piece1_type
                                if garment_type == "Conjunto"
                                else None,
                                piece2_type=piece2_type
                                if garment_type == "Conjunto"
                                else None,
                                piece3_type=piece3_type
                                if garment_type == "Conjunto" and piece3_type
                                else None,
                            )

                            if "url" in result:
                                # Production mode: Fetch from URL
                                response = requests.get(result["url"])
                                image_bytes = response.content
                            else:
                                # Local mode: Use returned bytes
                                image_bytes = result["image_bytes"]
                        else:
                            # DIRECT ENGINE MODE (current behavior)
                            # 1. Handle multiple temp files for the engine
                            temp_paths = []
                            for idx, uploaded_file in enumerate(uploaded_files):
                                temp_name = f"temp_{idx}_{uploaded_file.name}"
                                with open(temp_name, "wb") as f:
                                    f.write(uploaded_file.getbuffer())

                                # Convert HEIC to PNG if needed
                                if uploaded_file.name.lower().endswith(
                                    (".heic", ".heif")
                                ):
                                    try:
                                        from PIL import Image
                                        from pillow_heif import register_heif_opener

                                        register_heif_opener()
                                        img = Image.open(temp_name)

                                        # Convert to PNG
                                        png_name = f"temp_{idx}_converted.png"
                                        img.save(png_name, format="PNG")

                                        # Remove HEIC and use PNG
                                        os.remove(temp_name)
                                        temp_name = png_name
                                    except Exception as e:
                                        st.error(f"Failed to convert HEIC image: {e}")
                                        raise

                                temp_paths.append(temp_name)

                            # 2. Prepare conjunto metadata if applicable
                            conjunto_data = None
                            if garment_type == "Conjunto":
                                conjunto_data = {
                                    "piece1_type": piece1_type,
                                    "piece2_type": piece2_type,
                                    "piece3_type": piece3_type,
                                }

                            # 2.5. Prepare model attributes if provided
                            model_attrs = {
                                "height": model_height,
                                "body_type": model_body_type,
                                "skin_tone": model_skin_tone,
                                "hair_length": model_hair_length,
                                "hair_texture": model_hair_texture,
                                "hair_color": model_hair_color,
                                "hair_style": model_hair_style,
                            }
                            # Filter out empty values
                            model_attrs = {k: v for k, v in model_attrs.items() if v}

                            # 3. Call Engine (Handles single/list paths and front/back logic)
                            result = engine.generate_lifestyle_photo(
                                garment_path=temp_paths,
                                environment=env_value,
                                activity=act_value,
                                garment_number=garment_number.strip(),
                                garment_type=garment_type,
                                position=position,
                                conjunto_pieces=conjunto_data,
                                model_attributes=model_attrs if model_attrs else None,
                            )

                            # 3. Handle result data for Download/Drive
                            if isinstance(result, list):
                                result = result[0]  # Take first if multiple envs

                            if result.startswith("http"):
                                # Production Mode: Fetch from GCS
                                response = requests.get(result)
                                image_bytes = response.content
                            else:
                                # Local Mode: Read from disk
                                with open(result, "rb") as f:
                                    image_bytes = f.read()

                            # DON'T cleanup temp files yet - keep them for feedback/regeneration
                            # They will be cleaned up when a new generation starts

                        # 4. Display Results
                        st.success("Generation Complete!")

                        # Store in session state for feedback/regeneration
                        st.session_state.last_image_bytes = image_bytes
                        st.session_state.last_temp_paths = temp_paths
                        st.session_state.last_params = {
                            "env_value": env_value,
                            "act_value": act_value,
                            "garment_number": garment_number,
                            "garment_type": garment_type,
                            "position": position,
                            "conjunto_data": conjunto_data,
                            "model_attrs": model_attrs if model_attrs else None,
                            "selected_env_label": selected_env_label,
                            "selected_act_label": selected_act_label,
                        }

                    except Exception as e:
                        st.error(f"Engine Error: {e}")
        else:
            # Non-conjunto items
            # Optional: Show info if user selected "Ambos" but only uploaded 1 photo
            if position == "Ambos" and len(uploaded_files) == 1:
                st.info(
                    "ℹ️ Você selecionou 'Ambos' mas enviou apenas 1 foto. Vamos usar a mesma foto para frente e costas."
                )

            with st.spinner("Banana Pro is generating your image..."):
                try:
                    # Determine mode: API or Direct Engine
                    use_api = api_client is not None and settings.backend_url

                    if use_api:
                        # API MODE: Call backend
                        # Save temp files for feedback regeneration
                        temp_paths = []
                        for idx, uploaded_file in enumerate(uploaded_files):
                            temp_name = f"temp_{idx}_{uploaded_file.name}"
                            with open(temp_name, "wb") as f:
                                f.write(uploaded_file.getbuffer())
                            temp_paths.append(temp_name)

                        # Prepare conjunto metadata (for session state)
                        conjunto_data = None

                        # Prepare model attributes (for session state)
                        model_attrs = {
                            "height": model_height,
                            "body_type": model_body_type,
                            "skin_tone": model_skin_tone,
                            "hair_length": model_hair_length,
                            "hair_texture": model_hair_texture,
                            "hair_color": model_hair_color,
                            "hair_style": model_hair_style,
                        }
                        # Filter out empty values
                        model_attrs = {k: v for k, v in model_attrs.items() if v}

                        # Prepare all files for API
                        image_files = []
                        for uploaded_file in uploaded_files:
                            image_buffer = io.BytesIO(uploaded_file.getbuffer())
                            image_buffer.seek(0)
                            image_files.append((uploaded_file.name, image_buffer))

                        result = api_client.generate_photo(
                            image_files=image_files,
                            environment=env_value,
                            activity=act_value,
                            garment_number=garment_number.strip(),
                            garment_type=garment_type,
                            position=position,
                        )

                        if "url" in result:
                            # Production mode: Fetch from URL
                            response = requests.get(result["url"])
                            image_bytes = response.content
                        else:
                            # Local mode: Use returned bytes
                            image_bytes = result["image_bytes"]
                    else:
                        # DIRECT ENGINE MODE (current behavior)
                        # 1. Handle multiple temp files for the engine
                        temp_paths = []
                        for idx, uploaded_file in enumerate(uploaded_files):
                            temp_name = f"temp_{idx}_{uploaded_file.name}"
                            with open(temp_name, "wb") as f:
                                f.write(uploaded_file.getbuffer())

                            # Convert HEIC to PNG if needed
                            if uploaded_file.name.lower().endswith((".heic", ".heif")):
                                try:
                                    from PIL import Image
                                    from pillow_heif import register_heif_opener

                                    register_heif_opener()
                                    img = Image.open(temp_name)

                                    # Convert to PNG
                                    png_name = f"temp_{idx}_converted.png"
                                    img.save(png_name, format="PNG")

                                    # Remove HEIC and use PNG
                                    os.remove(temp_name)
                                    temp_name = png_name
                                except Exception as e:
                                    st.error(f"Failed to convert HEIC image: {e}")
                                    raise

                            temp_paths.append(temp_name)

                        # 2. Prepare conjunto metadata if applicable (will be None for non-conjunto)
                        conjunto_data = None

                        # 2.5. Prepare model attributes if provided
                        model_attrs = {
                            "height": model_height,
                            "body_type": model_body_type,
                            "skin_tone": model_skin_tone,
                            "hair_length": model_hair_length,
                            "hair_texture": model_hair_texture,
                            "hair_color": model_hair_color,
                            "hair_style": model_hair_style,
                        }
                        # Filter out empty values
                        model_attrs = {k: v for k, v in model_attrs.items() if v}

                        # 3. Call Engine (Handles single/list paths and front/back logic)
                        result = engine.generate_lifestyle_photo(
                            garment_path=temp_paths,
                            environment=env_value,
                            activity=act_value,
                            garment_number=garment_number.strip(),
                            garment_type=garment_type,
                            position=position,
                            conjunto_pieces=conjunto_data,
                            model_attributes=model_attrs if model_attrs else None,
                        )

                        # 3. Handle result data for Download/Drive
                        if isinstance(result, list):
                            result = result[0]  # Take first if multiple envs

                        if result.startswith("http"):
                            # Production Mode: Fetch from GCS
                            response = requests.get(result)
                            image_bytes = response.content
                        else:
                            # Local Mode: Read from disk
                            with open(result, "rb") as f:
                                image_bytes = f.read()

                        # DON'T cleanup temp files yet - keep them for feedback/regeneration
                        # They will be cleaned up when a new generation starts

                    # 4. Display Results
                    st.success("Generation Complete!")

                    # Store in session state for feedback/regeneration
                    st.session_state.last_image_bytes = image_bytes
                    st.session_state.last_temp_paths = temp_paths
                    st.session_state.last_params = {
                        "env_value": env_value,
                        "act_value": act_value,
                        "garment_number": garment_number,
                        "garment_type": garment_type,
                        "position": position,
                        "conjunto_data": conjunto_data,
                        "model_attrs": model_attrs if model_attrs else None,
                        "selected_env_label": selected_env_label,
                        "selected_act_label": selected_act_label,
                    }

                except Exception as e:
                    st.error(f"Engine Error: {e}")
    else:
        st.error("Por favor, envie pelo menos uma foto da peça.")

# --- FEEDBACK SECTION (Always visible after any generation) ---
if (
    "last_image_bytes" in st.session_state
    and st.session_state.last_image_bytes
    and "last_params" in st.session_state
):
    st.divider()

    # Display the last generated image persistently
    params = st.session_state.last_params
    st.image(
        st.session_state.last_image_bytes,
        caption=f"{params['selected_env_label']} | {params['selected_act_label']}",
    )

    # Actions: Download & Drive
    from src.engine import TYPE_NORMALIZATION

    normalized_type = TYPE_NORMALIZATION.get(
        params["garment_type"].lower(), params["garment_type"].lower()
    )
    download_filename = (
        f"cabide_{params['garment_number'].strip()}_{normalized_type}.png"
    )

    col_down, col_drive = st.columns(2)

    with col_down:
        st.download_button(
            label="💾 Download Imagem Atual",
            data=st.session_state.last_image_bytes,
            file_name=download_filename,
            mime="image/png",
            use_container_width=True,
        )

    with col_drive:
        if drive_manager:
            # Generate unique key for this specific image using hash of bytes
            import hashlib

            image_hash = hashlib.md5(st.session_state.last_image_bytes).hexdigest()[:8]
            drive_url_key = f"drive_url_{download_filename}_{image_hash}"

            if drive_url_key in st.session_state:
                # Already uploaded - show link
                st.link_button(
                    "✅ View on Google Drive",
                    st.session_state[drive_url_key],
                    use_container_width=True,
                )
            else:
                # Not uploaded yet - show upload button
                if st.button(
                    "📤 Save to Store Drive",
                    use_container_width=True,
                    key=f"drive_btn_{image_hash}",
                ):
                    with st.spinner("Uploading..."):
                        try:
                            drive_url = drive_manager.upload_file(
                                st.session_state.last_image_bytes, download_filename
                            )
                            # Store URL in session state
                            st.session_state[drive_url_key] = drive_url
                            st.balloons()
                            st.rerun()  # Rerun to show the link button
                        except Exception as e:
                            st.error(f"Upload failed: {e}")
        else:
            st.button(
                "📤 Drive Not Configured", disabled=True, use_container_width=True
            )

    st.divider()
    st.subheader("💬 Quer melhorar a imagem?")

    feedback_text = st.text_area(
        "O que você gostaria de ajustar?",
        placeholder="Ex: 'Colocar em festa, em vez de praia'",
        height=80,
        key="feedback_text",
    )

    if st.button(
        "🔄 Regenerar com Feedback",
        use_container_width=True,
        disabled=not feedback_text,
    ):
        with st.spinner("Regenerando com seu feedback..."):
            try:
                # Get parameters from session state
                params = st.session_state.last_params
                temp_paths = st.session_state.last_temp_paths

                # Determine mode: API or Direct Engine
                use_api = api_client is not None and settings.backend_url

                if use_api:
                    # API MODE: Need to read temp files and send via API
                    # Prepare all files for regeneration
                    image_files = []
                    for temp_path in temp_paths:
                        with open(temp_path, "rb") as f:
                            image_buffer = io.BytesIO(f.read())
                            image_buffer.seek(0)
                            image_files.append(
                                (os.path.basename(temp_path), image_buffer)
                            )

                    # Get conjunto data if applicable
                    conjunto_data = params.get("conjunto_data")

                    result = api_client.generate_photo(
                        image_files=image_files,
                        environment=params["env_value"],
                        activity=params["act_value"],
                        garment_number=params["garment_number"].strip(),
                        garment_type=params["garment_type"],
                        position=params["position"],
                        feedback=feedback_text,
                        piece1_type=conjunto_data.get("piece1_type")
                        if conjunto_data
                        else None,
                        piece2_type=conjunto_data.get("piece2_type")
                        if conjunto_data
                        else None,
                        piece3_type=conjunto_data.get("piece3_type")
                        if conjunto_data
                        else None,
                    )

                    if "url" in result:
                        # Production mode: Fetch from URL
                        response = requests.get(result["url"])
                        image_bytes_feedback = response.content
                    else:
                        # Local mode: Use returned bytes
                        image_bytes_feedback = result["image_bytes"]
                else:
                    # DIRECT ENGINE MODE
                    result_feedback = engine.generate_lifestyle_photo(
                        garment_path=temp_paths,
                        environment=params["env_value"],
                        activity=params["act_value"],
                        garment_number=params["garment_number"].strip(),
                        garment_type=params["garment_type"],
                        position=params["position"],
                        conjunto_pieces=params.get("conjunto_data"),
                        model_attributes=params.get("model_attrs"),
                        feedback=feedback_text,
                    )

                    # Handle result
                    if isinstance(result_feedback, list):
                        result_feedback = result_feedback[0]

                    if result_feedback.startswith("http"):
                        response = requests.get(result_feedback)
                        image_bytes_feedback = response.content
                    else:
                        with open(result_feedback, "rb") as f:
                            image_bytes_feedback = f.read()

                # Update session state with new image (this will make it the "current" image)
                st.session_state.last_image_bytes = image_bytes_feedback

                # Force rerun to show updated image and clear text area
                st.rerun()

            except Exception as e:
                st.error(f"Erro ao regenerar: {e}")
