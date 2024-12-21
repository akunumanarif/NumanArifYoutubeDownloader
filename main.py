from flask import Flask, render_template, request, jsonify
import os
import threading
import yt_dlp
from werkzeug.utils import secure_filename

app = Flask(__name__)

DOWNLOAD_FOLDER = 'downloads'
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# Global variable to track the download process
download_thread = None
progress = {'status': '', 'percent': 0, 'eta': 0}


def progress_hook(status):
    """Updates progress information during download."""
    global progress
    if status['status'] == 'downloading':
        percent = float(status['_percent_str'].strip('%'))
        eta = status.get('eta', 'N/A')
        progress = {'status': 'downloading', 'percent': percent, 'eta': eta}
    elif status['status'] == 'finished':
        progress = {'status': 'finished', 'percent': 100, 'eta': 0}
    elif status['status'] == 'error':
        progress = {'status': 'error', 'percent': 0, 'eta': 0}


def download_video(url, folder):
    """Handles the video download process."""
    global progress
    ydl_opts = {
        'format': 'mp4',  # Force the download to be in mp4 format.
        'outtmpl': os.path.join(folder, '%(title)s.%(ext)s'),
        'progress_hooks': [progress_hook],
        'noplaylist': True,  # Only download a single video.
        'quiet': True,  # Suppress verbose logs.
        'extractor_args': {
            'youtube': {
                'player_client': 'web,default',
                'po_token': 'web+MlPJuStGMFBIx8mFCyLwhUBkzJnNfr9AcyhM-W9NjCdyeghf8isCKnn55eLrQ5Vjrp-l2jjCQhKrLumRR_AUAjiwTvssUB9Uk_QxchLq_AWVvk3dDg==',
            }
        },
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        progress = {'status': 'error', 'percent': 0, 'eta': 0}
        print(f"Error: {e}")



def start_download_thread(url, folder):
    """Start the download in a separate thread."""
    global download_thread
    download_thread = threading.Thread(target=download_video, args=(url, folder))
    download_thread.start()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/download', methods=['POST'])
def download():
    """Handle the video download request."""
    url = request.form['url']
    folder = DOWNLOAD_FOLDER
    if not url or not folder:
        return jsonify({"error": "Please provide a valid URL and download folder."})

    progress['status'] = 'initializing'
    progress['percent'] = 0
    start_download_thread(url, folder)
    return jsonify({"status": "Download started."})


@app.route('/progress')
def check_progress():
    """Check the current download progress."""
    return jsonify(progress)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4444, debug=True)
