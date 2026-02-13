# QRMaster (Python Desktop App)

QRMaster is now a **Python desktop application** instead of an Android app.
It lets you:

- Generate QR codes from arbitrary text and save them as PNG images.
- Scan QR codes using your computer's webcam and read the decoded content.

## Requirements

- Python 3.9+ (recommended)
- pip

Install dependencies:

```bash
pip install -r requirements.txt
```

## Run the app

From the project root:

```bash
python main.py
```

This opens a window with two tabs:

- **Generate**: Type text, click **Generate QR**, then optionally **Save QR Image**.
- **Scan**: Click **Start Camera Scan**; a camera window opens and will detect and decode the first QR code it sees.

## Interface

Place your UI screenshots (e.g. `UI1.jpg` and `UI2.jpg`) in the project root, then they will be referenced here:

![Generate tab](UI1.jpg)

![Scan tab](UI2.jpg)

> Note: Packaging this Python app as an Android APK is possible with tools like Kivy/Buildozer or BeeWare, but requires additional environment setup (typically on Linux/WSL). This project currently targets desktop use.

