from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi

app = Flask(__name__)

def format_time(seconds):
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes}:{seconds:02d}"

@app.route('/get_transcript', methods=['GET'])
def get_transcript():
    video_id = request.args.get('video_id')
    target_time = float(request.args.get('target_time', 0))
    window = float(request.args.get('window', 40))

    if not video_id:
        return jsonify({"error": "video_id is required"}), 400

    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
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
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run()