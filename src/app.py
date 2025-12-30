import os
import io
import uuid
import json
import requests
import streamlit as st
from src.engine import FashionEngine
from src.driver_service import DriveService
from src.api_client import CabideAPIClient
from src.config import get_settings, Settings

# --- Page Configuration ---
st.set_page_config(
    page_title="Cabide AI - Professional Catalog",
    page_icon="👗",
    layout="centered"
)

# --- Singleton-style Initialization ---
@st.cache_resource
def get_engine():
    return FashionEngine()

@st.cache_resource
def get_drive_manager(_settings: Settings):
    """
    Initializes DriveService if in prod mode and credentials exist.
    The underscore prefix tells Streamlit not to hash this object.
    """
    if _settings.storage_mode == "prod" and _settings.gcp_service_account_json != "{}":
        try:
            sa_info = json.loads(_settings.gcp_service_account_json)
            return DriveService(sa_info, _settings.gdrive_folder_id)
        except Exception as e:
            st.error(f"Failed to initialize Drive Service: {e}")
    return None

# Load Resources
settings = get_settings()
engine = get_engine()
drive_manager = get_drive_manager(settings)

# Initialize API client if backend URL is configured
api_client = None
if settings.backend_url:
    try:
        api_client = CabideAPIClient(settings.backend_url)
        api_status = api_client.health_check()
        st.sidebar.success(f"✅ API Connected: v{api_status.get('version', 'unknown')}")
    except Exception as e:
        st.sidebar.warning(f"⚠️ API unavailable: {e}\nUsing direct engine mode")
        api_client = None

# --- UI Header ---
st.title("👗 Cabide AI")
st.markdown("### Professional Catalog Generator for your Mother's Store")
st.info(f"📍 Region: Brazil (southamerica-east1) | Storage: **{settings.storage_mode.upper()}**")

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
            "Consultório (Medical Office)": "medical office"
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
            "Fazendo Apresentação (Presenting)": "giving a presentation",
            "Atendendo Cliente (Attending Client)": "attending to a client"
        }
        selected_act_label = st.selectbox("Model Activity", list(activity_labels.keys()))
        act_value = activity_labels[selected_act_label]

# --- Garment Metadata Section ---
with st.expander("📋 Dados da Peça", expanded=True):
    col_num, col_type, col_position = st.columns(3)
    with col_num:
        garment_number = st.text_input(
            "Número da Peça *",
            placeholder="Ex: 100",
            help="Número único da peça para o catálogo"
        )
    with col_type:
        garment_type = st.selectbox(
            "Tipo da Peça *",
            ["", "Vestido", "Vestido de Festa", "Calça", "Camisa", "Saia",
             "Sapato", "Écharpe", "Bracelete", "Veste", "Conjunto"],
            help="Selecione o tipo de roupa"
        )
    with col_position:
        position = st.selectbox(
            "Posição (Opcional)",
            ["Frente", "Costas", "Ambos"],
            help="Útil para vestidos e peças com frente/costas diferentes. Se não enviar costas, usamos a frente."
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
                help="Parte de cima do conjunto (obrigatório)"
            )
        with col2:
            piece2_type = st.selectbox(
                "Peça Inferior *",
                ["", "Calça", "Saia"],
                help="Parte de baixo do conjunto (obrigatório)"
            )
        with col3:
            piece3_type = st.selectbox(
                "Peça Adicional (Opcional)",
                ["", "Veste", "Écharpe", "Bracelete", "Colar"],
                help="Veste, acessório ou complemento (opcional)"
            )

# --- File Upload Section ---
# Multi-file upload for Front/Back support or Conjunto pieces
if garment_type == "Conjunto":
    num_pieces = 2 if not piece3_type else 3
    st.info(f"📸 Envie {num_pieces} fotos separadas na ordem: 1) {piece1_type or 'Peça Superior'}, 2) {piece2_type or 'Peça Inferior'}" +
            (f", 3) {piece3_type}" if piece3_type else ""))
else:
    upload_help_text = {
        "Frente": "Envie 1 ou mais fotos da frente",
        "Costas": "Envie 1 ou mais fotos das costas",
        "Ambos": "Envie 2 fotos: frente e costas (recomendado para vestidos)"
    }
    st.info(f"📸 {upload_help_text.get(position, 'Envie as fotos da peça')} • Se não tiver foto das costas, usamos a frente.")

uploaded_files = st.file_uploader(
    "Upload garment photos (1 ou 2 fotos)",
    type=['png', 'jpg', 'jpeg', 'heic', 'heif'],
    accept_multiple_files=True
)

