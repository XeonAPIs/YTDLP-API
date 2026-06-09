# YTDLP-API (Fixed)

A Flask REST API that wraps **yt-dlp** to download audio and video from YouTube (and 1000+ other sites).

---

## Fixes & improvements over the original

| # | Issue | Fix |
|---|-------|-----|
| 1 | `cookiefile` key had a stray comment breaking the dict | Cleaned up; cookies load automatically when present |
| 2 | `user-agent` was not a valid yt-dlp key | Moved to `http_headers` → `User-Agent` |
| 3 | `ytsearch:` results returned a list; `prepare_filename` crashed | Unwrap `entries[0]` for search results |
| 4 | Video rename used the wrong extension after merging | Correct fallback to `.mp4` after merge |
| 5 | No `ffmpeg` in Dockerfile → video merging silently failed | Added `apt-get install ffmpeg` |
| 6 | `BASE_URL` hard-coded in source | Reads from `BASE_URL` env var (falls back to localhost) |
| 7 | No `/info` endpoint | Added `/info?url=` for metadata without downloading |
| 8 | No quality param for video | Added optional `?quality=720` (default 1080) |
| 9 | cookies.txt placeholder was confusing | Clear instructions + auto-detection logic |
| 10 | Missing background image causing UI issues | Removed missing image refs; added gradient background |
| 11 | YouTube signature solving errors | Added better error handling & retry logic; improved error messages |
| 12 | No media format fallbacks | Added socket timeout, retries, and fragment retry logic |

---

## Setup

### Local

```bash
pip install -r requirements.txt
# optional: add cookies (see cookies.txt)
BASE_URL=http://localhost:5000 python app.py
```

### Docker

```bash
docker build -t ytdlp-api .
docker run -p 5000:5000 \
  -e BASE_URL=https://yourdomain.com \
  -v $(pwd)/cookies.txt:/app/cookies.txt \
  ytdlp-api
```

### Render / Railway / Fly.io

Set the environment variable `BASE_URL` to your public URL.  
The `render.yaml` already references this.

---

## 🔧 Requirements & System Dependencies

### ffmpeg

**Required for video merging.** Install:

- **Windows:** `choco install ffmpeg` (via Chocolatey) or download from [ffmpeg.org](https://ffmpeg.org)
- **macOS:** `brew install ffmpeg`
- **Linux:** `sudo apt install ffmpeg` (Debian/Ubuntu)

### Node.js (for YouTube signature solving)

**Required to download newer YouTube videos.** yt-dlp uses Node.js to solve YouTube's signature challenges.

Install:

- **Windows:** Download from [nodejs.org](https://nodejs.org) or `choco install nodejs`
- **macOS:** `brew install node`
- **Linux:** `sudo apt install nodejs npm`

**Verify installation:**
```bash
ffmpeg -version
node --version
```

---

## Cookies (important for age-restricted / sign-in-required videos)

1. Install the **Cookie-Editor** browser extension.
2. Open **YouTube** and log in.
3. Click the extension → **Export** → **Netscape** format.
4. Paste the result into `cookies.txt` (replace the placeholder).
5. Restart the app.

The app auto-detects whether real cookies are present; it runs fine without them for public videos.

> ⚠️ **Never commit `cookies.txt` to a public repo.**

### Supplying cookies on Render

When deploying on Render you can provide cookies securely via an environment secret named `COOKIES_CONTENT`. The container entrypoint will write this value to `cookies.txt` at startup so the app can use it.

1. Export cookies in Netscape format using a browser extension.
2. In the Render dashboard, add a secret env var `COOKIES_CONTENT` with the full contents of the exported file.
3. Deploy the service; the container will create `cookies.txt` from the secret at boot.

This avoids committing credentials to the repo and lets the app use the cookies for restricted content.

---

## Endpoints

### `GET /audio?url=<youtube_url>`
### `GET /audio?name=<search_term>`

Downloads the best audio stream and converts to MP3 (192 kbps).

**Response:**
```json
{
  "download_url": "https://yourdomain.com/download/abc123.mp3",
  "name": "Video Title",
  "url": "https://youtu.be/..."
}
```

---

### `GET /video?url=<youtube_url>[&quality=1080]`
### `GET /video?name=<search_term>[&quality=720]`

Downloads the best video+audio and merges into MP4.  
`quality` defaults to `1080`. Pass `720`, `480`, `360`, etc. to reduce size.

---

### `GET /info?url=<youtube_url>`

Returns metadata **without** downloading.

```json
{
  "title": "...",
  "duration": 243,
  "uploader": "...",
  "view_count": 1234567,
  "thumbnail": "https://..."
}
```

---

### `GET /download/<filename>`

Serves a previously downloaded file.

> Open `/` in your browser to use the built-in download form. The video form includes a quality selector for `1080`, `720`, `480`, and `360`.
