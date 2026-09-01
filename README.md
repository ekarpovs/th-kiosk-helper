
---

# 📘 ThKiosk Helper App  
A cross‑platform Python application that runs on **Windows**, **macOS**, and **Linux**, providing a secure way for a cloud service to open a **real browser window in kiosk or standard mode** on the client machine.

The helper app exposes a **local FastAPI server** and supports a **custom protocol handler** (`thkiosk://`) so your cloud backend can trigger browser launches on the user's device.

---

## 🚀 Features

- Launch Firefox, Chrome, Chromium, Edge, or Brave  
- Kiosk mode with fullscreen, new‑instance, no tab reuse  
- Standard mode supported  
- Installed browser detection  
- Local FastAPI API (`localhost:3333`)  
- Custom protocol handler (`thkiosk://`)  
- Cross‑platform installers  
- Persistent logging  
- Health and status endpoints  

---

## 📦 Project Structure

```
thkiosk-helper/
│
├── src/
│   └── main.py
│
├── build/
│   ├── linux/
│   ├── macos/
│   └── windows/
│
├── dist/
│   ├── linux/
│   ├── macos/
│   └── windows/
│
├── requirements.txt
├── build-requirements.txt
└── README.md
```

---

# 🔧 Dependencies

## Runtime dependencies (`requirements.txt`)
These are required **when the helper app is running**:

```
fastapi==0.115.0
uvicorn==0.30.0
python-multipart==0.0.9
```

Install them for development:

```bash
pip install -r requirements.txt
```

---

## Build dependencies (`build-requirements.txt`)
These are required **only when building installers**:

```
pyinstaller==6.3.0
```

Install them when preparing installers:

```bash
pip install -r build-requirements.txt
```

---

# 🏗️ Build Instructions (Run from Project Root)

All build commands must be executed from the **project root**, because:

- PyInstaller writes `main.spec` to the root  
- Installer scripts reference root‑relative paths  
- Output binaries are placed in `dist/`  

PyInstaller always generates:

```
main.spec
build/main/
dist/main
```

This is correct and expected.

---

# 🟦 Linux Build (DEB Installer)

### 1. Build binary

```bash
pyinstaller --onefile src/main.py
```

### 2. Move binary into installer staging

```bash
cp dist/main build/linux/debian/usr/local/bin/thkiosk-helper
chmod +x build/linux/debian/usr/local/bin/thkiosk-helper
```

### 3. Build `.deb` installer

```bash
dpkg-deb --build build/linux/debian dist/linux/thkiosk-helper_1.0.0_amd64.deb
```

### 4. Install

```bash
sudo dpkg -i dist/linux/thkiosk-helper_1.0.0_amd64.deb
```

---

# 🟩 macOS Build (APP + DMG)

### 1. Build `.app` binary

```bash
pyinstaller --onefile --windowed src/main.py
cp dist/main build/macos/ThKiosk.app/Contents/MacOS/thkiosk-helper
```

### 2. Build `.dmg`

```bash
hdiutil create -volname ThKiosk \
  -srcfolder build/macos/ThKiosk.app \
  -ov -format UDZO dist/macos/ThKiosk.dmg
```

### 3. Install

Drag `ThKiosk.app` into `/Applications`.

---

# 🟥 Windows Build (Inno Setup Installer)

### 1. Build `.exe`

```bash
pyinstaller --onefile --windowed src/main.py
cp dist/main.exe build/windows/dist/thkiosk-helper.exe
```

### 2. Build installer

```bash
ISCC build/windows/InnoSetup/setup.iss
```

Installer output:

```
dist/windows/ThKioskHelperInstaller.exe
```

---

# 🌐 API Endpoints

### **GET /browsers**
Returns installed browsers.

### **POST /open-browser**
Launches a browser in kiosk or standard mode.

Example body:

```json
{
  "target_url": "https://example.com",
  "browser": "firefox",
  "kiosk": true
}
```

### **GET /health**
Lightweight liveness probe.

### **GET /status**
Detailed system status including installed browsers, log file path, working directory, and PID.

---

# 🔗 Custom Protocol Handler (`thkiosk://`)

Example:

```
thkiosk://open?url=https://example.com&browser=firefox&kiosk=true
```

Protocol registration is handled automatically by installers on each platform.

---

# 📥 Distribution

Place installers in:

```
dist/linux/
dist/macos/
dist/windows/
```

---

# 🔐 Security Notes

- Helper app listens only on `localhost`  
- No remote access  
- Logs stored at: `~/.thkiosk-helper.log`  

---

# 📄 License

MIT License.

---
