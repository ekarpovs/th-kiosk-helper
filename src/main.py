# src/main.py
import sys
import os
import subprocess
import shutil
import logging
import shlex
import platform

from urllib.parse import urlparse, parse_qs

from fastapi import FastAPI, Body, Request, requests
from fastapi.middleware.cors import CORSMiddleware
import uvicorn


# ------------------------------------------------------------
# 📘 Logging Setup
# ------------------------------------------------------------

LOG_FILE = os.path.expanduser("~/.thkiosk-helper.log")

import logging
import sys

safe_stream = sys.stdout if sys.stdout else open(os.devnull, "w")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(safe_stream)
    ]
)

logger = logging.getLogger("thkiosk-helper")


# ------------------------------------------------------------
# 🌐 FastAPI App
# ------------------------------------------------------------

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------------------------------------
# 🔍 Browser Detection
# ------------------------------------------------------------

# Linux/macOS candidates (PATH-based)
UNIX_BROWSER_CANDIDATES = [
    "google-chrome",
    "chrome",
    "chromium",
    "chromium-browser",
    "firefox",
    "brave",
    "microsoft-edge",
    "edge",
]

# Windows absolute paths
WINDOWS_BROWSER_PATHS = {
    "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "chrome-x86": r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    "edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "edge-64": r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    "firefox": r"C:\Program Files\Mozilla Firefox\firefox.exe",
    "firefox-x86": r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
}


def detect_installed_browsers():
    system = sys.platform.lower()
    found = []

    if system.startswith("linux") or system.startswith("darwin"):  # macOS = darwin
        for name in UNIX_BROWSER_CANDIDATES:
            path = shutil.which(name)
            if path:
                found.append({"name": name, "path": path})

    elif system.startswith("win"):
        for name, path in WINDOWS_BROWSER_PATHS.items():
            if os.path.exists(path):
                found.append({"name": name, "path": path})

    logger.info(f"Detected browsers: {found}")
    return found


# ------------------------------------------------------------
# 🚀 Browser Launcher
# ------------------------------------------------------------

def launch_browser(browser_name, url, kiosk=False):
    system = platform.system().lower()
    browsers = detect_installed_browsers()

    # Find matching browser
    browser = next((b for b in browsers if browser_name in b["name"]), None)
    if not browser:
        logger.error(f"Browser '{browser_name}' not found.")
        return False

    path = browser["path"]
    logger.info(f"Launching browser: {path} (kiosk={kiosk}) url={url}")

    try:
        if system == "windows":
            # Build command string
            if kiosk:
                cmd = f'"{path}" --kiosk "{url}"'
            else:
                cmd = f'"{path}" "{url}"'

            # Safe split → prevents CTRL+C stack traces
            args = shlex.split(cmd)
            subprocess.Popen(args)

        elif system == "darwin":  # macOS
            if kiosk:
                cmd = f'open -a "{path}" --args --kiosk "{url}"'
            else:
                cmd = f'open -a "{path}" "{url}"'

            args = shlex.split(cmd)
            subprocess.Popen(args)

        else:  # Linux
            if kiosk:
                cmd = f'"{path}" --kiosk "{url}"'
            else:
                cmd = f'"{path}" "{url}"'

            args = shlex.split(cmd)
            subprocess.Popen(args)

        return True

    except Exception as e:
        logger.error(f"Failed to launch browser: {e}")
        return False


# ------------------------------------------------------------
# 🌐 FastAPI Endpoints
# ------------------------------------------------------------

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Incoming request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response

@app.get("/health")
def health():
    """
    Lightweight liveness probe.
    Cloud service uses this to check that the helper app is running.
    """
    logger.info("Health check requested.")
    return {"status": "alive"}


@app.get("/status")
def status():
    """
    Detailed status report for cloud monitoring.
    Includes:
    - helper app status
    - installed browsers
    - log file location
    - current working directory
    """
    logger.info("Status check requested.")

    return {
        "helper_status": "running",
        "installed_browsers": detect_installed_browsers(),
        "log_file": LOG_FILE,
        "cwd": os.getcwd(),
        "pid": os.getpid()
    }


@app.get("/browsers")
def list_browsers():
    logger.info("Cloud requested browser list.")
    return detect_installed_browsers()


@app.post("/open-browser")
def open_browser(
    target_url: str = Body(..., embed=True),
    browser: str = Body(..., embed=True),
    kiosk: bool = Body(False, embed=True),
):
    logger.info(f"Cloud requested browser launch: browser={browser}, kiosk={kiosk}, url={target_url}")
    launch_browser(browser, target_url, kiosk)
    return {"status": "ok"}


# ------------------------------------------------------------
# 🔗 Custom Protocol Handler (optional)
# ------------------------------------------------------------

def handle_custom_protocol_arg():
    th_url = sys.argv[1]
    logger.info(f"Handling custom protocol call: {th_url}")

    # Extract path from protocol URL
    path = th_url.replace("thkiosk://", "").lstrip("/")
    http_url = f"http://127.0.0.1:3333/{path}"

    logger.info(f"One-shot mode: sending request to {http_url}")

    try:
        response = requests.get(http_url, timeout=5)
        logger.info(f"Response {response.status_code}: {response.text}")
    except Exception as e:
        logger.error(f"Request failed: {e}")

    logger.info("One-shot protocol handler finished. Exiting.")


# ------------------------------------------------------------
# 🏁 Entry Point
# ------------------------------------------------------------

def is_protocol_launch():
    for arg in sys.argv[1:]:
        if arg.startswith("thkiosk://"):
            return arg
    return None


if __name__ == "__main__":
    logger.info("ThKiosk Helper App starting...")
    PORT = int(os.getenv("THKIOSK_PORT", "3333"))

    proto = is_protocol_launch()

    # One-shot protocol handler mode
    if proto:
        handle_custom_protocol_arg()
        sys.exit(0)

    # Persistent server mode
    logger.info(f"Starting FastAPI server on http://127.0.0.1:{PORT}")

    import uvicorn

    config = uvicorn.Config(
        app,
        host="127.0.0.1",
        port=PORT,
        log_config=None,
        access_log=False
    )
    server = uvicorn.Server(config)
    try:
        server.run()
    except KeyboardInterrupt:
        logger.info("Server stopped cleanly.")
        # swallow the exception so Python does NOT print a traceback
