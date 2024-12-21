from flask import Flask, render_template, request, jsonify
import os
import threading
import yt_dlp

app = Flask(__name__)

DOWNLOAD_FOLDER = 'downloads'
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# Shared dictionary for progress tracking
progress_data = {
    'status': 'waiting',
    'percent': 0,
    'eta': 0
}

# Global variable to track the download thread
download_thread = None


def progress_hook(status):
    """Updates progress information during download."""
    if status['status'] == 'downloading':
        percent = float(status['_percent_str'].strip('%'))
        eta = status.get('eta', 'N/A')
        progress_data.update({'status': 'downloading', 'percent': percent, 'eta': eta})
    elif status['status'] == 'finished':
        progress_data.update({'status': 'finished', 'percent': 100, 'eta': 0})
    elif status['status'] == 'error':
        progress_data.update({'status': 'error', 'percent': 0, 'eta': 0})


def download_video(url, folder):
    """Handles the video download process."""
    progress_data.update({'status': 'initializing', 'percent': 0, 'eta': 0})
    ydl_opts = {
        'format': 'mp4',  # Force the download to be in mp4 format.
        'outtmpl': os.path.join(folder, '%(title)s.%(ext)s'),
        'progress_hooks': [progress_hook],
        'noplaylist': True,  # Only download a single video.
        'quiet': True,  # Suppress verbose logs.
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        progress_data.update({'status': 'error', 'percent': 0, 'eta': 0})


def start_download_thread(url, folder):
    """Start the download in a separate thread."""
    global download_thread
    download_thread = threading.Thread(target=download_video, args=(url, folder))
    download_thread.start()


@app.route('/')
def index():
    return render_template('index.html', progress=progress_data)


@app.route('/download', methods=['POST'])
def download():
    """Handle the video download request."""
    url = request.form['url']
    folder = DOWNLOAD_FOLDER
    if not url or not folder:
        return jsonify({"error": "Please provide a valid URL and download folder."})

    start_download_thread(url, folder)
    return jsonify({"status": "Download started."})


@app.route('/progress')
def check_progress():
    """Check the current download progress."""
    return jsonify(progress_data)


if __name__ == "__main__":
    app.run(debug=True)
