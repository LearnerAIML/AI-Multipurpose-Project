import streamlit as st
import time
import io
import tempfile

from PIL import Image

from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from msrest.authentication import CognitiveServicesCredentials

import azure.cognitiveservices.speech as speechsdk

# =========================================================
# PAGE CONFIGURATION
# =========================================================
st.set_page_config(
    page_title="Readify AI",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =========================================================
# MODERN CLOUD AESTHETIC CSS
# =========================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;600&family=Inter:wght@300;400;500;600&display=swap');

    :root {
        --bg-color:         #F4F7F5;
        --card-bg:          #FFFFFF;
        --primary:          #1A4331;
        --primary-light:    #2A5A44;
        --text-main:        #2D3748;
        --text-muted:       #718096;
        --border-color:     #E2E8F0;
        --accent-bg:        #F0F4F2;
    }

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: var(--bg-color);
        color: var(--text-main);
    }

    .stApp {
        background: radial-gradient(circle at top left, #FFFFFF 0%, #F4F7F5 100%);
        min-height: 100vh;
    }

    header, footer, [data-testid="stToolbar"] { display: none !important; }

    /* Masthead */
    .masthead {
        padding: 40px 0 30px 0;
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
    }
    .masthead-eyebrow {
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 4px;
        color: var(--text-muted);
        text-transform: uppercase;
        margin-bottom: 12px;
    }
    .masthead-title {
        font-family: 'Cormorant Garamond', serif;
        font-size: 72px;
        font-weight: 600;
        color: var(--primary);
        letter-spacing: 4px;
        line-height: 1;
        margin-bottom: 12px;
    }
    .masthead-tagline {
        font-size: 14px;
        color: var(--text-muted);
        letter-spacing: 1px;
    }
    .masthead-status {
        margin-top: 16px;
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 1px;
        color: var(--primary);
        background: var(--accent-bg);
        padding: 6px 16px;
        border-radius: 20px;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: transparent;
        gap: 12px;
        justify-content: center;
        padding: 0;
        margin: 0 0 24px 0;
        border: none;
    }
    .stTabs [data-baseweb="tab"] {
        font-family: 'Inter', sans-serif;
        font-size: 13px;
        font-weight: 600;
        color: var(--text-muted);
        background: var(--card-bg);
        border: 1px solid var(--border-color);
        padding: 12px 24px;
        border-radius: 12px;
        transition: all 0.3s ease;
    }
    .stTabs [aria-selected="true"] {
        background: var(--primary) !important;
        color: #FFFFFF !important;
        border-color: var(--primary) !important;
        box-shadow: 0 4px 12px rgba(26, 67, 49, 0.2);
    }
    .stTabs [data-baseweb="tab-highlight"] { display: none !important; }

    /* Output Areas */
    .panel-heading {
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 2px;
        color: var(--text-main);
        padding-bottom: 12px;
        border-bottom: 1px solid var(--border-color);
        margin-bottom: 20px;
    }
    .transcript-well {
        background: #F8FAF9;
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 20px;
        font-size: 14px;
        line-height: 1.8;
        height: 300px;
        overflow-y: auto;
        color: #000000; /* Ensured text is black for clear visibility */
    }
    
    /* --- THE CENTERING FIX IS HERE --- */
    .transcript-empty {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 100%;
        min-height: 200px;
        text-align: center;
        color: var(--text-muted);
        font-size: 13px;
        gap: 10px;
    }

    /* Buttons & Inputs */
    .stButton > button {
        background: var(--primary) !important;
        color: #FFFFFF !important;
        border-radius: 8px !important;
        font-size: 12px !important;
        font-weight: 600 !important;
        padding: 12px 24px !important;
    }
    .stDownloadButton > button {
        background: var(--card-bg) !important;
        color: var(--primary) !important;
        border: 1px solid var(--primary) !important;
        border-radius: 8px !important;
        font-size: 12px !important;
        font-weight: 600 !important;
        padding: 12px 24px !important;
        width: 100% !important;
    }
    [data-testid="stFileUploadDropzone"] {
        background: var(--accent-bg) !important;
        border: 2px dashed #CBD5E0 !important;
        border-radius: 12px !important;
        padding: 30px !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 24px !important;
        font-weight: 600 !important;
        color: var(--primary) !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 10px !important;
        color: var(--text-muted) !important;
    }
    .stTextArea textarea {
        background: #F8FAF9 !important;
        border-radius: 12px !important;
    }
</style>
""", unsafe_allow_html=True)

# =========================================================
# AZURE CREDENTIALS & INITIALIZATION
# =========================================================
try:
    endpoint      = st.secrets["AZURE_ENDPOINT"]
    api_key       = st.secrets["AZURE_API_KEY"]
    speech_key    = st.secrets["AZURE_SPEECH_KEY"]
    speech_region = st.secrets["AZURE_SPEECH_REGION"]

    vision_client = ComputerVisionClient(
        endpoint,
        CognitiveServicesCredentials(api_key)
    )
except Exception:
    st.error("Configuration error — Azure credentials not found in secrets.")
    st.stop()

# =========================================================
# MASTHEAD
# =========================================================
st.markdown("""
<div class="masthead">
    <div class="masthead-eyebrow">🌿 ESTABLISHED 2026</div>
    <div class="masthead-title">READIFY_AI</div>
    <div class="masthead-tagline">Document Intelligence &nbsp;•&nbsp; Speech Synthesis &nbsp;•&nbsp; Image To Speech</div>
    <div class="masthead-status"> MADE USING MICROSOFT AZURE</div>
</div>
""", unsafe_allow_html=True)

st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

# =========================================================
# TABS
# =========================================================
t1, t2, t3 = st.tabs(["📄 I. DOCUMENT INTELLIGENCE", "🎙️ II. SPEECH SYNTHESIS", "🔊 III. IMAGE TO SPEECH"])

# =========================================================
# MODULE 1 — DOCUMENT INTELLIGENCE (OCR)
# =========================================================
with t1:
    col_in, col_out = st.columns([1, 1.5], gap="large")

    with col_in:
        st.markdown('<div class="panel-heading">☁️ UPLOAD DOCUMENT</div>', unsafe_allow_html=True)
        image_file = st.file_uploader("Upload Target Document", type=["png", "jpg", "jpeg"], label_visibility="collapsed", key="ocr_uploader")

        if image_file:
            st.image(image_file, use_container_width=True)
            m1, m2 = st.columns(2)
            m1.metric("Size", f"{image_file.size / 1024:.1f} KB")
            m2.metric("Format", image_file.type.split('/')[-1].upper())
            execute_ocr = st.button("✨ EXTRACT TEXT")
        else:
            st.markdown('<div style="padding:40px 0; text-align:center; color:#718096; font-size:14px;">Drop your document here<br>to begin analysis</div>', unsafe_allow_html=True)

    with col_out:
        st.markdown('<div class="panel-heading">📄 EXTRACTED TEXT</div>', unsafe_allow_html=True)

        if image_file and 'execute_ocr' in locals() and execute_ocr:
            with st.spinner("Analysing document..."):
                try:
                    response = vision_client.read_in_stream(io.BytesIO(image_file.read()), raw=True)
                    op_id    = response.headers["Operation-Location"].split("/")[-1]

                    while True:
                        result = vision_client.get_read_result(op_id)
                        if result.status not in [OperationStatusCodes.running, OperationStatusCodes.not_started]:
                            break
                        time.sleep(0.5)

                    lines = []
                    if result.status == OperationStatusCodes.succeeded:
                        for page in result.analyze_result.read_results:
                            for line in page.lines:
                                lines.append(line.text)

                    full_text = "\n".join(lines)
                    st.markdown(f'<div class="transcript-well">{full_text}</div>', unsafe_allow_html=True)
                    st.download_button("📥 Export as .txt", full_text, file_name="ocr.txt", key="ocr_download")

                except Exception as e:
                    st.error(f"Extraction error: {e}")
        else:
            # Fixed HTML structure for centering
            st.markdown("""
            <div class="transcript-well">
                <div class="transcript-empty">
                    <span style="font-size:32px; color:#CBD5E0;">📄</span>
                    <div>
                        Awaiting document ingestion...<br>
                        <span style="font-size:12px; color:#A0AEC0;">Once processed, the extracted text will appear here.</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# =========================================================
# MODULE 2 — SPEECH SYNTHESIS (TTS)
# =========================================================
with t2:
    col_text, col_audio = st.columns([1.4, 1], gap="large")

    with col_text:
        st.markdown('<div class="panel-heading">✍️ SCRIPT INPUT</div>', unsafe_allow_html=True)
        user_script = st.text_area("Enter text:", height=220, label_visibility="collapsed", placeholder="Compose your script here…")
        
        # New Voice Selection feature
        voice_choice_t2 = st.radio("Select Voice:", ["Male", "Female"], horizontal=True, key="voice_t2")
        
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        generate_voice = st.button("🪄 SYNTHESISE VOICE")

    with col_audio:
        st.markdown('<div class="panel-heading">🎧 AUDIO OUTPUT</div>', unsafe_allow_html=True)

        if generate_voice and user_script.strip():
            with st.spinner("Synthesising voice..."):
                try:
                    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
                    
                    # Apply selected voice
                    voice_name = "en-US-ChristopherNeural" if voice_choice_t2 == "Male" else "en-US-JennyNeural"
                    speech_config.speech_synthesis_voice_name = voice_name
                    
                    out_file = "voice.wav"
                    audio_config = speechsdk.audio.AudioOutputConfig(filename=out_file)
                    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
                    synthesizer.speak_text_async(user_script).get()
                    audio_data = open(out_file, "rb").read()
                    st.success(f"Voice synthesised successfully ({voice_choice_t2}).")
                    st.audio(audio_data, format="audio/wav")
                    st.download_button("📥 Download Audio (.wav)", audio_data, file_name=out_file, key="tts_download")
                except Exception as e:
                    st.error(f"Synthesis error: {e}")
        elif generate_voice:
            st.warning("Please enter a script before synthesising.")
        else:
            # Fixed HTML structure for centering
            st.markdown("""
            <div class="transcript-well" style="height:220px;">
                <div class="transcript-empty">
                    <span style="font-size:32px; color:#CBD5E0;">🎙️</span>
                    <div>Awaiting script input...</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# =========================================================
# MODULE 3 — IMAGE TO SPEECH (OCR + TTS)
# =========================================================
with t3:
    col_in3, col_out3 = st.columns([1, 1.5], gap="large")

    with col_in3:
        st.markdown('<div class="panel-heading">☁️ UPLOAD DOCUMENT FOR READING</div>', unsafe_allow_html=True)
        image_file_t3 = st.file_uploader("Upload Target Document", type=["png", "jpg", "jpeg"], label_visibility="collapsed", key="img_to_speech_uploader")

        if image_file_t3:
            st.image(image_file_t3, use_container_width=True)
            m1_t3, m2_t3 = st.columns(2)
            m1_t3.metric("Size", f"{image_file_t3.size / 1024:.1f} KB")
            m2_t3.metric("Format", image_file_t3.type.split('/')[-1].upper())
            
            # New Voice Selection feature
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            voice_choice_t3 = st.radio("Select Voice:", ["Male", "Female"], horizontal=True, key="voice_t3")
            
            execute_img_to_speech = st.button("🔊 READ DOCUMENT ALOUD")
        else:
            st.markdown('<div style="padding:40px 0; text-align:center; color:#718096; font-size:14px;">Drop your document here<br>to convert directly to voice</div>', unsafe_allow_html=True)

    with col_out3:
        st.markdown('<div class="panel-heading">⚙️ PROCESSED OUTPUT</div>', unsafe_allow_html=True)

        if image_file_t3 and 'execute_img_to_speech' in locals() and execute_img_to_speech:
            with st.spinner("Extracting text and synthesising voice..."):
                try:
                    response = vision_client.read_in_stream(io.BytesIO(image_file_t3.read()), raw=True)
                    op_id = response.headers["Operation-Location"].split("/")[-1]

                    while True:
                        result = vision_client.get_read_result(op_id)
                        if result.status not in [OperationStatusCodes.running, OperationStatusCodes.not_started]:
                            break
                        time.sleep(0.5)

                    lines = []
                    if result.status == OperationStatusCodes.succeeded:
                        for page in result.analyze_result.read_results:
                            for line in page.lines:
                                lines.append(line.text)

                    extracted_text = "\n".join(lines)

                    if not extracted_text.strip():
                        st.warning("No text was found in the uploaded image.")
                    else:
                        st.markdown(f'<div class="transcript-well" style="height:200px;">{extracted_text}</div>', unsafe_allow_html=True)
                        
                        speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
                        
                        # Apply selected voice
                        voice_name_t3 = "en-US-ChristopherNeural" if voice_choice_t3 == "Male" else "en-US-JennyNeural"
                        speech_config.speech_synthesis_voice_name = voice_name_t3
                        
                        out_file_t3 = "vision_to_voice.wav"
                        audio_config_t3 = speechsdk.audio.AudioOutputConfig(filename=out_file_t3)
                        synthesizer_t3 = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config_t3)
                        synthesizer_t3.speak_text_async(extracted_text).get()
                        
                        audio_data_t3 = open(out_file_t3, "rb").read()
                        st.success(f"Voice synthesised successfully from document ({voice_choice_t3}).")
                        st.audio(audio_data_t3, format="audio/wav")
                        st.download_button("📥 Download Audio (.wav)", audio_data_t3, file_name=out_file_t3, key="img2speech_download")

                except Exception as e:
                    st.error(f"Processing error: {e}")
        else:
            # Fixed HTML structure for centering
            st.markdown("""
            <div class="transcript-well">
                <div class="transcript-empty">
                    <span style="font-size:32px; color:#CBD5E0;">⚙️</span>
                    <div>Awaiting document ingestion...</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# =========================================================
# FOOTER
# =========================================================
st.markdown("""
<div style="margin-top: 60px; padding: 30px 0; border-top: 1px solid #E2E8F0; text-align: center;">
    <div style="display: flex; justify-content: center; gap: 40px; margin-bottom: 20px; color: #718096; font-size: 12px;">
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 16px;">🤖</span> 
            <div style="text-align: left;">
                <strong>AI POWERED</strong><br>Advanced Azure AI models
            </div>
        </div>
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 16px;">🔒</span> 
            <div style="text-align: left;">
                <strong>SECURE & PRIVATE</strong><br>Your data is encrypted
            </div>
        </div>
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 16px;">⚡</span> 
            <div style="text-align: left;">
                <strong>FAST PROCESSING</strong><br>Optimized for speed
            </div>
        </div>
    </div>
    <div style="color: #2D3748; font-size: 14px; font-weight: 500;">
        Made with ❤️ by Varad Petare
    </div>
    <div style="color: #A0AEC0; font-size: 11px; margin-top: 6px;">
        © 2026 READIFY_AI. All rights reserved.
    </div>
</div>
""", unsafe_allow_html=True)
