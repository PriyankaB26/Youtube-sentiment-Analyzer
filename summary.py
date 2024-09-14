from flask import Flask, request, jsonify, send_from_directory
from transformers import pipeline
from youtube_transcript_api import YouTubeTranscriptApi
import time

app = Flask(__name__)

# Initialize the summarizer pipeline
summarizer = pipeline('summarization',model="sshleifer/distilbart-cnn-12-6")

def get_transcript(video_id):
    try:
        # Fetch transcript for the given video ID
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        result = ""
        for entry in transcript:
            result += ' ' + entry['text']
        return result
    except Exception as e:
        return str(e)

def summarize_text(text):
    # Split text into chunks and summarize
    num_iters = int(len(text) / 1000)
    summarized_text = []
    for i in range(num_iters + 1):
        start = i * 1000
        end = (i + 1) * 1000
        chunk = text[start:end]
        out = summarizer(chunk)
        summarized_text.append(out[0]['summary_text'])
    return ' '.join(summarized_text)

@app.route('/')
def index():
    return send_from_directory('templates', 'summary.html')

@app.route('/summarize', methods=['POST'])
def summarize_video():
    start_time = time.time()
    data = request.json
    video_id = data.get('video_id')
    if not video_id:
        return jsonify({"error": "Video ID is required"}), 400

    transcript = get_transcript(video_id)
    if 'error' in transcript.lower():
        return jsonify({"error": transcript}), 400

    summary = summarize_text(transcript)
    return jsonify({"summary": summary})
    print(f"total_time={time.time()-start_time}")

if __name__ == '__main__':
    app.run(debug=True)
