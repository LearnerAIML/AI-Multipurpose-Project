import io
import time
import streamlit as st
import azure.cognitiveservices.speech as speechsdk

from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from msrest.authentication import CognitiveServicesCredentials

# ----------------------------
# PAGE SETUP
# ----------------------------
st.set_page_config(
    page_title="READIFY_AI",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ----------------------------
# SIMPLE CSS
# ----------------------------
st.markdown("""
<style>
    .output-box {
        background: #f8fafc;
        border: 1px solid #dbe3ea;
        border-radius: 12px;
        padding: 18px;
        min-height: 220px;
        white-space: pre-wrap;
        line-height: 1.7;
        color: #1f2937;   /* Output text color */
        font-size: 15px;
    }

    .center-box {
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 220px;
        color: #64748b;
    }

    .title {
        text-align: center;
        font-size: 42px;
        font-weight: 800;
        color: #0f172a;
        margin-bottom: 5px;
    }

    .subtitle {
        text-align: center;
        color: #64748b;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# ----------------------------
# GET AZURE CLIENTS
# ----------------------------
@st.cache_resource
def get_clients():
    endpoint = st.secrets["AZURE_ENDPOINT"]
    api_key = st.secrets["AZURE_API_KEY"]
    speech_key = st.secrets["AZURE_SPEECH_KEY"]
    speech_region = st.secrets["AZURE_SPEECH_REGION"]

    vision_client = ComputerVisionClient(
        endpoint,
        CognitiveServicesCredentials(api_key)
    )

    return vision_client, speech_key, speech_region


vision_client, speech_key, speech_region = get_clients()

# ----------------------------
# HELPER FUNCTIONS
# ----------------------------
def extract_text_from_image(uploaded_file):
    """Extract text from an image using Azure OCR."""
    image_bytes = uploaded_file.getvalue()
    response = vision_client.read_in_stream(io.BytesIO(image_bytes), raw=True)
    operation_id = response.headers["Operation-Location"].split("/")[-1]

    while True:
        result = vision_client.get_read_result(operation_id)
        if result.status not in [OperationStatusCodes.running, OperationStatusCodes.not_started]:
            break
        time.sleep(0.5)

    text_lines = []
    if result.status == OperationStatusCodes.succeeded:
        for page in result.analyze_result.read_results:
            for line in page.lines:
                text_lines.append(line.text)

    return "\n".join(text_lines).strip()


def text_to_speech(text, output_file="output.wav"):
    """Convert text to speech using Azure TTS."""
    speech_config = speechsdk.SpeechConfig(
        subscription=speech_key,
        region=speech_region
    )
    speech_config.speech_synthesis_voice_name = "en-US-ChristopherNeural"

    audio_config = speechsdk.audio.AudioOutputConfig(filename=output_file)
    synthesizer = speechsdk.SpeechSynthesizer(
        speech_config=speech_config,
        audio_config=audio_config
    )
    synthesizer.speak_text_async(text).get()

    with open(output_file, "rb") as f:
        return f.read()


# ----------------------------
# HEADER
# ----------------------------
st.markdown('<div class="title">READIFY_AI</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">OCR • Text to Speech • Image to Speech</div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📄 OCR", "🎙️ Text to Speech", "🔊 Image to Speech"])

# ----------------------------
# TAB 1: OCR
# ----------------------------
with tab1:
    col1, col2 = st.columns(2)

    with col1:
        uploaded_image = st.file_uploader(
            "Upload an image",
            type=["png", "jpg", "jpeg"],
            key="ocr_upload"
        )
        run_ocr = st.button("Extract Text", use_container_width=True)

        if uploaded_image:
            st.image(uploaded_image, use_container_width=True)

    with col2:
        if uploaded_image and run_ocr:
            try:
                text = extract_text_from_image(uploaded_image)
                if text:
                    st.markdown(f'<div class="output-box">{text}</div>', unsafe_allow_html=True)
                    st.download_button(
                        "Download Text",
                        text,
                        file_name="ocr_text.txt",
                        use_container_width=True
                    )
                else:
                    st.info("No text found in the image.")
            except Exception as e:
                st.error(f"OCR error: {e}")
        else:
            st.markdown(
                '<div class="output-box center-box">Extracted text will appear here.</div>',
                unsafe_allow_html=True
            )

# ----------------------------
# TAB 2: TEXT TO SPEECH
# ----------------------------
with tab2:
    user_text = st.text_area("Enter text here", height=200, placeholder="Type something...")
    speak_btn = st.button("Generate Voice", use_container_width=True)

    if speak_btn:
        if user_text.strip():
            try:
                audio_data = text_to_speech(user_text, "tts_output.wav")
                st.success("Audio generated successfully.")
                st.audio(audio_data, format="audio/wav")
                st.download_button(
                    "Download Audio",
                    audio_data,
                    file_name="tts_output.wav",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"TTS error: {e}")
        else:
            st.warning("Please enter some text first.")

# ----------------------------
# TAB 3: IMAGE TO SPEECH
# ----------------------------
with tab3:
    col1, col2 = st.columns(2)

    with col1:
        uploaded_image2 = st.file_uploader(
            "Upload an image",
            type=["png", "jpg", "jpeg"],
            key="img2speech_upload"
        )
        run_img2speech = st.button("Read Image Aloud", use_container_width=True)

        if uploaded_image2:
            st.image(uploaded_image2, use_container_width=True)

    with col2:
        if uploaded_image2 and run_img2speech:
            try:
                extracted_text = extract_text_from_image(uploaded_image2)

                if extracted_text:
                    st.markdown(f'<div class="output-box">{extracted_text}</div>', unsafe_allow_html=True)
                    audio_data = text_to_speech(extracted_text, "img2speech_output.wav")
                    st.audio(audio_data, format="audio/wav")
                    st.download_button(
                        "Download Audio",
                        audio_data,
                        file_name="img2speech_output.wav",
                        use_container_width=True
                    )
                else:
                    st.warning("No text found in the image.")
            except Exception as e:
                st.error(f"Image to speech error: {e}")
        else:
            st.markdown(
                '<div class="output-box center-box">Processed output will appear here.</div>',
                unsafe_allow_html=True
            )
