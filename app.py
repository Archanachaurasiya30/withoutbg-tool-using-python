"""
withoutbg-tool — single file complete project
=============================================
Features:
  - Single image background removal
  - Batch folder processing with progress bar
  - Solid background color fill (white/blue/red for ID photos)
  - CLI mode + Web UI (Streamlit) mode in one file
  - Local model (free) or Cloud API (faster)

Install:
    pip install withoutbg pillow tqdm streamlit

Run CLI:
    python app.py --input bird.jpg --output out.png
    python app.py --input bird.jpg --output out.jpg --bg white
    python app.py --input-dir photos/ --output-dir results/

Run Web UI:
    streamlit run app.py

License: MIT
"""

import os
import sys
import argparse
from pathlib import Path

# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

VALID_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def load_model(use_local: bool = True, api_key: str = None):
    """Load withoutbg model (local open-weights or cloud API)."""
    from withoutbg import WithoutBG

    if use_local:
        print("Loading local model (first run downloads weights)...")
        model = WithoutBG.open_weights()
    else:
        if not api_key:
            raise ValueError("API key required for cloud mode")
        model = WithoutBG.api(api_key=api_key)

    print("Model ready")
    return model


def fill_background(rgba_img, color: str):
    """Fill transparent background with a solid color."""
    from PIL import Image

    bg = Image.new("RGB", rgba_img.size, color)
    bg.paste(rgba_img, mask=rgba_img.split()[-1])
    return bg


def remove_single(model, input_path: str, output_path: str, bg_color: str = None):
    """Remove background from one image and save it."""
    result = model.remove_background(input_path)
    if bg_color:
        result = fill_background(result, bg_color)

    if output_path.lower().endswith((".jpg", ".jpeg")) and result.mode == "RGBA":
        result = result.convert("RGB")

    result.save(output_path)
    return output_path


def remove_batch(model, input_dir: str, output_dir: str, bg_color: str = None):
    """Process all images in a folder with a progress bar."""
    from tqdm import tqdm

    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    images = [f for f in input_dir.iterdir() if f.suffix.lower() in VALID_EXTS]
    if not images:
        print("No images found")
        return []

    saved = []
    for img_path in tqdm(images, desc="Processing", unit="img"):
        out_path = output_dir / f"{img_path.stem}.png"
        try:
            remove_single(model, str(img_path), str(out_path), bg_color)
            saved.append(str(out_path))
        except Exception as e:
            print(f"Failed: {img_path.name} -> {e}")

    print(f"\nDone! {len(saved)}/{len(images)} images saved to {output_dir}")
    return saved


# ---------------------------------------------------------------------------
# CLI mode
# ---------------------------------------------------------------------------

def run_cli():
    parser = argparse.ArgumentParser(description="Remove image backgrounds easily")
    parser.add_argument("--input", help="Single input image path")
    parser.add_argument("--output", help="Single output image path")
    parser.add_argument("--input-dir", help="Folder of images (batch mode)")
    parser.add_argument("--output-dir", help="Output folder for batch mode")
    parser.add_argument("--bg", default=None,
                        help="Fill background color, e.g. white / #ffffff")
    parser.add_argument("--cloud", action="store_true",
                        help="Use cloud API instead of local model")
    parser.add_argument("--api-key", default=None, help="API key for cloud mode")

    args = parser.parse_args()

    model = load_model(use_local=not args.cloud, api_key=args.api_key)

    if args.input and args.output:
        remove_single(model, args.input, args.output, bg_color=args.bg)
        print(f"Saved -> {args.output}")
    elif args.input_dir and args.output_dir:
        remove_batch(model, args.input_dir, args.output_dir, bg_color=args.bg)
    else:
        parser.print_help()


# ---------------------------------------------------------------------------
# Streamlit Web UI mode
# ---------------------------------------------------------------------------

def run_streamlit():
    import streamlit as st
    from PIL import Image
    import io

    st.set_page_config(page_title="withoutbg-tool", page_icon="🖼️", layout="wide")
    st.title("🖼️ withoutbg-tool")
    st.caption("Remove image backgrounds — local model, free & private")

    @st.cache_resource(show_spinner="Loading model (first run downloads weights)...")
    def get_model():
        return load_model(use_local=True)

    with st.sidebar:
        st.header("Settings")
        bg_choice = st.selectbox(
            "Background fill",
            ["Transparent (PNG)", "White", "Blue", "Red", "Black", "Custom"],
        )
        custom_color = None
        if bg_choice == "Custom":
            custom_color = st.color_picker("Pick a color", "#ffffff")

        bg_map = {
            "Transparent (PNG)": None,
            "White": "white",
            "Blue": "#0047AB",
            "Red": "#C8102E",
            "Black": "black",
        }
        bg_color = custom_color if bg_choice == "Custom" else bg_map[bg_choice]

    model = get_model()

    tab1, tab2 = st.tabs(["📷 Single Image", "📁 Batch Folder"])

    with tab1:
        uploaded = st.file_uploader(
            "Upload an image", type=["jpg", "jpeg", "png", "webp"]
        )
        if uploaded:
            col1, col2 = st.columns(2)
            original = Image.open(uploaded)

            with col1:
                st.subheader("Original")
                st.image(original, use_container_width=True)

            if st.button("Remove Background", type="primary"):
                with st.spinner("Removing background..."):
                    result = model.remove_background(uploaded)

                    if bg_color:
                        result = fill_background(result, bg_color)

                    with col2:
                        st.subheader("Result")
                        st.image(result, use_container_width=True)

                    buf = io.BytesIO()
                    fmt = "JPEG" if bg_color else "PNG"
                    if fmt == "JPEG" and result.mode == "RGBA":
                        result = result.convert("RGB")
                    result.save(buf, format=fmt)

                    st.download_button(
                        "Download result",
                        data=buf.getvalue(),
                        file_name=f"result.{fmt.lower()}",
                        mime=f"image/{fmt.lower()}",
                    )
        else:
            st.info("Upload an image to get started")

    with tab2:
        files = st.file_uploader(
            "Upload multiple images",
            type=["jpg", "jpeg", "png", "webp"],
            accept_multiple_files=True,
        )
        if files and st.button("Process all", type="primary"):
            progress = st.progress(0, text="Processing...")
            results = []

            for i, f in enumerate(files):
                try:
                    res = model.remove_background(f)
                    if bg_color:
                        res = fill_background(res, bg_color)
                    results.append((f.name, res))
                except Exception as e:
                    st.error(f"{f.name} failed: {e}")
                progress.progress((i + 1) / len(files),
                                  text=f"Processed {i+1}/{len(files)}")

            progress.empty()
            st.success(f"Done! {len(results)} images processed")

            for name, res in results:
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**{name}**")
                with col2:
                    buf = io.BytesIO()
                    fmt = "JPEG" if bg_color else "PNG"
                    if fmt == "JPEG" and res.mode == "RGBA":
                        res = res.convert("RGB")
                    res.save(buf, format=fmt)
                    st.download_button(
                        f"Download {name}",
                        data=buf.getvalue(),
                        file_name=f"out_{name.rsplit('.', 1)[0]}.{fmt.lower()}",
                        mime=f"image/{fmt.lower()}",
                        key=name,
                    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    run_cli()