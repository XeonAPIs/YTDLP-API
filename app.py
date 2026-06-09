from flask import Flask, request, jsonify, send_from_directory, render_template
from yt_dlp import YoutubeDL
from pydub import AudioSegment
import os
import uuid
from werkzeug.utils import secure_filename

app = Flask(__name__)
DOWNLOAD_FOLDER = 'downloads'
app.config['DOWNLOAD_FOLDER'] = DOWNLOAD_FOLDER

# ── Change this to your actual domain, e.g. https://myapp.onrender.com ──
URL = os.environ.get('BASE_URL', 'http://localhost:5000')

COOKIES_FILE = os.path.join(os.path.dirname(__file__), 'cookies.txt')

def cookies_available():
    """Return True only if a real cookies.txt (not just the placeholder) is present."""
    if not os.path.exists(COOKIES_FILE):
        return False
    with open(COOKIES_FILE, 'r') as f:
        content = f.read().strip()
    # The placeholder file contains only comments / empty lines
    real_lines = [l for l in content.splitlines() if l.strip() and not l.startswith('#')]
    return len(real_lines) > 0

def base_ydl_opts():
    """Common yt-dlp options shared by both audio and video routes."""
    opts = {
        'http_headers': {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) '
                'Gecko/20100101 Firefox/124.0'
            ),
        },
        'noplaylist': True,          # never accidentally grab a whole playlist
        'quiet': True,
        'no_warnings': False,
    }
    if cookies_available():
        opts['cookiefile'] = COOKIES_FILE
    return opts


# ── Home page ────────────────────────────────────────────────────────────────

@app.route('/')
def home():
    return render_template('index.html')


# ── Audio ─────────────────────────────────────────────────────────────────────

@app.route('/audio', methods=['GET'])
def download_audio():
    url  = request.args.get('url')
    name = request.args.get('name')

    if not url and not name:
        return jsonify({'error': 'Either url or name query param is required'}), 400

    search_query = f"ytsearch:{name}" if name else url

    output_filename = secure_filename(f"{uuid.uuid4()}.mp3")
    output_path     = os.path.join(DOWNLOAD_FOLDER, output_filename)
    tmp_template    = os.path.join(DOWNLOAD_FOLDER, f"tmp_{uuid.uuid4()}.%(ext)s")

    ydl_opts = base_ydl_opts()
    ydl_opts.update({
        'format':  'bestaudio/best',
        'outtmpl': tmp_template,
    })

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(search_query, download=True)

            # ytsearch wraps results in a list; unwrap it
            if 'entries' in info_dict:
                info_dict = info_dict['entries'][0]

            title     = info_dict.get('title', 'unknown')
            file_path = ydl.prepare_filename(info_dict)

            # Convert to MP3 with pydub
            audio = AudioSegment.from_file(file_path)
            audio.export(output_path, format='mp3', bitrate='192k')

            # Remove the raw downloaded file
            if os.path.exists(file_path):
                os.remove(file_path)

        return jsonify({
            'download_url': f'{URL}/download/{output_filename}',
            'name':         title,
            'url':          url or search_query,
        }), 200

    except Exception as e:
        # Clean up any partial files
        for p in [output_path]:
            if os.path.exists(p):
                os.remove(p)
        return jsonify({'error': str(e)}), 500


# ── Video ─────────────────────────────────────────────────────────────────────

@app.route('/video', methods=['GET'])
def download_video():
    url      = request.args.get('url')
    name     = request.args.get('name')
    quality  = request.args.get('quality', '1080')   # optional: 720, 480, etc.

    if not url and not name:
        return jsonify({'error': 'Either url or name query param is required'}), 400

    search_query = f"ytsearch:{name}" if name else url

    output_filename = secure_filename(f"{uuid.uuid4()}.mp4")
    output_path     = os.path.join(DOWNLOAD_FOLDER, output_filename)
    tmp_template    = os.path.join(DOWNLOAD_FOLDER, f"tmp_{uuid.uuid4()}.%(ext)s")

    ydl_opts = base_ydl_opts()
    ydl_opts.update({
        'format':  f'bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<={quality}]+bestaudio/best[height<={quality}]/best',
        'outtmpl': tmp_template,
        # merge into a single mp4 (requires ffmpeg)
        'merge_output_format': 'mp4',
    })

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(search_query, download=True)

            if 'entries' in info_dict:
                info_dict = info_dict['entries'][0]

            title     = info_dict.get('title', 'unknown')
            file_path = ydl.prepare_filename(info_dict)

            # yt-dlp may write .mp4 directly after merging
            if not os.path.exists(file_path):
                file_path = file_path.rsplit('.', 1)[0] + '.mp4'

            os.rename(file_path, output_path)

        return jsonify({
            'download_url': f'{URL}/download/{output_filename}',
            'name':         title,
            'url':          url or search_query,
        }), 200

    except Exception as e:
        if os.path.exists(output_path):
            os.remove(output_path)
        return jsonify({'error': str(e)}), 500


# ── Info (no download) ────────────────────────────────────────────────────────

@app.route('/info', methods=['GET'])
def video_info():
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'url query param is required'}), 400

    ydl_opts = base_ydl_opts()
    ydl_opts['skip_download'] = True

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return jsonify({
                'title':     info.get('title'),
                'duration':  info.get('duration'),
                'uploader':  info.get('uploader'),
                'view_count': info.get('view_count'),
                'thumbnail': info.get('thumbnail'),
            }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── Serve downloaded files ────────────────────────────────────────────────────

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    return send_from_directory(app.config['DOWNLOAD_FOLDER'], filename)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == '__main__':
    os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
