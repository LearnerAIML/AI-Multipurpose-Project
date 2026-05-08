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
# EDITORIAL JOURNAL AESTHETIC
# Palette: Warm Cream · Forest Green · Aged Ink · Rose Dust
# Typography: Cormorant Garamond (display) + DM Mono (body)
# =========================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;0,700;1,300;1,400&family=DM+Mono:wght@300;400;500&family=Literata:ital,wght@0,300;0,400;1,300&display=swap');

    /* ─── Root Tokens ─── */
    :root {
        --cream:        #F5F0E8;
        --cream-dark:   #EDE8DC;
        --ink:          #1C1A16;
        --ink-light:    #3D3A34;
        --forest:       #2D4A3E;
        --forest-light: #3D6B5A;
        --forest-muted: #5A8A75;
        --rose:         #C4857A;
        --rose-light:   #D9A89F;
        --gold:         #B8A070;
        --gold-light:   #D4BC94;
        --rule:         #C8C0B0;
        --rule-light:   #DDD8CC;
    }

    /* ─── Global Reset ─── */
    html, body, [class*="css"] {
        font-family: 'DM Mono', monospace;
        background-color: var(--cream);
        color: var(--ink);
    }

    .stApp {
        background-color: var(--cream);
        background-image:
            repeating-linear-gradient(
                0deg,
                transparent,
                transparent 39px,
                var(--rule-light) 39px,
                var(--rule-light) 40px
            );
        min-height: 100vh;
    }

    header, footer, [data-testid="stToolbar"] { display: none !important; }

    /* ─── Masthead ─── */
    .masthead {
        border-top: 3px solid var(--ink);
        border-bottom: 1px solid var(--rule);
        padding: 28px 0 20px 0;
        margin-bottom: 0;
        display: flex;
        flex-direction: column;
        align-items: center;
    }

    .masthead-eyebrow {
        font-family: 'DM Mono', monospace;
        font-size: 10px;
        font-weight: 500;
        letter-spacing: 5px;
        color: var(--forest-muted);
        text-transform: uppercase;
        margin-bottom: 8px;
    }

    .masthead-title {
        font-family: 'Cormorant Garamond', serif;
        font-size: 80px;
        font-weight: 300;
        color: var(--ink);
        letter-spacing: 8px;
        line-height: 1;
        text-transform: uppercase;
        margin-bottom: 6px;
    }

    .masthead-rule-row {
        display: flex;
        align-items: center;
        gap: 16px;
        width: 100%;
        max-width: 600px;
        margin: 10px 0 6px 0;
    }
    .masthead-rule-row hr {
        flex: 1;
        border: none;
        border-top: 1px solid var(--rule);
        margin: 0;
    }
    .masthead-diamond {
        color: var(--forest);
        font-size: 12px;
    }

    .masthead-tagline {
        font-family: 'Literata', serif;
        font-size: 13px;
        font-style: italic;
        color: var(--ink-light);
        letter-spacing: 1px;
    }

    .masthead-status {
        margin-top: 12px;
        font-family: 'DM Mono', monospace;
        font-size: 9px;
        letter-spacing: 3px;
        color: var(--forest);
        text-transform: uppercase;
        padding: 4px 14px;
        border: 1px solid var(--forest-muted);
        border-radius: 0;
    }

    /* ─── Section Divider ─── */
    .section-divider {
        border: none;
        border-top: 1px solid var(--rule);
        margin: 0;
    }

    /* ─── Tab Nav — Newspaper section headers ─── */
    .stTabs [data-baseweb="tab-list"] {
        background: transparent;
        border-bottom: 2px solid var(--ink);
        gap: 0;
        justify-content: flex-start;
        padding: 0;
        margin: 0 0 32px 0;
    }
    .stTabs [data-baseweb="tab"] {
        font-family: 'Cormorant Garamond', serif;
        font-size: 16px;
        font-weight: 600;
        color: var(--ink-light);
        letter-spacing: 1px;
        text-transform: uppercase;
        border: none;
        border-right: 1px solid var(--rule);
        padding: 12px 28px;
        background: transparent;
        height: auto;
        border-radius: 0;
    }
    .stTabs [data-baseweb="tab"]:first-child {
        border-left: 1px solid var(--rule);
    }
    .stTabs [aria-selected="true"] {
        background: var(--forest) !important;
        color: var(--cream) !important;
        border-color: var(--forest) !important;
    }
    .stTabs [data-baseweb="tab-highlight"] { display: none !important; }

    /* ─── Cards — Archival Document Style ─── */
    .journal-panel {
        background: var(--cream);
        border: 1px solid var(--rule);
        border-top: 3px solid var(--forest);
        padding: 28px 28px 24px 28px;
        position: relative;
    }

    .journal-panel::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
        background: var(--forest);
    }

    .panel-heading {
        font-family: 'Cormorant Garamond', serif;
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 4px;
        text-transform: uppercase;
        color: var(--forest);
        padding-bottom: 10px;
        border-bottom: 1px solid var(--rule-light);
        margin-bottom: 20px;
    }

    /* ─── Transcript / Output Area ─── */
    .transcript-well {
        background: #FDFAF5;
        border: 1px solid var(--rule);
        border-left: 4px solid var(--forest);
        padding: 22px 24px;
        font-family: 'Literata', serif;
        font-size: 14px;
        line-height: 1.9;
        color: var(--ink);
        height: 300px;
        overflow-y: auto;
    }

    .transcript-empty {
        display: flex;
        align-items: center;
        justify-content: center;
        height: 100%;
        font-family: 'Literata', serif;
        font-style: italic;
        font-size: 14px;
        color: var(--rule);
    }

    /* ─── Buttons ─── */
    .stButton > button {
        background: var(--forest) !important;
        color: var(--cream) !important;
        border: none !important;
        border-radius: 0 !important;
        font-family: 'DM Mono', monospace !important;
        font-size: 10px !important;
        font-weight: 500 !important;
        letter-spacing: 3px !important;
        text-transform: uppercase !important;
        padding: 14px 0 !important;
        width: 100% !important;
        transition: background 0.2s ease, color 0.2s ease !important;
    }
    .stButton > button:hover {
        background: var(--ink) !important;
        color: var(--cream) !important;
    }

    .stDownloadButton > button {
        background: transparent !important;
        color: var(--forest) !important;
        border: 1px solid var(--forest) !important;
        border-radius: 0 !important;
        font-family: 'DM Mono', monospace !important;
        font-size: 10px !important;
        font-weight: 500 !important;
        letter-spacing: 3px !important;
        text-transform: uppercase !important;
        padding: 12px 0 !important;
        width: 100% !important;
        transition: all 0.2s ease !important;
    }
    .stDownloadButton > button:hover {
        background: var(--forest) !important;
        color: var(--cream) !important;
    }

    /* ─── File Uploader ─── */
    [data-testid="stFileUploadDropzone"] {
        background: #FDFAF5 !important;
        border: 1px dashed var(--rule) !important;
        border-radius: 0 !important;
    }
    [data-testid="stFileUploadDropzone"]:hover {
        border-color: var(--forest-muted) !important;
        background: #F8F4EC !important;
    }

    /* ─── Metrics ─── */
    [data-testid="stMetricValue"] {
        font-family: 'Cormorant Garamond', serif !important;
        font-size: 28px !important;
        font-weight: 600 !important;
        color: var(--forest) !important;
    }
    [data-testid="stMetricLabel"] {
        font-family: 'DM Mono', monospace !important;
        font-size: 9px !important;
        letter-spacing: 3px !important;
        text-transform: uppercase !important;
        color: var(--ink-light) !important;
    }

    /* ─── Spinner ─── */
    .stSpinner > div > div {
        border-top-color: var(--forest) !important;
    }

    /* ─── Audio Player ─── */
    audio {
        width: 100%;
        margin-top: 12px;
        filter: sepia(0.3);
    }

    /* ─── Text Area ─── */
    .stTextArea textarea {
        background: #FDFAF5 !important;
        border: 1px solid var(--rule) !important;
        border-radius: 0 !important;
        font-family: 'Literata', serif !important;
        font-size: 14px !important;
        color: var(--ink) !important;
        line-height: 1.8 !important;
    }
    .stTextArea textarea:focus {
        border-color: var(--forest) !important;
        box-shadow: none !important;
    }

    /* ─── Column gap fine-tuning ─── */
    .block-container {
        padding-top: 0 !important;
        padding-bottom: 40px !important;
        max-width: 1200px !important;
    }

    /* ─── Image rounded slightly ─── */
    [data-testid="stImage"] img {
        border: 1px solid var(--rule);
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
    <div class="masthead-eyebrow">Cognitive Intelligence · Established 2026</div>
    <div class="masthead-title">Readify_AI</div>
    <div class="masthead-rule-row">
        <hr/>
        <span class="masthead-diamond">◈</span>
        <hr/>
    </div>
    <div class="masthead-tagline">Document Intelligence &nbsp;·&nbsp; Acoustic Analysis &nbsp;·&nbsp; Speech Synthesis</div>
    <div class="masthead-status">● Azure uplink verified</div>
</div>
""", unsafe_allow_html=True)

st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)

# =========================================================
# TABS
# =========================================================
t1, t2, t3 = st.tabs(["I. Document Intelligence", "II. Acoustic Analysis", "III. Speech Synthesis"])

# =========================================================
# MODULE 1 — DOCUMENT INTELLIGENCE (OCR)
# =========================================================
with t1:
    col_in, col_out = st.columns([1, 1.5], gap="large")

    with col_in:
        st.markdown('<div class="journal-panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-heading">◈ &nbsp; Upload Document</div>', unsafe_allow_html=True)

        image_file = st.file_uploader(
            "Upload Target Document",
            type=["png", "jpg", "jpeg"],
            label_visibility="collapsed"
        )

        if image_file:
            st.image(image_file, use_container_width=True)
            st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

            m1, m2 = st.columns(2)
            m1.metric("Size", f"{image_file.size / 1024:.1f} KB")
            m2.metric("Format", image_file.type.split('/')[-1].upper())

            st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
            execute_ocr = st.button("Extract Text")
        else:
            st.markdown("""
            <div style="padding:40px 0; text-align:center; color:#C8C0B0; font-family:'Literata',serif; font-style:italic; font-size:13px;">
                Drop your document here<br>to begin analysis
            </div>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    with col_out:
        st.markdown('<div class="journal-panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-heading">◈ &nbsp; Extracted Text</div>', unsafe_allow_html=True)

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
                    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
                    st.download_button("Export as .txt", full_text, file_name="ocr.txt")

                except Exception as e:
                    st.error(f"Extraction error: {e}")
        else:
            st.markdown("""
            <div class="transcript-well">
                <div class="transcript-empty">Awaiting document ingestion…</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# MODULE 2 — ACOUSTIC ANALYSIS (STT)
# =========================================================
with t2:
    st.markdown('<div class="journal-panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-heading">◈ &nbsp; Audio Transcription</div>', unsafe_allow_html=True)

    audio_file = st.file_uploader(
        "Upload Audio (.wav)",
        type=["wav"],
        label_visibility="collapsed"
    )

    if audio_file:
        st.audio(audio_file)
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            process_audio = st.button("Transcribe Recording")

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

        if process_audio:
            with st.spinner("Transcribing audio..."):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                    tmp.write(audio_file.read())
                    tmp_path = tmp.name

                try:
                    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
                    audio_config  = speechsdk.audio.AudioConfig(filename=tmp_path)
                    recognizer    = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
                    stt_result    = recognizer.recognize_once()

                    if stt_result.reason == speechsdk.ResultReason.RecognizedSpeech:
                        st.markdown(f'<div class="transcript-well" style="height:auto;min-height:140px;">{stt_result.text}</div>', unsafe_allow_html=True)
                        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
                        st.download_button("Export Transcript (.txt)", stt_result.text, file_name="transcript.txt")
                    else:
                        st.error("Audio could not be recognised. Please verify the file.")

                except Exception as e:
                    st.error(f"Transcription error: {e}")
    else:
        st.markdown("""
        <div style="padding:40px 0; text-align:center; color:#C8C0B0; font-family:'Literata',serif; font-style:italic; font-size:13px;">
            Upload a .wav file to begin transcription
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# MODULE 3 — SPEECH SYNTHESIS (TTS)
# =========================================================
with t3:
    col_text, col_audio = st.columns([1.4, 1], gap="large")

    with col_text:
        st.markdown('<div class="journal-panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-heading">◈ &nbsp; Script Input</div>', unsafe_allow_html=True)

        user_script = st.text_area(
            "Enter text:",
            height=220,
            label_visibility="collapsed",
            placeholder="Compose your script here…"
        )
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        generate_voice = st.button("Synthesise Voice")

        st.markdown('</div>', unsafe_allow_html=True)

    with col_audio:
        st.markdown('<div class="journal-panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-heading">◈ &nbsp; Audio Output</div>', unsafe_allow_html=True)

        if generate_voice and user_script.strip():
            with st.spinner("Synthesising voice..."):
                try:
                    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
                    speech_config.speech_synthesis_voice_name = "en-US-ChristopherNeural"

                    out_file     = "voice.wav"
                    audio_config = speechsdk.audio.AudioOutputConfig(filename=out_file)
                    synthesizer  = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
                    synthesizer.speak_text_async(user_script).get()

                    audio_data = open(out_file, "rb").read()

                    st.success("Voice synthesised successfully.")
                    st.audio(audio_data, format="audio/wav")
                    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
                    st.download_button("Download Audio (.wav)", audio_data, file_name=out_file)

                except Exception as e:
                    st.error(f"Synthesis error: {e}")

        elif generate_voice:
            st.warning("Please enter a script before synthesising.")
        else:
            st.markdown("""
            <div class="transcript-well" style="height:220px;">
                <div class="transcript-empty">Awaiting script input…</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)
