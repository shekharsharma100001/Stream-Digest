# StreamDigest

StreamDigest is a Streamlit app that allows users to summarize YouTube videos. The app extracts the transcript of the video and generates a summary based on user-provided instructions and word limits. The summary can be downloaded as a PDF file.

## Features

- **YouTube Video Summarization**: Extracts and summarizes transcripts from YouTube videos.
- **Customizable Summarization**: Set your own word limit and customize the summary format with prompts.
- **PDF Export**: Download the generated summary as a PDF.

## Technologies Used

- **Streamlit**: Web framework for building the interactive app.
- **Google Generative AI**: To generate the summaries based on the video transcripts.
- **YouTube Transcript API**: To fetch the video transcripts.
- **ReportLab**: To generate the summary in PDF format.
- **Markdown2**: To convert markdown content to HTML for rendering in the app.

## Requirements

Before running the project, you need to install the required dependencies.
```bash
   pip install -r requirements.txt
```


### Installation and Setup

1. Clone the repository to your local machine and navigate to the project directory:

   ```bash
   git clone https://github.com/shekharsharma100001/Stream-Digest.git
   cd StreamDigest
   ```
2. Running Streamlit app
   ```bash
   streamlit run app.py
   ```



