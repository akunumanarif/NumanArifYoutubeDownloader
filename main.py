from flask import Flask, render_template, request, jsonify, session
import os
import threading
import yt_dlp

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for session to work

DOWNLOAD_FOLDER = 'downloads'
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# Global variable to track the download process
download_thread = None


def progress_hook(status):
    """Updates progress information during download."""
    if status['status'] == 'downloading':
        percent = float(status['_percent_str'].strip('%'))
        eta = status.get('eta', 'N/A')
        session['progress'] = {'status': 'downloading', 'percent': percent, 'eta': eta}
    elif status['status'] == 'finished':
        session['progress'] = {'status': 'finished', 'percent': 100, 'eta': 0}
    elif status['status'] == 'error':
        session['progress'] = {'status': 'error', 'percent': 0, 'eta': 0}


def download_video(url, folder):
    """Handles the video download process."""
    session['progress'] = {'status': 'initializing', 'percent': 0, 'eta': 0}
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
        session['progress'] = {'status': 'error', 'percent': 0, 'eta': 0}


def start_download_thread(url, folder):
    """Start the download in a separate thread."""
    global download_thread
    download_thread = threading.Thread(target=download_video, args=(url, folder))
    download_thread.start()


@app.route('/')
def index():
    # Check if download has been initiated
    download_started = session.get('download_started', False)
    if not download_started:
        session['progress'] = {'status': 'waiting', 'percent': 0, 'eta': 0}  # Show default message

    progress = session.get('progress', {'status': 'waiting', 'percent': 0, 'eta': 0})
    return render_template('index.html', progress=progress)


@app.route('/download', methods=['POST'])
def download():
    """Handle the video download request."""
    url = request.form['url']
    folder = DOWNLOAD_FOLDER
    if not url or not folder:
        return jsonify({"error": "Please provide a valid URL and download folder."})

    session['download_started'] = True  # Mark that the download has started
    start_download_thread(url, folder)
    return jsonify({"status": "Download started."})


@app.route('/progress')
def check_progress():
    """Check the current download progress."""
    progress = session.get('progress', {'status': 'waiting', 'percent': 0, 'eta': 0})
    return jsonify(progress)


if __name__ == "__main__":
    app.run(debug=True)