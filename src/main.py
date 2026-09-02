# src/main.py
import sys
import os
import subprocess
import shutil
import logging
import shlex

from urllib.parse import urlparse, parse_qs

from fastapi import FastAPI, Body, Request
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

BROWSER_CANDIDATES = [
    "firefox",
    "google-chrome",
    "chrome",
    "chromium",
    "chromium-browser",
    "brave",
    "microsoft-edge",
    "edge",
]


def detect_installed_browsers():
    found = []
    for name in BROWSER_CANDIDATES:
        path = shutil.which(name)
        if path:
            found.append({"name": name, "path": path})
    logger.info(f"Detected browsers: {found}")
    return found


# ------------------------------------------------------------
# 🚀 Browser Launcher
# ------------------------------------------------------------

def launch_browser(url: str, browser_name: str, kiosk: bool):
    logger.info(f"Launching browser: name={browser_name}, kiosk={kiosk}, url={url}")
    # Disable AT-SPI (Assistive Technology Service Provider Interface) 
    # for GTK applications to avoid accessibility warnings.
    os.environ["NO_AT_BRIDGE"] = "1"

    browser_path = shutil.which(browser_name)
    if not browser_path:
        logger.error(f"Browser '{browser_name}' not found.")
        return

    safe_url = str(url)

    if kiosk:
        if browser_name == "firefox":
            cmd = [
                browser_path,
                "--kiosk",
                "--new-window",
                "--new-instance",
                safe_url
            ]
        elif browser_name in ("chrome", "google-chrome", "chromium", "chromium-browser", "brave"):
            cmd = [
                browser_path,
                "--kiosk",
                "--new-window",
                f"--app={safe_url}"
            ]
        elif browser_name in ("microsoft-edge", "edge"):
            cmd = [
                browser_path,
                "--kiosk",
                "--edge-kiosk-type=fullscreen",
                f"--app={safe_url}"
            ]
        else:
            logger.warning(f"Browser '{browser_name}' may not support kiosk mode. Launching normally.")
            cmd = [browser_path, shlex.quote(safe_url)]
    else:
        cmd = [browser_path, shlex.quote(safe_url)]

    logger.info(f"Executing command: {cmd}")

    try:
        subprocess.Popen(cmd)
        logger.info("Browser launched successfully.")
    except Exception as e:
        logger.exception(f"Failed to launch browser: {e}")


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
    launch_browser(target_url, browser, kiosk)
    return {"status": "ok"}


# ------------------------------------------------------------
# 🔗 Custom Protocol Handler (optional)
# ------------------------------------------------------------

def handle_custom_protocol_arg():
    raw = sys.argv[1]
    logger.info(f"Handling custom protocol call: {raw}")

    parsed = urlparse(raw)
    if parsed.scheme != "thkiosk":
        logger.warning("Unknown protocol scheme.")
        return

    qs = parse_qs(parsed.query)
    target_url = qs.get("url", [""])[0]
    browser = qs.get("browser", ["firefox"])[0]
    kiosk = qs.get("kiosk", ["false"])[0].lower() == "true"

    logger.info(f"Protocol launch: browser={browser}, kiosk={kiosk}, url={target_url}")
    launch_browser(target_url, browser, kiosk)


# ------------------------------------------------------------
# 🏁 Entry Point
# ------------------------------------------------------------

if __name__ == "__main__":
    logger.info("ThKiosk Helper App starting...")
    PORT = int(os.getenv("THKIOSK_PORT", "3333"))

    # Handle custom protocol invocation
    if len(sys.argv) > 1 and sys.argv[1].startswith("thkiosk://"):
        handle_custom_protocol_arg()
    else:
        logger.info(f"Starting FastAPI server on http://127.0.0.1:{PORT}")

        import uvicorn

        config = uvicorn.Config(
            app,
            host="127.0.0.1",
            port=PORT,
            log_config=None,      # PyInstaller-safe
            access_log=False      # avoid Uvicorn handlers
        )
        server = uvicorn.Server(config)

        try:
            server.run()
        except KeyboardInterrupt:
            logger.info("ThKiosk Helper stopped cleanly.")
