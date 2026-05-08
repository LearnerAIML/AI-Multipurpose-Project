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
""")
st.markdown("", unsafe_allow_html=True)

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
                    # Added style="color: black;" for output visibility
                    st.markdown(f'<div class="transcript-well" style="color: black;">{full_text}</div>', unsafe_allow_html=True)
                    st.download_button("📥 Export as .txt", full_text, file_name="ocr.txt", key="ocr_download")

                except Exception as e:
                    st.error(f"Extraction error: {e}")
        else:
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
        
        # Added Voice Selection Toggle
        voice_choice_t2 = st.radio("Select Voice:", ["Male", "Female"], horizontal=True, key="tts_voice")
        
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        generate_voice = st.button("🪄 SYNTHESISE VOICE")

    with col_audio:
        st.markdown('<div class="panel-heading">🎧 AUDIO OUTPUT</div>', unsafe_allow_html=True)

        if generate_voice and user_script.strip():
            with st.spinner("Synthesising voice..."):
                try:
                    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
                    
                    # Dynamically set voice based on selection
                    speech_config.speech_synthesis_voice_name = "en-US-ChristopherNeural" if voice_choice_t2 == "Male" else "en-US-JennyNeural"
                    
                    out_file = "voice.wav"
                    audio_config = speechsdk.audio.AudioOutputConfig(filename=out_file)
                    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
                    synthesizer.speak_text_async(user_script).get()
                    audio_data = open(out_file, "rb").read()
                    st.success("Voice synthesised successfully.")
                    st.audio(audio_data, format="audio/wav")
                    st.download_button("📥 Download Audio (.wav)", audio_data, file_name=out_file, key="tts_download")
                except Exception as e:
                    st.error(f"Synthesis error: {e}")
        elif generate_voice:
            st.warning("Please enter a script before synthesising.")
        else:
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
            
            # Added Voice Selection Toggle
            voice_choice_t3 = st.radio("Select Voice:", ["Male", "Female"], horizontal=True, key="img2speech_voice")
            
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
                        # Added style="color: black;" for output visibility
                        st.markdown(f'<div class="transcript-well" style="height:200px; color: black;">{extracted_text}</div>', unsafe_allow_html=True)
                        
                        speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
                        
                        # Dynamically set voice based on selection
                        speech_config.speech_synthesis_voice_name = "en-US-ChristopherNeural" if voice_choice_t3 == "Male" else "en-US-JennyNeural"
                        
                        out_file_t3 = "vision_to_voice.wav"
                        audio_config_t3 = speechsdk.audio.AudioOutputConfig(filename=out_file_t3)
                        synthesizer_t3 = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config_t3)
                        synthesizer_t3.speak_text_async(extracted_text).get()
                        
                        audio_data_t3 = open(out_file_t3, "rb").read()
                        st.success("Voice synthesised successfully from document.")
                        st.audio(audio_data_t3, format="audio/wav")
                        st.download_button("📥 Download Audio (.wav)", audio_data_t3, file_name=out_file_t3, key="img2speech_download")

                except Exception as e:
                    st.error(f"Processing error: {e}")
        else:
            st.markdown("""
            <div class="transcript-well">
                <div class="transcript-empty">
                    <span style="font-size:32px; color:#CBD5E0;">⚙️</span>
                    <div>Awaiting document ingestion...</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
