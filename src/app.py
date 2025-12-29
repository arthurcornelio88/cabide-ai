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
            "Festa (Party)": "luxury party ballroom"
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
            "No Celular (On Phone)": "checking phone"
        }
        selected_act_label = st.selectbox("Model Activity", list(activity_labels.keys()))
        act_value = activity_labels[selected_act_label]

# --- File Upload Section ---
# Multi-file upload for Front/Back support
uploaded_files = st.file_uploader(
    "Upload garment photos (Front & Back recommended for better fidelity)",
    type=['png', 'jpg', 'jpeg'],
    accept_multiple_files=True
)

if st.button("✨ Generate Professional Photo", use_container_width=True):
    if uploaded_files:
        with st.spinner("Banana Pro is generating your image..."):
            try:
                # Determine mode: API or Direct Engine
                use_api = api_client is not None and settings.backend_url

                if use_api:
                    # API MODE: Call backend
                    # For now, use first file (multi-file upload needs backend update)
                    uploaded_file = uploaded_files[0]

                    result = api_client.generate_photo(
                        image_file=io.BytesIO(uploaded_file.getbuffer()),
                        filename=uploaded_file.name,
                        environment=env_value,
                        activity=act_value
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
                        temp_paths.append(temp_name)

                    # 2. Call Engine (Handles single/list paths and front/back logic)
                    result = engine.generate_lifestyle_photo(
                        garment_path=temp_paths,
                        environment=env_value,
                        activity=act_value
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
                    st.download_button(
                        label="💾 Download Image",
                        data=image_bytes,
                        file_name=f"catalog_{uuid.uuid4().hex[:5]}.png",
                        mime="image/png",
                        use_container_width=True
                    )

                with col_drive:
                    if drive_manager:
                        if st.button("📤 Save to Store Drive", use_container_width=True):
                            with st.spinner("Uploading..."):
                                drive_url = drive_manager.upload_file(
                                    image_bytes,
                                    f"catalog_{uuid.uuid4().hex[:5]}.png"
                                )
                                st.balloons()
                                st.link_button("View on Google Drive", drive_url, use_container_width=True)
                    else:
                        st.button("📤 Drive Not Configured", disabled=True, use_container_width=True)

            except Exception as e:
                st.error(f"Engine Error: {e}")
    else:
        st.error("Please upload at least one garment photo.")