if st.button("✨ Generate Professional Photo", use_container_width=True):
    if uploaded_files:
        # Validate metadata
        if not garment_number or not garment_number.strip():
            st.error("⚠️ Por favor, preencha o Número da Peça")
        elif not garment_type:
            st.error("⚠️ Por favor, selecione o Tipo da Peça")
        elif garment_type == "Conjunto" and (not piece1_type or not piece2_type):
            st.error("⚠️ Por favor, selecione a Peça Superior e Peça Inferior do conjunto")
        elif garment_type == "Conjunto":
            expected_photos = 2 if not piece3_type else 3
            if len(uploaded_files) != expected_photos:
                st.error(f"⚠️ Por favor, envie exatamente {expected_photos} fotos para o conjunto ({len(uploaded_files)} enviada(s))")
        else:
            # Optional: Show info if user selected "Ambos" but only uploaded 1 photo
            if position == "Ambos" and len(uploaded_files) == 1:
                st.info("ℹ️ Você selecionou 'Ambos' mas enviou apenas 1 foto. Vamos usar a mesma foto para frente e costas.")

            with st.spinner("Banana Pro is generating your image..."):
                try:
                    # Determine mode: API or Direct Engine
                    use_api = api_client is not None and settings.backend_url

                    if use_api:
                        # API MODE: Call backend
                        # For now, use first file (multi-file upload needs backend update)
                        uploaded_file = uploaded_files[0]

                        # Create BytesIO and ensure it's at position 0
                        image_buffer = io.BytesIO(uploaded_file.getbuffer())
                        image_buffer.seek(0)

                        result = api_client.generate_photo(
                            image_file=image_buffer,
                            filename=uploaded_file.name,
                            environment=env_value,
                            activity=act_value,
                            garment_number=garment_number.strip(),
                            garment_type=garment_type,
                            position=position
                        )

                        if 'url' in result:
                            # Production mode: Fetch from URL
                            response = requests.get(result['url'])
                            image_bytes = response.content
                        else:
                            # Local mode: Use returned bytes
                            image_bytes = result['image_bytes']
                    else:
                        # DIRECT ENGINE MODE (current behavior)
                        # 1. Handle multiple temp files for the engine
                        temp_paths = []
                        for idx, uploaded_file in enumerate(uploaded_files):
                            temp_name = f"temp_{idx}_{uploaded_file.name}"
                            with open(temp_name, "wb") as f:
                                f.write(uploaded_file.getbuffer())

                            # Convert HEIC to PNG if needed
                            if uploaded_file.name.lower().endswith(('.heic', '.heif')):
                                try:
                                    from PIL import Image
                                    from pillow_heif import register_heif_opener

                                    register_heif_opener()
                                    img = Image.open(temp_name)

                                    # Convert to PNG
                                    png_name = f"temp_{idx}_converted.png"
                                    img.save(png_name, format='PNG')

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
                                "piece3_type": piece3_type
                            }

                        # 3. Call Engine (Handles single/list paths and front/back logic)
                        result = engine.generate_lifestyle_photo(
                            garment_path=temp_paths,
                            environment=env_value,
                            activity=act_value,
                            garment_number=garment_number.strip(),
                            garment_type=garment_type,
                            position=position,
                            conjunto_pieces=conjunto_data
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

                        # Cleanup temp files
                        for p in temp_paths:
                            if os.path.exists(p):
                                os.remove(p)

                    # 4. Display Results
                    st.success("Generation Complete!")
                    st.image(image_bytes, caption=f"{selected_env_label} | {selected_act_label}")

                    # --- Actions (Download & Drive) ---
                    col_down, col_drive = st.columns(2)

                    with col_down:
                        # Generate filename with metadata
                        from src.engine import TYPE_NORMALIZATION
                        normalized_type = TYPE_NORMALIZATION.get(garment_type.lower(), garment_type.lower())
                        download_filename = f"cabide_{garment_number.strip()}_{normalized_type}.png"

                        st.download_button(
                            label="💾 Download Image",
                            data=image_bytes,
                            file_name=download_filename,
                            mime="image/png",
                            use_container_width=True
                        )

                    with col_drive:
                        if drive_manager:
                            if st.button("📤 Save to Store Drive", use_container_width=True):
                                with st.spinner("Uploading..."):
                                    drive_url = drive_manager.upload_file(
                                        image_bytes,
                                        download_filename  # Use same filename as download
                                    )
                                    st.balloons()
                                    st.link_button("View on Google Drive", drive_url, use_container_width=True)
                        else:
                            st.button("📤 Drive Not Configured", disabled=True, use_container_width=True)

                except Exception as e:
                    st.error(f"Engine Error: {e}")
    else:
        st.error("Please upload at least one garment photo.")
