import streamlit as st
import google.generativeai as genai 
from youtube_transcript_api import YouTubeTranscriptApi
import os
import re
from io import BytesIO
from dotenv import load_dotenv
import pdfkit
import markdown2

Gapi_key = st.secrets["GOOGLE_API_KEY"]



st.set_page_config(layout="wide")
genai.configure(api_key=Gapi_key)


# Extracts video id from youtube URL
def extract_video_id(youtube_url):
    regex = (
        r'(?:https?://)?(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/v/|youtube\.com/shorts/|youtube.com/playlist\?list=)([^&=%\?]{11})'
    )
    match = re.match(regex, youtube_url)
    if match:
        return match.group(1)
    else:
        raise ValueError("Invalid YouTube URL")

# This function will Extract Transcript from the yt Video
def get_english_transcript(video_id):
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

        try:
            transcript = transcript_list.find_manually_created_transcript(['en'])
            transcript_text = transcript.fetch()
            transcript = ' '.join([i['text'] for i in transcript_text])
            return transcript

        except:
            pass

        try:
            transcript = transcript_list.find_generated_transcript(['en'])
            transcript_text = transcript.fetch()
            transcript = ' '.join([i['text'] for i in transcript_text])
            return transcript

        except:
            pass

        for transcript in transcript_list:
            if transcript.language_code != 'en' and transcript.is_translatable:
                translated_transcript = transcript.translate('en')
                transcript_text = translated_transcript.fetch()
                transcript = ' '.join([i['text'] for i in transcript_text])
                return transcript

        return None

    except:
        return None

def generate_gemini_content(transcript_text, prompt):
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(prompt + transcript_text)
    return response.text


import base64

def get_base64_file(file_path):
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

# Convert the GIF to Base64
gif_data = get_base64_file("images/S.gif")

# Embed the GIF in HTML
st.markdown(
    f'<img src="data:image/gif;base64,{gif_data}" alt="Animated GIF" style="width:100%;">',
    unsafe_allow_html=True
)


text = '''
<h1 style="text-align: right;">
    <span style="color:cyan">Video</span> 
    <span style="color:red">Summarizer</span>
</h1>
'''
st.markdown(text, unsafe_allow_html=True)

st.title("📢 :green[Instructions]")
st.info("""
1. Paste the URL of Youtube Video.
2. You can use your own prompt to generate your summary according to requirements.
3. Select the word limits of your Summary by moving the slider.
""")
st.header("🔗 :green[Paste Youtube URL]")
youtube_link = st.text_input('yt link', help="Copy Your Youtube URL and paste it in the Text Box", label_visibility="hidden")
thumbnail, desc = st.columns(2)

if youtube_link:
    video_id = extract_video_id(youtube_link)
    with thumbnail.container(border=True):
        st.image(f"http://img.youtube.com/vi/{video_id}/0.jpg", use_column_width=True)
    with desc.container(border=True):
        st.header(":violet[Word Limit] ⏩")
        with st.container(border = True):
            words = st.slider('word limit', 50, 500, 250, 10, label_visibility='hidden')
        with st.container(border = True):
            prompt = f"""You are a YouTube video summarizer. You will be taking the transcript text 
        and summarizing the entire video, providing the important summary in points within {words} words.
        Please provide the summary of the given YouTube caption here: """
            st.header(":violet[Enter Prompt(Optional)]")
            prompt = st.text_input("prompt", label_visibility='hidden', help='Enter the prompt to clarify in which format summary is to be generated.',placeholder="Provide specific instructions for summary format.")
        st.write(' ')
        st.markdown('<h7><h7>',unsafe_allow_html=True)
        btn, spin = st.columns(2)

        if btn.button("Generate Summary", use_container_width=True):
            with spin:
                with st.spinner("Generating summary..."):
                    transcript_text = get_english_transcript(video_id)
                    if transcript_text:
                        summary = generate_gemini_content(transcript_text, prompt)
                        st.session_state['summary'] = summary
                        st.success("Summary generated successfully!")
                    else:
                        st.error("Could not fetch transcript for this video.")

if 'summary' in st.session_state and st.session_state['summary'] == False:
    st.info("🥲 Sorry, Summary for the video cannot be generated. Try with another video.")



# Path to wkhtmltopdf (adjust for your system)
WKHTMLTOPDF_PATH = r"wkhtmltopdf\bin\wkhtmltopdf.exe"

# Global Styling for HTML
GLOBAL_STYLES = """
<style>
    body {
        font-family: Arial, sans-serif;
        line-height: 1.6;
        color: #333;
    }
    h2 {
        color: #2c3e50;
        font-weight: bold;
    }
    ul {
        margin: 0 0 1em 1.5em;
        padding: 0;
    }
    li {
        margin-bottom: 8px;
    }
    table {
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 1em;
    }
    th, td {
        border: 1px solid #ccc;
        padding: 8px;
        text-align: left;
    }
    th {
        background-color: #f4f4f4;
    }
    br {
        content: '';
        display: block;
        margin: 10px 0;
    }
    strong {
        color: #000;
    }
</style>
"""

# Convert Markdown to HTML using markdown2 with extras
def markdown_to_html(content):
    extras = ["tables", "fenced-code-blocks", "cuddled-lists"]
    html = markdown2.markdown(content, extras=extras)
    return html

# Generate HTML for the document
def generate_html(content):
    formatted_content = markdown_to_html(content)
    html = f"""
    <html>
    <head>{GLOBAL_STYLES}</head>
    <body>
        <h2>Detailed Notes:</h2>
        {formatted_content}
    </body>
    </html>
    """
    return html

# Generate PDF from HTML
def generate_pdf(html_content):
    try:
        config = pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF_PATH)
        options = {"enable-local-file-access": None, "encoding": "UTF-8"}
        pdf_file = pdfkit.from_string(html_content, False, options=options, configuration=config)
        return BytesIO(pdf_file)
    except Exception as e:
        st.error(f"PDF generation failed: {e}")
        return None


# Main App
if "summary" in st.session_state and st.session_state["summary"]:
    raw_summary = st.session_state["summary"]
    html_content = generate_html(raw_summary)
    st.markdown("## Detailed Notes:")
    box = st.container(border=True)
    with box:
        st.markdown(raw_summary, unsafe_allow_html=True)


    st.header(":green[Import as PDF file] ⬇️")
    pdf_file = generate_pdf(html_content)
    if pdf_file:
        st.download_button(
            label="Download PDF ✅",
            data=pdf_file,
            file_name="summary_report.pdf",
            mime="application/pdf",
        )
