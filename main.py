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

    # Add your cookies here
    cookies = {
        "PREF": "tz=Asia.Jakarta&f4=4000000&f6=40000000&f5=30000&f7=100",
        "wide": "1",
        "GPS": "1",
        "SID": "g.a000rgjUsXhrUeMAnTgEfOg3MOEBu-2rgBxDG1kuNgIGPgwUWhBQmPlEJZisCUWfltYWysdyQwACgYKAasSARMSFQHGX2Mi1ZCjF98FqukRvsZ3p8Zz-xoVAUF8yKqOu3TuabwBhRqABFUKxj610076",
        "__Secure-1PSIDTS": "sidts-CjIB7wV3sShgIoEjhATmKKnsZqR1yYsrKk3ltZVKagWEN2EPjD624LZ2LIgRc4kkDhpZoRAA",
        "__Secure-3PSIDTS": "sidts-CjIB7wV3sShgIoEjhATmKKnsZqR1yYsrKk3ltZVKagWEN2EPjD624LZ2LIgRc4kkDhpZoRAA",
        "__Secure-1PSID": "g.a000rgjUsXhrUeMAnTgEfOg3MOEBu-2rgBxDG1kuNgIGPgwUWhBQktBBSzUWFs9HjxFd_uzP4QACgYKASgSARMSFQHGX2MiniZJTPEk-fAqFz3Ha93cKRoVAUF8yKqIrVzHiCQb3mFkrYfwJ39k0076",
        "__Secure-3PSID": "g.a000rgjUsXhrUeMAnTgEfOg3MOEBu-2rgBxDG1kuNgIGPgwUWhBQOEg8ZPLXy3rBYM64lEbw1gACgYKAekSARMSFQHGX2MicXuzOeg-vNJK0pPIsVW1uxoVAUF8yKoFc9BGJ4cnqrDA2Kzqxyp50076",
        "HSID": "A5-UDhZuW2bIc8CS_",
        "SSID": "AbpjdmqSBnXXctrTy",
        "APISID": "G8Bz-3uzQSQF-B_d/AcEWi6mpmIeaWqhqY",
        "SAPISID": "n3A3XJRo6lihlheK/ApSsNqjPatLQgMhL5",
        "__Secure-1PAPISID": "n3A3XJRo6lihlheK/ApSsNqjPatLQgMhL5",
        "__Secure-3PAPISID": "n3A3XJRo6lihlheK/ApSsNqjPatLQgMhL5",
        "LOGIN_INFO": "AFmmF2swRAIgVqFC3mXA9jonuTqCy6bKVYnDJa_hJAgnueRtR5geqJ4CIGRCWlX2R_9iQsAnGzDUH_pSTHZDSYPKVh_Y_CvsO8ak:QUQ3MjNmeEZqeW1lQVNqU1BOdXRpWUlTN25XX2RzMGVLTm5mb0FBRzZqbzZKcksxMjR0WFktNkY0SkpuSGY0ME40WUVDSmpXcUhPNW5TblZSeDdxN3dNZ0hWYUtDdHVCZnNxT1dWQUZCYVdhVFdaU2hXUUZrdmwtdXlIZFFEeWxMNUF2Y18zMkpLT0tuVXhGd29PMlZQcGtybDg5WnUxODdR",
        "ST-xuwub9": "session_logininfo=AFmmF2swRAIgVqFC3mXA9jonuTqCy6bKVYnDJa_hJAgnueRtR5geqJ4CIGRCWlX2R_9iQsAnGzDUH_pSTHZDSYPKVh_Y_CvsO8ak%3AQUQ3MjNmeEZqeW1lQVNqU1BOdXRpWUlTN25XX2RzMGVLTm5mb0FBRzZqbzZKcksxMjR0WFktNkY0SkpuSGY0ME40WUVDSmpXcUhPNW5TblZSeDdxN3dNZ0hWYUtDdHVCZnNxT1dWQUZCYVdhVFdaU2hXUUZrdmwtdXlIZFFEeWxMNUF2Y18zMkpLT0tuVXhGd29PMlZQcGtybDg5WnUxODdR",
        "SIDCC": "AKEyXzVtquWveeTgxoBYp737ZuRk4EYM19hwGkNV6Sf5-A6MNryopnPJkJOagd1_PTX-9iQkWA",
        "__Secure-1PSIDCC": "AKEyXzUm7gg4dBxfyVmuflNeLfLDBdsv_ErsEYqNyCXvmj6V-bmOoIJdmzHua57RkG9ucaba",
        "__Secure-3PSIDCC": "AKEyXzWa6RTbp-5i0a0he5jNbpklO30fdbAIrAInwzfN1UgObTLuTqBwqTQ1ycfWfyC2R2LQ"
    }

    ydl_opts = {
        'format': 'mp4',  # Force the download to be in mp4 format.
        'outtmpl': os.path.join(folder, '%(title)s.%(ext)s'),
        'progress_hooks': [progress_hook],
        'noplaylist': True,  # Only download a single video.
        'quiet': True,  # Suppress verbose logs.
        'cookie': cookies,  # Add the cookies here
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
        print(f"Download error: {e}")



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
