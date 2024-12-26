import streamlit as st
import google.generativeai as genai 
from youtube_transcript_api import YouTubeTranscriptApi
import os
import re
from io import BytesIO
from dotenv import load_dotenv
import markdown2
from weasyprint import HTML


st.set_page_config(layout="wide")
Gapi_key = st.secrets["GOOGLE_API_KEY"]
genai.configure(api_key=Gapi_key)


# Extracts video id from YouTube URL
def extract_video_id(youtube_url):
    regex = (
        r'(?:https?://)?(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/v/|youtube\.com/shorts/|youtube.com/playlist\?list=)([^&=%\?]{11})'
    )
    match = re.match(regex, youtube_url)
    if match:
        return match.group(1)
    else:
        raise ValueError("Invalid YouTube URL")

# Extract Transcript from the YouTube Video
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

# Generate PDF from HTML using WeasyPrint
def generate_pdf(html_content):
    try:
        pdf = BytesIO()
        HTML(string=html_content).write_pdf(pdf)
        pdf.seek(0)
        return pdf
    except Exception as e:
        st.error(f"PDF generation failed: {e}")
        return None

# Main App
st.title("📢 Video Summarizer")

st.header("🔗 Paste YouTube URL")
youtube_link = st.text_input('YouTube Link', placeholder="Paste your YouTube URL here")

if youtube_link:
    video_id = extract_video_id(youtube_link)
    st.image(f"http://img.youtube.com/vi/{video_id}/0.jpg", use_column_width=True)

    word_limit = st.slider('Word Limit', 50, 500, 250, 10)
    prompt = st.text_input("Prompt (Optional)", placeholder="Provide specific instructions for the summary format.")
    
    if st.button("Generate Summary"):
        transcript_text = get_english_transcript(video_id)
        if transcript_text:
            summary = generate_gemini_content(transcript_text, prompt)
            st.session_state['summary'] = summary
            st.success("Summary generated successfully!")
        else:
            st.error("Could not fetch transcript for this video.")

if 'summary' in st.session_state:
    raw_summary = st.session_state['summary']
    html_content = generate_html(raw_summary)
    st.markdown("## Summary:")
    st.markdown(raw_summary, unsafe_allow_html=True)

    st.header(":green[Download as PDF]")
    pdf_file = generate_pdf(html_content)
    if pdf_file:
        st.download_button(
            label="Download PDF ✅",
            data=pdf_file,
            file_name="summary_report.pdf",
            mime="application/pdf",
        )
