# 🖼️ withoutbg-tool

A simple, practical background removal tool built on top of
[`withoutbg`](https://pypi.org/project/withoutbg/). Supports single image,
batch folder processing, background color fill, and a web UI.

## ✨ Features
- Remove background from any image (JPG/PNG/WebP)
- Batch process an entire folder with a progress bar
- Fill transparent background with a solid color (e.g. white for ID photos)
- CLI mode + Streamlit Web UI in one file
- Local model (free) or Cloud API (faster)

## 📦 Installation
```bash
pip install -r requirements.txt
```

> First run downloads the local model automatically (~450MB).
> It is cached, so subsequent runs are fast.

## 🚀 Usage

**Single image:**
```bash
python app.py --input bird.jpg --output out.png
```

**White background (ID photo style):**
```bash
python app.py --input bird.jpg --output out.jpg --bg white
```

**Batch folder:**
```bash
python app.py --input-dir photos/ --output-dir results/
```

**Web UI:**
```bash
streamlit run app.py
```

## 🧠 How it works
This project wraps `withoutbg`'s `open_weights()` (local) and `api()` (cloud)
methods. The local model runs entirely on your machine — no data leaves your
computer.

## 📄 License
MIT