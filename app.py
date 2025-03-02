from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
import logging

app = Flask(__name__)

# Настройка логирования
logging.basicConfig(level=logging.INFO)

def format_time(seconds):
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes}:{seconds:02d}"

@app.route('/get_transcript', methods=['GET'])
def get_transcript():
    video_id = request.args.get('video_id')
    target_time = float(request.args.get('target_time', 0))
    window = float(request.args.get('window', 40))

    logging.info(f"Processing request for video_id: {video_id}")

    if not video_id:
        return jsonify({"error": "video_id is required"}), 400

    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'en-US', 'en-GB'])
        logging.info(f"Transcript retrieved: {transcript[:2]}")  # Логируем первые два элемента для отладки
        window_start = target_time - (window / 2)
        window_end = target_time + (window / 2)
        captured_text = ""

        for entry in transcript:
            start = entry['start']
            end = start + entry['duration']
            if end >= window_start and start <= window_end:
                captured_text += entry['text'] + " "

        response = {
            "time_segment": f"{format_time(window_start)} to {format_time(window_end)}",
            "text": captured_text.strip()
        }
        logging.info(f"Returning response: {response}")
        return jsonify(response)
    except Exception as e:
        error_message = str(e)
        logging.error(f"Error occurred: {error_message}")
        if "Subtitles are disabled" in error_message:
            return jsonify({"error": "Subtitles are not available for this video. Please try another video with subtitles enabled."}), 400
        return jsonify({"error": "An unexpected error occurred: " + error_message}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)