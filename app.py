from flask import Flask, request, jsonify
import yt_dlp
import logging
from datetime import datetime
import pytz
import os

# Настройка логирования на уровне старта
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)

try:
    app = Flask(__name__)
    logging.info("Flask app initialized successfully")

    # Настройка логирования с локальным временем (MSK)
    class MSKFormatter(logging.Formatter):
        def formatTime(self, record, datefmt=None):
            msk_tz = pytz.timezone('Europe/Moscow')
            dt = datetime.fromtimestamp(record.created, tz=pytz.UTC)
            dt_msk = dt.astimezone(msk_tz)
            return dt_msk.strftime('%Y-%m-%d %H:%M:%S')

    formatter = MSKFormatter('%(asctime)s [%(levelname)s] %(message)s')
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(logging.INFO)

    @app.route('/ping')
    def ping():
        logging.info("Ping route accessed")
        return "Pong!"

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
            logging.error("video_id is missing")
            return jsonify({"error": "video_id is required"}), 400

        try:
            logging.info("Setting up cookies")
            cookies = os.getenv('COOKIES', '')
            if cookies:
                logging.info("Cookies found, writing to cookies.txt")
                with open('cookies.txt', 'w') as f:
                    f.write(cookies)
            else:
                logging.warning("No cookies provided")

            ydl_opts = {
                'skip_download': True,
                'writeautomaticsub': True,
                'subtitleslangs': ['en'],
                'subtitlesformat': 'json3',
                'quiet': False,
                'cookiefile': 'cookies.txt' if cookies else None,
            }

            logging.info("Starting yt-dlp extraction")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                info = ydl.extract_info(video_url, download=False)
                logging.info(f"Extracted info: {info}")
                subtitles = info.get('automatic_captions', {}).get('en', [])

            if not subtitles:
                logging.warning("No subtitles found for the video")
                return jsonify({"error": "Subtitles are not available for this video."}), 400

            window_start = target_time - (window / 2)
            window_end = target_time + (window / 2)
            captured_text = ""

            for subtitle in subtitles[0].get('events', []):
                if subtitle.get('segs'):
                    start = subtitle['tStartMs'] / 1000
                    duration = subtitle.get('dDurationMs', 0) / 1000
                    end = start + duration
                    if end >= window_start and start <= window_end:
                        text = "".join(seg['utf8'] for seg in subtitle['segs'])
                        captured_text += text + " "

            response = {
                "time_segment": f"{format_time(window_start)} to {format_time(window_end)}",
                "text": captured_text.strip()
            }
            logging.info(f"Returning response: {response}")
            return jsonify(response)

        except Exception as e:
            error_message = str(e)
            logging.error(f"Error occurred: {error_message}")
            return jsonify({"error": "An unexpected error occurred: " + error_message}), 500

except Exception as e:
    logging.error(f"Failed to initialize application: {str(e)}")
    raise e

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)